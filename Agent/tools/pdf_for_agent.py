#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf"]
# ///
"""
pdf_for_agent.py — prepare a PDF for an OpenCode agent.

Splits a PDF into two kinds of artefact on disk:
  * one Markdown file holding the text layer of every page that has one
  * one PNG per page that has no usable text layer (or that you force)

OpenCode can attach both (`-f file.png -f file.md`), which the base64
inline-image path in 04_bdi_pipeline_v8.py cannot do.

Triage rule (same as find_bdi_pages): a page whose extracted text is
shorter than --text-threshold characters is treated as image-only.
"""

import argparse
import pathlib
import sys

import pymupdf  # `import fitz` still works but is deprecated in >=1.28


def parse_pages(spec: str, n_pages: int) -> set[int]:
    """'1,4-6' -> {0, 3, 4, 5}  (input is 1-based, output 0-based)."""
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = (int(x) for x in part.split("-", 1))
        else:
            lo = hi = int(part)
        for p in range(lo, hi + 1):
            if not 1 <= p <= n_pages:
                sys.exit(f"page {p} out of range (PDF has {n_pages})")
            out.add(p - 1)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("-o", "--outdir", help="default: <pdf stem>_agent/")
    ap.add_argument("--dpi", type=int, default=200,
                    help="rasterisation DPI (default 200; 300+ for small text)")
    ap.add_argument("--render", metavar="PAGES",
                    help="force-render these pages too, e.g. '1,4-6' (1-based)")
    ap.add_argument("--render-all", action="store_true",
                    help="render every page, regardless of text layer")
    ap.add_argument("--text-threshold", type=int, default=40,
                    help="chars below which a page counts as image-only (default 40)")
    args = ap.parse_args()

    pdf_path = pathlib.Path(args.pdf)
    if not pdf_path.is_file():
        sys.exit(f"no such file: {pdf_path}")

    outdir = pathlib.Path(args.outdir) if args.outdir else \
        pdf_path.with_name(pdf_path.stem + "_agent")
    outdir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(pdf_path)
    n_pages = doc.page_count
    forced = parse_pages(args.render, n_pages) if args.render else set()

    zoom = args.dpi / 72
    mat = pymupdf.Matrix(zoom, zoom)

    text_chunks: list[str] = []
    png_paths: list[pathlib.Path] = []

    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        needs_png = (args.render_all
                     or i in forced
                     or len(text) < args.text_threshold)

        if text:
            text_chunks.append(f"## Page {i + 1}\n\n{text}")

        if needs_png:
            png = outdir / f"page-{i + 1:03d}.png"
            page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB).save(png)
            png_paths.append(png)

    doc.close()

    md_path = outdir / f"{pdf_path.stem}.md"
    if text_chunks:
        md_path.write_text(f"# {pdf_path.name}\n\n" + "\n\n".join(text_chunks),
                           encoding="utf-8")
    else:
        md_path = None

    attach = ([md_path] if md_path else []) + png_paths
    print(f"{n_pages} pages -> {len(png_paths)} PNG, "
          f"{'1 md' if md_path else 'no text layer'}  ({outdir})")
    if attach:
        print("\n" + " ".join(f"-f {p}" for p in attach))


if __name__ == "__main__":
    main()
