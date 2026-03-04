#!/usr/bin/env python3
"""
Export selected wiki.ozma.io docs into local markdown snapshot files.

Output directory: docs/wiki
"""

from __future__ import annotations

import argparse
import asyncio
import html
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

WIKI_DOCS: dict[str, dict[str, str]] = {
    "funql": {"title": "FunQL", "url": "https://wiki.ozma.io/en/docs/funql"},
    "fundb": {"title": "FunDB", "url": "https://wiki.ozma.io/en/docs/fundb"},
    "fundb-api": {"title": "FunDB API", "url": "https://wiki.ozma.io/en/docs/fundb-api"},
    "funapp/menu": {"title": "FunApp Menu", "url": "https://wiki.ozma.io/en/docs/funapp/menu"},
    "funapp/table": {"title": "FunApp Table", "url": "https://wiki.ozma.io/en/docs/funapp/table"},
    "funapp/form": {"title": "FunApp Form", "url": "https://wiki.ozma.io/en/docs/funapp/form"},
    "funapp/board": {"title": "FunApp Board", "url": "https://wiki.ozma.io/en/docs/funapp/board"},
    "funapp/tree": {"title": "FunApp Tree", "url": "https://wiki.ozma.io/en/docs/funapp/tree"},
    "funapp/timeline": {"title": "FunApp Timeline", "url": "https://wiki.ozma.io/en/docs/funapp/timeline"},
    "funapp/settings": {"title": "FunApp Settings", "url": "https://wiki.ozma.io/en/docs/funapp/settings"},
    "color-variants": {"title": "Color Variants", "url": "https://wiki.ozma.io/en/docs/color-variants"},
}


def html_to_text(page_html: str) -> str:
    body = page_html
    for tag in ("main", "article", "body"):
        m = re.search(rf"(?is)<{tag}\b[^>]*>(.*?)</{tag}>", page_html)
        if m:
            body = m.group(1)
            break
    body = re.sub(r"(?is)<(script|style|noscript|svg|canvas)\b[^>]*>.*?</\1>", "", body)
    body = re.sub(r"(?i)<br\s*/?>", "\n", body)
    body = re.sub(r"(?i)</(p|div|section|article|blockquote)>", "\n\n", body)
    body = re.sub(r"(?i)</(h1|h2|h3|h4|h5|h6)>", "\n\n", body)
    body = re.sub(r"(?i)</li>", "\n", body)
    body = re.sub(r"(?i)<li\b[^>]*>", "- ", body)
    body = re.sub(r"(?i)</tr>", "\n", body)
    body = re.sub(r"(?is)<[^>]+>", "", body)
    text = html.unescape(body)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def doc_path(base_dir: Path, slug: str) -> Path:
    return base_dir / f"{slug}.md"


async def fetch_one(client: httpx.AsyncClient, slug: str, meta: dict[str, str], out_dir: Path, stamp: str) -> Path:
    r = await client.get(meta["url"], follow_redirects=True)
    r.raise_for_status()
    extracted = html_to_text(r.text)
    content = (
        f"# {meta['title']}\n\n"
        f"Source: {meta['url']}\n"
        f"Exported at (UTC): {stamp}\n\n"
        f"{extracted}\n"
    )
    path = doc_path(out_dir, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


async def run(out_dir: Path) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for slug, meta in WIKI_DOCS.items():
            path = await fetch_one(client, slug, meta, out_dir, stamp)
            paths.append(path)

    index_lines = [
        "# Ozma Wiki Documentation Index",
        "",
        f"Exported at (UTC): {stamp}",
        "",
        "## Sections",
    ]
    for slug, meta in WIKI_DOCS.items():
        index_lines.append(f"- `ozma://docs/wiki/{slug}` — {meta['title']} ({meta['url']})")
    index_lines.append("")
    (out_dir / "index.md").write_text("\n".join(index_lines), encoding="utf-8")

    full_chunks = [f"# Ozma Wiki Full Documentation Bundle\n\nExported at (UTC): {stamp}\n"]
    for slug, meta in WIKI_DOCS.items():
        full_chunks.append(f"\n## {meta['title']}\n")
        full_chunks.append(doc_path(out_dir, slug).read_text(encoding="utf-8"))
    (out_dir / "full.md").write_text("\n".join(full_chunks).strip() + "\n", encoding="utf-8")

    print(f"Exported {len(paths)} section files + index.md + full.md into {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="docs/wiki", help="Output directory")
    args = parser.parse_args()
    out_dir = Path(args.out).resolve()
    asyncio.run(run(out_dir))


if __name__ == "__main__":
    main()
