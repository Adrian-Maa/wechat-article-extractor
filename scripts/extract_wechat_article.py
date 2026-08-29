#!/usr/bin/env python3
"""Extract readable text and metadata from a WeChat Official Account article."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
BLOCK_TAGS = {
    "article", "blockquote", "div", "figcaption", "h1", "h2", "h3", "h4",
    "h5", "h6", "li", "ol", "p", "section", "table", "td", "th", "tr",
    "ul",
}
SKIP_TAGS = {"script", "style", "noscript"}


class WeChatArticleParser(HTMLParser):
    """Collect metadata and text inside the `js_content` article container."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.author_parts: list[str] = []
        self.published_parts: list[str] = []
        self._capture_field: str | None = None
        self._capture_depth = 0
        self._inside_article = False
        self._article_depth = 0
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr = {key.lower(): value or "" for key, value in attrs}

        if tag == "meta":
            prop = attr.get("property") or attr.get("name")
            if prop == "og:title":
                self.title = attr.get("content", "").strip()
            elif prop == "og:description":
                self.description = attr.get("content", "").strip()

        element_id = attr.get("id", "")
        if not self._capture_field and element_id in {"js_name", "publish_time"}:
            self._capture_field = element_id
            self._capture_depth = 1
        elif self._capture_field and tag not in VOID_TAGS:
            self._capture_depth += 1

        if not self._inside_article and element_id == "js_content":
            self._inside_article = True
            self._article_depth = 1
            self._parts.append("\n")
            return

        if not self._inside_article:
            return

        if tag in SKIP_TAGS:
            self._skip_depth += 1

        if not self._skip_depth:
            if tag in BLOCK_TAGS or tag == "br":
                self._parts.append("\n")
            if tag == "img":
                alt = attr.get("alt", "").strip()
                if alt:
                    self._parts.append(f"[图片：{alt}]")

        if tag not in VOID_TAGS:
            self._article_depth += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if self._capture_field:
            self._capture_depth -= 1
            if self._capture_depth <= 0:
                self._capture_field = None
                self._capture_depth = 0

        if not self._inside_article:
            return

        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        elif not self._skip_depth and tag in BLOCK_TAGS:
            self._parts.append("\n")

        if tag not in VOID_TAGS:
            self._article_depth -= 1
        if self._article_depth <= 0:
            self._inside_article = False
            self._article_depth = 0

    def handle_data(self, data: str) -> None:
        if self._capture_field == "js_name":
            self.author_parts.append(data)
        elif self._capture_field == "publish_time":
            self.published_parts.append(data)

        if self._inside_article and not self._skip_depth:
            self._parts.append(data)

    @staticmethod
    def _clean_inline(parts: list[str]) -> str:
        return " ".join(" ".join(parts).split())

    @property
    def author(self) -> str:
        return self._clean_inline(self.author_parts)

    @property
    def published_at(self) -> str:
        return self._clean_inline(self.published_parts)

    @property
    def article_text(self) -> str:
        lines: list[str] = []
        previous = None
        for raw_line in "".join(self._parts).splitlines():
            line = " ".join(raw_line.split())
            if line and line != previous:
                lines.append(line)
                previous = line
        return "\n".join(lines).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract text from a mp.weixin.qq.com article."
    )
    parser.add_argument("url", help="WeChat Official Account article URL")
    parser.add_argument(
        "--format", choices=("text", "markdown", "json"), default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--output", help="Optional UTF-8 output file")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--max-bytes", type=int, default=10_000_000)
    return parser.parse_args()


def validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname != "mp.weixin.qq.com":
        raise ValueError("Expected an http(s) URL on mp.weixin.qq.com")


def fetch(url: str, timeout: float, max_bytes: int) -> tuple[str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
            ),
            "Referer": "https://mp.weixin.qq.com/",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(max_bytes + 1)
        final_url = response.geturl()
    if len(payload) > max_bytes:
        raise ValueError(f"Article exceeds --max-bytes ({max_bytes})")
    return payload.decode("utf-8", "replace"), final_url


def render(data: dict[str, object], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(data, ensure_ascii=False, indent=2)

    title = str(data["title"] or "未命名微信公众号文章")
    author = str(data["author"] or "")
    published_at = str(data["published_at"] or "")
    source_url = str(data["url"])
    description = str(data["description"] or "")
    text = str(data["text"])

    if output_format == "markdown":
        metadata = [f"- 来源：{source_url}"]
        if author:
            metadata.append(f"- 作者：{author}")
        if published_at:
            metadata.append(f"- 发布时间：{published_at}")
        if description:
            metadata.append(f"- 摘要：{description}")
        return f"# {title}\n\n" + "\n".join(metadata) + f"\n\n{text}\n"

    metadata = [f"TITLE: {title}", f"URL: {source_url}"]
    if author:
        metadata.append(f"AUTHOR: {author}")
    if published_at:
        metadata.append(f"PUBLISHED_AT: {published_at}")
    if description:
        metadata.append(f"DESCRIPTION: {description}")
    return "\n".join(metadata) + f"\n\n{text}\n"


def main() -> int:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        validate_url(args.url)
        html, final_url = fetch(args.url, args.timeout, args.max_bytes)
        parser = WeChatArticleParser()
        parser.feed(html)
        article_text = parser.article_text
        if len(article_text) < 100:
            raise ValueError(
                "No readable js_content article body found; WeChat may have returned a verification page"
            )

        data: dict[str, object] = {
            "title": parser.title,
            "description": parser.description,
            "author": parser.author,
            "published_at": parser.published_at,
            "url": final_url,
            "text": article_text,
            "character_count": len(article_text),
        }
        rendered = render(data, args.format)
        if args.output:
            output_path = Path(args.output).expanduser().resolve()
            output_path.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (ValueError, urllib.error.URLError, TimeoutError) as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
