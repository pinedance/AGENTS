---
name: my-md2pdf
description: Convert Markdown documents to high-quality PDF files with complete Korean font support, mathematical equations, tables, footnotes, and custom layout styling. Use whenever the user asks to convert markdown to PDF, export/generate PDF from markdown, print markdown to PDF, or wants a PDF document from an .md file.
---

# Markdown to PDF Converter (`my-md2pdf`)

Converts Markdown (`.md`) files into high-quality PDF documents with full Korean CJK font rendering, LaTeX math syntax support, styled tables, code highlighting, and clean margins.

## Why Standard Pandoc Fails on Korean Documents

Running default `pandoc input.md -o output.pdf` in Linux fails or produces question marks/blank glyphs because:
1. The default PDF engine (`pdflatex`) does not bind OpenType/TrueType system fonts.
2. Standard LaTeX templates do not load CJK macro packages without explicit configuration.

To reliably generate clean Korean PDFs, this skill uses **XeLaTeX** with system CJK fonts (`NanumGothic`, `Noto Sans CJK KR`, etc.) or **Chrome Headless** for HTML-styled PDFs.

---

## 1. Quick Execution (Recommended)

Use the bundled conversion script located in `scripts/md2pdf.sh`:

```bash
# Standard conversion (outputs to <filename>.pdf in the same directory)
/home/user/Labs/AGENTS/skills/my-md2pdf/scripts/md2pdf.sh document.md

# Specify custom output path
/home/user/Labs/AGENTS/skills/my-md2pdf/scripts/md2pdf.sh document.md custom_output.pdf

# With custom margin and table of contents
/home/user/Labs/AGENTS/skills/my-md2pdf/scripts/md2pdf.sh document.md final.pdf -m 2.0cm --toc
```

### Script CLI Options
- `-f, --font <FONT>`: CJK font family (default: `NanumGothic`; auto-fallbacks if missing)
- `-m, --margin <MARGIN>`: Page margin (default: `2.5cm`)
- `-s, --fontsize <SIZE>`: Base font size (e.g. `10pt`, `11pt`, `12pt`; default: `11pt`)
- `-t, --toc`: Include Table of Contents
- `--engine <xelatex|chrome>`: PDF engine (`xelatex` for academic/paper layout, `chrome` for web styling)

---

## 2. Direct Pandoc XeLaTeX Pipeline

When running custom Pandoc commands directly:

```bash
pandoc input.md -o output.pdf \
  --pdf-engine=xelatex \
  -V CJKmainfont="NanumGothic" \
  -V geometry:margin=2.5cm \
  -V fontsize=11pt \
  --highlight-style=tango
```

### Supported Markdown Elements
- **Headers & Sections**: `#`, `##`, `###` formatted hierarchically
- **Korean Typography**: Native Hangul characters rendered cleanly via `NanumGothic` / `Noto Sans CJK KR`
- **Math Equations**: Inline (`$...$`) and block (`$$...$$`) LaTeX formulas rendered natively via TeX engine
- **Tables**: Markdown pipe tables converted to LaTeX tabular environments
- **Code Blocks**: Syntax highlighted via `--highlight-style=tango` (or `kate`, `monochrome`)

---

## 3. Alternative Pipeline: Chrome Headless (Web/GitHub Styled)

When a document requires web CSS formatting or GitHub-like markdown styling rather than formal LaTeX typography:

```bash
TMP_HTML="$(mktemp --suffix=.html)"
pandoc input.md -s -o "$TMP_HTML"
google-chrome --headless --disable-gpu --run-all-compositor-stages-before-draw --print-to-pdf=output.pdf "$TMP_HTML"
rm -f "$TMP_HTML"
```

---

## 4. Verification & Inspection

Always verify the output PDF after generation:
1. **File Existence & Size**:
   ```bash
   ls -lh output.pdf
   ```
2. **Page Count & Content Inspection**:
   Use Python `pypdf` to inspect page count and extracted text if necessary:
   ```python
   from pypdf import PdfReader
   reader = PdfReader("output.pdf")
   print(f"Total Pages: {len(reader.pages)}")
   ```
