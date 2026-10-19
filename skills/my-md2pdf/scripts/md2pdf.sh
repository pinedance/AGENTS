#!/usr/bin/env bash
#
# md2pdf.sh - Convert Markdown to PDF with Korean CJK support and Pandoc XeLaTeX
#
set -euo pipefail

usage() {
    cat <<EOF
Usage: $(basename "$0") <input.md> [output.pdf] [OPTIONS]

Options:
    -f, --font FONT        CJK font name (default: NanumGothic)
    -m, --margin MARGIN    Page margin (default: 2.5cm)
    -t, --toc              Include Table of Contents
    -s, --fontsize SIZE    Main font size (e.g. 10pt, 11pt, 12pt; default: 11pt)
    --engine ENGINE        Engine: xelatex (default) or chrome
    -h, --help             Show this help message

Examples:
    $(basename "$0") report.md
    $(basename "$0") report.md final_report.pdf -m 2.0cm
    $(basename "$0") paper.md paper.pdf -f "Noto Sans CJK KR" --toc
EOF
    exit 1
}

if [[ $# -lt 1 ]]; then
    usage
fi

INPUT="$1"
shift

if [[ ! -f "$INPUT" ]]; then
    echo "Error: Input file '$INPUT' not found." >&2
    exit 1
fi

OUTPUT=""
FONT="NanumGothic"
MARGIN="2.5cm"
FONTSIZE="11pt"
TOC=false
ENGINE="xelatex"

# Check if next argument is output file (not starting with -)
if [[ $# -gt 0 && "$1" != -* ]]; then
    OUTPUT="$1"
    shift
fi

if [[ -z "$OUTPUT" ]]; then
    OUTPUT="${INPUT%.*}.pdf"
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--font)
            FONT="$2"
            shift 2
            ;;
        -m|--margin)
            MARGIN="$2"
            shift 2
            ;;
        -s|--fontsize)
            FONTSIZE="$2"
            shift 2
            ;;
        -t|--toc)
            TOC=true
            shift
            ;;
        --engine)
            ENGINE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            ;;
    esac
done

# Font fallback check if specified font is not detected
if ! fc-list : family | grep -Fq "$FONT"; then
    for candidate in "NanumGothic" "NanumMyeongjo" "Noto Sans CJK KR" "Noto Serif CJK KR" "Batang" "Dotum" "HCR Batang"; do
        if fc-list : family | grep -Fq "$candidate"; then
            echo "[Info] Font '$FONT' not found. Falling back to '$candidate'." >&2
            FONT="$candidate"
            break
        fi
    done
fi

echo "[md2pdf] Converting '$INPUT' -> '$OUTPUT'..."

if [[ "$ENGINE" == "xelatex" ]]; then
    if ! command -v pandoc >/dev/null 2>&1; then
        echo "Error: pandoc is not installed." >&2
        exit 1
    fi
    if ! command -v xelatex >/dev/null 2>&1; then
        echo "[Warn] xelatex not found. Falling back to Chrome headless engine." >&2
        ENGINE="chrome"
    fi
fi

if [[ "$ENGINE" == "xelatex" ]]; then
    PANDOC_ARGS=(
        "$INPUT"
        -o "$OUTPUT"
        --pdf-engine=xelatex
        -V "CJKmainfont=${FONT}"
        -V "geometry:margin=${MARGIN}"
        -V "fontsize=${FONTSIZE}"
        --highlight-style=tango
    )
    if [[ "$TOC" == true ]]; then
        PANDOC_ARGS+=(--toc --toc-depth=3)
    fi

    pandoc "${PANDOC_ARGS[@]}"

elif [[ "$ENGINE" == "chrome" ]]; then
    CHROME_BIN=""
    for bin in google-chrome chromium-browser chromium; do
        if command -v "$bin" >/dev/null 2>&1; then
            CHROME_BIN="$bin"
            break
        fi
    done

    if [[ -z "$CHROME_BIN" ]]; then
        echo "Error: Neither xelatex nor chrome/chromium is available." >&2
        exit 1
    fi

    TMP_HTML="$(mktemp --suffix=.html)"
    trap 'rm -f "$TMP_HTML"' EXIT

    pandoc "$INPUT" -s --metadata title="$(basename "${INPUT%.*}")" -o "$TMP_HTML"
    "$CHROME_BIN" --headless --disable-gpu --run-all-compositor-stages-before-draw --print-to-pdf="$OUTPUT" "$TMP_HTML" >/dev/null 2>&1
else
    echo "Error: Unsupported engine '$ENGINE'." >&2
    exit 1
fi

if [[ -f "$OUTPUT" ]]; then
    FILE_SIZE=$(ls -lh "$OUTPUT" | awk '{print $5}')
    echo "[md2pdf] Success: Created '$OUTPUT' (${FILE_SIZE})."
else
    echo "Error: Failed to create '$OUTPUT'." >&2
    exit 1
fi
