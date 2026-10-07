---
name: "my-md2hwpx"
description: "마크다운을 템플릿 없이 한글 .hwpx(표·한글 수식·그림·쪽번호)로 변환하거나, .hwpx 문서를 읽고 내용을 파악·요약할 때, 사용자가 고친 .hwpx를 md/html 사본과 동기화할 때 사용."
---

# Markdown → HWPX (한글 문서) 변환

템플릿 없이 마크다운 문서를 한글에서 바로 열리는 `.hwpx`로 만든다. HWPX는 OWPML XML을 묶은 zip이라,
파이썬 표준 라이브러리 + lxml(검증용) + Pillow(그림 크기)만으로 생성한다. 한글 프로그램이 없어도 된다.

언제 쓰나

- 계획서·보고서를 md로 다듬은 뒤 **한글 파일로 제출**해야 할 때 (양식 파일이 없을 때)
- 사용자가 한글에서 고친 `.hwpx`를 받아 **md·html 사본을 다시 맞춰야** 할 때 (아래 "역방향 동기화")
- 받은 `.hwpx` 문서를 **읽고 내용을 파악·요약·검토**해야 할 때: 새 빈 폴더에 복사한 뒤
  `python3 -I hwpx_dump.py 문서.hwpx > dump.txt`로 본문·표·수식을 문서 순서대로 뽑아 읽는다.
  `[PIC]`는 그림 위치만 알려 주고, 병합 칸·서식(글꼴·색)은 나오지 않는다는 점을 감안한다. `.hwp`(구형)는 대상이 아니다.
- 이미 있는 양식(.hwpx/.hwp)을 채우거나 일부만 고치는 일이면 이 스킬 대신 hwp-munging 스킬을 쓴다.

## 1. 원고(md) 작성 규칙 — 변환기가 지원하는 문법

| 마크다운                                        | 한글 결과                                                              |
| ----------------------------------------------- | ---------------------------------------------------------------------- |
| `## 제목` / `### 절` / `#### 소제목`            | 함초롬돋움 굵게 16 / 13 / 11pt, 다음 문단과 붙여 쪽 나눔               |
| 일반 문단                                       | 함초롬바탕 10pt, 양쪽 정렬, 줄간격 160%                                |
| `**굵게**`, `` `코드` ``                        | 굵은 글자 / 백틱 제거                                                  |
| `- 항목` (들여쓰기 4칸마다 한 단계, 최대 3단계) | 내어쓰기 목록, 글머리표 • / - / ㆍ                                     |
| `1. 항목`                                       | 굵은 번호 문단                                                         |
| 문단·목록 안의 `<br>`                           | 같은 문단 안 줄바꿈(lineBreak)                                         |
| 마크다운 표 (첫 행 = 머리글)                    | 테두리 표, 머리글 회색 음영·가운데 정렬, 열 너비는 글자 수로 자동 배분 |
| 표 칸 안의 `<br>`                               | 칸 안에서 새 문단                                                      |
| 표 칸에서 `$...\frac{..}{..}...$`만 있는 줄     | **한글 수식 개체**(더블클릭하면 수식 편집기)                           |
| 그 밖의 `$...$` (예: `$\ge 85\%$`)              | 일반 글자로 변환(≥ 85%)                                                |
| `![설명](그림.png)`                             | 본문 폭 95% 그림(경로는 md 기준 상대경로, PNG)                         |
| `---`                                           | 무시                                                                   |

쪽번호는 자동으로 아래 가운데 "- 1 -" 형식. 용지는 A4 세로, 여백 좌우 30mm·위 20mm·아래 15mm.

수식 LaTeX는 `\frac`, `\text{}`, `\left( \right)`, `\times`만 한글 수식 스크립트로 바꾼다
(`{A} over {B}`, `"한글 텍스트"`, `LEFT ( … RIGHT )`, `TIMES`). 다른 명령은 쓰지 말 것.

## 2. 실행

스크립트 세 개를 작업용(스크래치) 폴더에 그대로 써서 실행한다. 사용자 폴더나 업로드 폴더 안에서 실행하지 않는다.

```bash
python3 -I md2hwpx.py 문서.md 문서.hwpx          # 생성
python3 -I hwpx_dump.py 문서.hwpx > dump.txt      # 내용 확인(아래 검증)
```

그림이 HTML(디자인 캔버스 아트보드 등)에 있으면 먼저 PNG로 만든다:

```bash
python3 -I render_png.py page.html 그림.png "body > div" 800 1180
```

- 아트보드(.dc.html)는 `<x-dc>` 안의 본문과 `<helmet>`의 `<style>`만 뽑아 일반 HTML로 저장한 뒤 렌더링한다.
- 웹 글꼴(Google Fonts 등)은 이 환경에서 받지 못하는 경우가 많다. `font-family` 맨 앞을 설치된 한글 글꼴
  (`fc-list :lang=ko`로 확인, 보통 `Noto Sans CJK KR`)로 바꾸고, 사용자에게 글꼴이 대체됐다고 알린다.
- 렌더링한 PNG는 Read로 열어 깨진 글자·잘림이 없는지 눈으로 확인한다.

## 3. 검증 (전달 전 필수)

1. zip·XML 무결성: `zipfile.ZipFile(f).testzip() is None`, 모든 `.xml/.hpf`를 `lxml.etree.fromstring`으로 파싱.
2. `mimetype`이 첫 항목·비압축인지 확인(스크립트가 보장).
3. `hwpx_dump.py` 출력과 md를 문장 단위로 대조해 빠진 문단·표·수식이 없는지 확인.
4. 수식은 `<hp:script>` 내용을, 표는 열 수와 칸 너비를 출력해 확인.

사용자에게 알릴 것: 한글 프로그램 없이 규격대로 만든 파일이라 **실제 열림·레이아웃은 한글에서 확인이 필요**하다.
수식 크기는 추정값이라 어긋나 보이면 수식을 더블클릭해 편집기를 열었다 닫으면 한글이 다시 계산한다.
열리지 않으면 대안으로 html을 한글에서 열어 "다른 이름으로 저장 → HWPX"를 안내한다.

## 4. 역방향 동기화 (사용자가 한글에서 고친 파일 → md/html)

1. 업로드된 `.hwpx`를 새 빈 폴더에 복사해 다룬다(원본 수정 금지). 매직 바이트가 `50 4b`(zip)인지 확인.
2. 사용자 파일과 직전 생성본을 각각 `hwpx_dump.py`로 덤프하고 `diff`로 바뀐 문장을 찾는다.
3. md에 반영할 때 주의:
    - 한글은 가운뎃점 `·`(U+00B7)를 `ㆍ`(U+318D)로 바꾸는 경우가 많다. 사용자가 어느 쪽을 썼는지 그대로 따르고,
      섞여 있으면 알려준다.
    - 새로 생긴 표(예: 연차별 요약표)는 md 표로 옮긴다. 한 칸에 여러 문단이 쌓인 표는 행을 나눠 옮기면 읽기 쉽다.
    - `<hp:lineBreak/>`는 덤프에서 앞뒤 글자가 붙어 보인다 → md에서는 `<br>`로 옮긴다.
4. 반영 후 양방향 확인: (a) 사용자 덤프의 모든 문장이 md에 있는지, (b) md의 모든 문장이 사용자 덤프에 있는지.
   LaTeX로 쓴 수식·기호 칸은 비교에서 제외하고 따로 눈으로 확인한다.
5. html은 md에서 다시 만든다(그림은 base64로 넣어 한 파일로).

## 5. 확장할 때 참고 (OWPML 함정)

- 단위 HWPUNIT: 1pt = 100, 1mm ≈ 283.46. A4 = 59528 × 84186. 본문 폭 = 59528 − 좌우 여백.
- 첫 문단의 첫 run에 `secPr`(용지·여백)과 `colPr`가 있어야 한다. 쪽번호는 다음 run의 `<hp:ctrl><hp:pageNum …/>`.
- `landscape="WIDELY"`가 **세로** 용지다.
- 표·그림·수식은 `treatAsChar="1"`로 글자처럼 문단 안에 둔다. 표 뒤에는 빈 run을 하나 둔다.
- 그림은 `BinData/imageN.png` + `content.hpf` manifest 항목 + `<hc:img binaryItemIDRef="imageN">` 세 곳이 맞아야 한다.
- 수식은 줄바꿈이 안 되므로 들어갈 칸 폭을 넉넉히 주고, 글자 크기(baseUnit)를 폭에 맞춰 줄인다(최소 7pt).
- `linesegarray`(줄 배치 캐시)는 넣지 않는다. 한글이 열 때 다시 계산한다.
- XML 텍스트는 반드시 escape 한다(`&`, `<`, `>`).

## 스크립트

### md2hwpx.py

```python
"""Markdown -> standalone .hwpx (OWPML 2011), no template needed.
Usage: python3 md2hwpx.py input.md output.hwpx
Supports: #~#### headings, paragraphs, **bold**, `code`, - lists (3 levels, 4-space indent), 1. lines,
| tables | (<br> = new paragraph in a cell, $\frac{..}{..}$-only lines -> Hangul equations),
<br> inside paragraphs (line break), ![alt](image.png) (path relative to the .md), bottom-centre page number.
"""
import os, re, sys, zipfile
from xml.sax.saxutils import escape

SRC, DST = sys.argv[1], sys.argv[2]
IMAGES = []  # (zip name, source path)

NS = ('xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
      'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
      'xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" '
      'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
      'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
      'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
      'xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" '
      'xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" '
      'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" '
      'xmlns:dc="http://purl.org/dc/elements/1.1/" '
      'xmlns:opf="http://www.idpf.org/2007/opf/" '
      'xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" '
      'xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" '
      'xmlns:epub="http://www.idpf.org/2007/ops" '
      'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"')
DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'

# ---------------------------------------------------------------- header.xml
LANGS = ["HANGUL", "LATIN", "HANJA", "JAPANESE", "OTHER", "SYMBOL", "USER"]
FONTS = ["함초롬바탕", "함초롬돋움"]  # 0: body, 1: headings

def fontfaces():
    out = [f'<hh:fontfaces itemCnt="{len(LANGS)}">']
    for lang in LANGS:
        out.append(f'<hh:fontface lang="{lang}" fontCnt="{len(FONTS)}">')
        for i, f in enumerate(FONTS):
            fam = "FCAT_GOTHIC" if i else "FCAT_OLDSTYLE"
            out.append(f'<hh:font id="{i}" face="{f}" type="TTF" isEmbedded="0">'
                       f'<hh:typeInfo familyType="{fam}" weight="6" proportion="4" contrast="0" '
                       f'strokeVariation="1" armStyle="1" letterform="1" midline="1" xHeight="1"/></hh:font>')
        out.append('</hh:fontface>')
    out.append('</hh:fontfaces>')
    return "".join(out)

def border_fill(i, line, fill=None):
    b = lambda side: f'<hh:{side} type="{line}" width="0.12 mm" color="#000000"/>'
    brush = (f'<hc:fillBrush><hc:winBrush faceColor="{fill}" hatchColor="#999999" alpha="0"/></hc:fillBrush>'
             if fill else '')
    return (f'<hh:borderFill id="{i}" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
            '<hh:slash type="NONE" Crooked="0" isCounter="0"/><hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
            + b("leftBorder") + b("rightBorder") + b("topBorder") + b("bottomBorder") +
            '<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>' + brush + '</hh:borderFill>')

BORDERFILLS = [border_fill(1, "NONE"), border_fill(2, "NONE", "none"),
               border_fill(3, "SOLID"), border_fill(4, "SOLID", "#F2F2F2")]

def char_pr(i, height, bold=False, font=0, color="#000000"):
    ref = " ".join(f'{k}="{font}"' for k in ["hangul", "latin", "hanja", "japanese", "other", "symbol", "user"])
    same = lambda v: " ".join(f'{k}="{v}"' for k in ["hangul", "latin", "hanja", "japanese", "other", "symbol", "user"])
    return (f'<hh:charPr id="{i}" height="{height}" textColor="{color}" shadeColor="none" useFontSpace="0" '
            f'useKerning="0" symMark="NONE" borderFillIDRef="2">'
            f'<hh:fontRef {ref}/><hh:ratio {same(100)}/><hh:spacing {same(0)}/>'
            f'<hh:relSz {same(100)}/><hh:offset {same(0)}/>' + ('<hh:bold/>' if bold else '') +
            '<hh:underline type="NONE" shape="SOLID" color="#000000"/>'
            '<hh:strikeout shape="NONE" color="#000000"/><hh:outline type="NONE"/>'
            '<hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/></hh:charPr>')

# id: (height, bold, font)
CHARS = {0: (1000, False, 0), 1: (1000, True, 0), 2: (1600, True, 1), 3: (1300, True, 1),
         4: (1100, True, 1), 5: (900, False, 0), 6: (900, True, 0)}
C_BODY, C_BOLD, C_H2, C_H3, C_H4, C_TBL, C_TBLB = range(7)

def para_pr(i, align="JUSTIFY", left=0, indent=0, prev=0, nxt=0, line=160, keep_next=0):
    return (f'<hh:paraPr id="{i}" tabPrIDRef="0" condense="0" fontLineHeight="0" snapToGrid="1" '
            f'suppressLineNumbers="0" checked="0">'
            f'<hh:align horizontal="{align}" vertical="BASELINE"/>'
            '<hh:heading type="NONE" idRef="0" level="0"/>'
            f'<hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="KEEP_WORD" widowOrphan="0" '
            f'keepWithNext="{keep_next}" keepLines="0" pageBreakBefore="0" lineWrap="BREAK"/>'
            '<hh:autoSpacing eAsianEng="0" eAsianNum="0"/>'
            f'<hh:margin><hc:intent value="{indent}" unit="HWPUNIT"/><hc:left value="{left}" unit="HWPUNIT"/>'
            f'<hc:right value="0" unit="HWPUNIT"/><hc:prev value="{prev}" unit="HWPUNIT"/>'
            f'<hc:next value="{nxt}" unit="HWPUNIT"/></hh:margin>'
            f'<hh:lineSpacing type="PERCENT" value="{line}" unit="HWPUNIT"/>'
            '<hh:border borderFillIDRef="2" offsetLeft="0" offsetRight="0" offsetTop="0" offsetBottom="0" '
            'connect="0" ignoreMargin="0"/></hh:paraPr>')

PARAS = [para_pr(0, prev=200),                                   # body
         para_pr(1, align="LEFT", prev=0, nxt=600, keep_next=1),  # h2
         para_pr(2, align="LEFT", prev=1400, nxt=400, keep_next=1),  # h3
         para_pr(3, align="LEFT", prev=1000, nxt=200, keep_next=1),  # h4
         para_pr(4, left=1400, indent=-1400, prev=100),          # list level 0
         para_pr(5, left=2800, indent=-1400, prev=60),           # list level 1
         para_pr(6, left=4200, indent=-1400, prev=60),           # list level 2
         para_pr(7, align="LEFT", line=130),                     # table cell
         para_pr(8, align="CENTER", line=130)]                   # table header cell
P_BODY, P_H2, P_H3, P_H4, P_L0, P_L1, P_L2, P_CELL, P_HCELL = range(9)

def numbering():
    heads = "".join(
        f'<hh:paraHead start="1" level="{lv}" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" '
        f'textOffsetType="PERCENT" textOffset="50" numFormat="DIGIT" charPrIDRef="4294967295" checkable="0">'
        f'^{lv}.</hh:paraHead>' for lv in range(1, 8))
    return f'<hh:numberings itemCnt="1"><hh:numbering id="1" start="0">{heads}</hh:numbering></hh:numberings>'

HEADER = (DECL + f'<hh:head {NS} version="1.4" secCnt="1">'
          '<hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>'
          '<hh:refList>' + fontfaces() +
          f'<hh:borderFills itemCnt="{len(BORDERFILLS)}">' + "".join(BORDERFILLS) + '</hh:borderFills>' +
          f'<hh:charProperties itemCnt="{len(CHARS)}">' +
          "".join(char_pr(i, h, b, f) for i, (h, b, f) in CHARS.items()) + '</hh:charProperties>'
          '<hh:tabProperties itemCnt="1"><hh:tabPr id="0" autoTabLeft="0" autoTabRight="0"/></hh:tabProperties>' +
          numbering() +
          f'<hh:paraProperties itemCnt="{len(PARAS)}">' + "".join(PARAS) + '</hh:paraProperties>'
          '<hh:styles itemCnt="1"><hh:style id="0" type="PARA" name="바탕글" engName="Normal" paraPrIDRef="0" '
          'charPrIDRef="0" nextStyleIDRef="0" langID="1042" lockForm="0"/></hh:styles>'
          '</hh:refList>'
          '<hh:compatibleDocument targetProgram="HWP201X"><hh:layoutCompatibility/></hh:compatibleDocument>'
          '<hh:docOption><hh:linkinfo path="" pageInherit="0" footnoteInherit="0"/></hh:docOption>'
          '<hh:trackchageConfig flags="56"/></hh:head>')

# ---------------------------------------------------------------- section0.xml
TEXT_W = 59528 - 2 * 8504  # A4 width minus left/right margins (HWPUNIT)
_pid = [0]

def pid():
    _pid[0] += 1
    return _pid[0]

def latex_to_text(s):
    s = s.strip("$")
    def frac(s):
        while r"\frac" in s:
            i = s.index(r"\frac")
            def grab(j):
                assert s[j] == "{"
                depth, k = 0, j
                while True:
                    if s[k] == "{": depth += 1
                    elif s[k] == "}":
                        depth -= 1
                        if depth == 0: return s[j + 1:k], k + 1
                    k += 1
            a, j = grab(i + 5)
            b, j = grab(j)
            s = s[:i] + f"({frac(a)}) ÷ ({frac(b)})" + s[j:]
        return s
    s = frac(s)
    s = re.sub(r"\\text\{([^{}]*)\}", r"\1", s)
    for a, b in [(r"\left", ""), (r"\right", ""), (r"\times", "×"), (r"\ge", "≥"), (r"\approx", "≈"),
                 (r"\pm", "±"), (r"\%", "%"), ("{", ""), ("}", "")]:
        s = s.replace(a, b)
    s = re.sub(r"\(\s*([A-Za-z0-9.]+)\s*\)", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()

def clean_inline(s):
    s = re.sub(r"\$[^$]+\$", lambda m: latex_to_text(m.group(0)), s)
    s = re.sub(r"_\(([^)]*)\)_", r"(\1)", s)
    s = s.replace("`", "")
    return s

def runs(text, base_char, bold_char):
    """Split **bold** markers into runs."""
    text = clean_inline(text)
    parts = text.split("**")
    out = []
    for k, part in enumerate(parts):
        if part:
            c = bold_char if k % 2 else base_char
            body = "<hp:lineBreak/>".join(escape(x) for x in re.split(r"<br\s*/?>", part))
            out.append(f'<hp:run charPrIDRef="{c}"><hp:t>{body}</hp:t></hp:run>')
    return "".join(out) or f'<hp:run charPrIDRef="{base_char}"/>'

def para(text, ppr, cchar=C_BODY, bchar=C_BOLD):
    return (f'<hp:p id="{pid()}" paraPrIDRef="{ppr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
            + runs(text, cchar, bchar) + '</hp:p>')

SECPR = ('<hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" tabStopVal="4000" '
         'tabStopUnit="HWPUNIT" outlineShapeIDRef="1" memoShapeIDRef="0" textVerticalWidthHead="0" masterPageCnt="0">'
         '<hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/>'
         '<hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>'
         '<hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" '
         'fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/>'
         '<hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/>'
         '<hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY">'
         '<hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/>'
         '</hp:pagePr>'
         '<hp:footNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>'
         '<hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>'
         '<hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/>'
         '<hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="EACH_COLUMN" beneathText="0"/>'
         '</hp:footNotePr>'
         '<hp:endNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>'
         '<hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/>'
         '<hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/>'
         '<hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="END_OF_DOCUMENT" beneathText="0"/>'
         '</hp:endNotePr>' +
         "".join(f'<hp:pageBorderFill type="{t}" borderFillIDRef="1" textBorder="PAPER" headerInside="0" '
                 f'footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
                 f'</hp:pageBorderFill>' for t in ["BOTH", "EVEN", "ODD"]) +
         '</hp:secPr>')
COLPR = ('<hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/></hp:ctrl>')


def _grab(s, j):
    depth, k = 0, j
    while True:
        if s[k] == "{": depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0: return s[j + 1:k], k + 1
        k += 1

def latex_to_eq(s):
    """LaTeX (subset) -> Hangul equation script."""
    s = s.strip().strip("$")
    out, i = [], 0
    while i < len(s):
        if s.startswith(r"\frac", i):
            a, j = _grab(s, i + 5); b, j = _grab(s, j)
            out.append("{" + latex_to_eq(a) + "} over {" + latex_to_eq(b) + "}"); i = j
        elif s.startswith(r"\text", i):
            a, j = _grab(s, i + 5)
            out.append('"' + a + '"'); i = j
        elif s.startswith(r"\left", i): out.append(" LEFT "); i += 5
        elif s.startswith(r"\right", i): out.append(" RIGHT "); i += 6
        elif s.startswith(r"\times", i): out.append(" TIMES "); i += 6
        else: out.append(s[i]); i += 1
    return re.sub(r"\s+", " ", "".join(out)).strip()

def _em_text(t):
    w = 0.0
    for ch in t:
        if "\uac00" <= ch <= "\ud7a3": w += 1.0
        elif ch == " ": w += 0.3
        elif ch.isascii() and ch.isalnum(): w += 0.55
        else: w += 0.6
    return w

def eq_width_em(s):
    s = s.strip().strip("$")
    w, i = 0.0, 0
    while i < len(s):
        if s.startswith(r"\frac", i):
            a, j = _grab(s, i + 5); b, j = _grab(s, j)
            w += max(eq_width_em(a), eq_width_em(b)) + 0.4; i = j
        elif s.startswith(r"\text", i):
            a, j = _grab(s, i + 5); w += _em_text(a); i = j
        elif s.startswith(r"\left", i) or s.startswith(r"\right", i):
            i += 5 if s.startswith(r"\left", i) else 6; w += 0.1
        elif s.startswith(r"\times", i): w += 1.2; i += 6
        elif s[i] in "{}": i += 1
        else: w += _em_text(s[i]); i += 1
    return w

def equation(latex, avail):
    em = eq_width_em(latex)
    base = max(700, min(1000, int(avail / em) // 10 * 10))
    width = int(em * base) + 300
    height = int(base * 2.5)
    script = escape(latex_to_eq(latex))
    return (f'<hp:run charPrIDRef="{C_TBL}"><hp:equation id="{pid()}" zOrder="0" numberingType="EQUATION" '
            'textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" '
            f'version="Equation Version 60" baseLine="60" textColor="#000000" baseUnit="{base}" '
            'lineMode="CHAR" font="HancomEQN">'
            f'<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>'
            '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" '
            'vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
            '<hp:outMargin left="56" right="56" top="0" bottom="0"/>'
            '<hp:shapeComment>수식입니다.</hp:shapeComment>'
            f'<hp:script>{script}</hp:script></hp:equation></hp:run>')

def eq_para(latex, avail):
    return (f'<hp:p id="{pid()}" paraPrIDRef="{P_CELL}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
            + equation(latex, avail) + '</hp:p>')

def auto_ratios(rows):
    ncol = max(len(r) for r in rows)
    ratios = []
    for c in range(ncol):
        cells = [r[c] for r in rows if c < len(r)]
        longest = max((len(clean_inline(x)) for cell in cells for x in re.split(r"<br\s*/?>", cell)), default=4)
        weight = min(max(longest, 6), 40)
        ratios.append(weight)
    # a column holding fraction equations gets ~45% of the width (equations cannot wrap)
    for c in range(ncol):
        if any(c < len(r) and "\\frac" in r[c] for r in rows[1:]):
            others = sum(w for k, w in enumerate(ratios) if k != c)
            ratios[c] = max(ratios[c], int(others * 0.82))
    return ratios

def table(rows, ratios=None):
    ratios = ratios or auto_ratios(rows)
    ncol = len(ratios)
    widths = [int(TEXT_W * r / sum(ratios)) for r in ratios]
    widths[-1] = TEXT_W - sum(widths[:-1])
    row_h = 1800
    trs = []
    for r, cells in enumerate(rows):
        tcs = []
        for c in range(ncol):
            raw = cells[c] if c < len(cells) else ""
            lines = [l.strip() for l in re.split(r"<br\s*/?>", raw)] or [""]
            hdr = r == 0
            avail = widths[c] - 1020 - 200
            ps = "".join(eq_para(l, avail) if (not hdr and re.fullmatch(r"\$[^$]*\\frac[^$]*\$", l))
                         else para(l, P_HCELL if hdr else P_CELL, C_TBLB if hdr else C_TBL, C_TBLB)
                         for l in lines)
            tcs.append(f'<hp:tc name="" header="{1 if hdr else 0}" hasMargin="0" protect="0" editable="0" dirty="0" '
                       f'borderFillIDRef="{4 if hdr else 3}">'
                       f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" '
                       f'linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" '
                       f'hasNumRef="0">{ps}</hp:subList>'
                       f'<hp:cellAddr colAddr="{c}" rowAddr="{r}"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
                       f'<hp:cellSz width="{widths[c]}" height="{row_h}"/>'
                       f'<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>')
        trs.append('<hp:tr>' + "".join(tcs) + '</hp:tr>')
    tbl = (f'<hp:tbl id="{pid()}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" '
           f'lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="{len(rows)}" colCnt="{ncol}" '
           f'cellSpacing="0" borderFillIDRef="3" noAdjust="0">'
           f'<hp:sz width="{TEXT_W}" widthRelTo="ABSOLUTE" height="{row_h * len(rows)}" heightRelTo="ABSOLUTE" protect="0"/>'
           '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" '
           'vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
           '<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
           '<hp:inMargin left="510" right="510" top="141" bottom="141"/>' + "".join(trs) + '</hp:tbl>')
    return (f'<hp:p id="{pid()}" paraPrIDRef="{P_BODY}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="0">{tbl}</hp:run><hp:run charPrIDRef="0"/></hp:p>')


def picture(path, alt=""):
    from PIL import Image
    ref = f"image{len(IMAGES) + 1}"
    IMAGES.append((f"BinData/{ref}.png", path))
    pw, ph = Image.open(path).size
    width = int(TEXT_W * 0.95)
    height = int(width * ph / pw)
    ow, oh = int(pw / 2.5 * 75), int(ph / 2.5 * 75)
    cw, ch = pw * 75, ph * 75
    pic = (f'<hp:pic id="{pid()}" zOrder="1" numberingType="PICTURE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" '
           'lock="0" dropcapstyle="None" href="" groupLevel="0" instid="{0}" reverse="0">'.format(pid()) +
           '<hp:offset x="0" y="0"/>'
           f'<hp:orgSz width="{ow}" height="{oh}"/><hp:curSz width="{width}" height="{height}"/>'
           '<hp:flip horizontal="0" vertical="0"/>'
           f'<hp:rotationInfo angle="0" centerX="{width // 2}" centerY="{height // 2}" rotateimage="1"/>'
           '<hp:renderingInfo><hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
           f'<hc:scaMatrix e1="{width / ow:.6f}" e2="0" e3="0" e4="0" e5="{height / oh:.6f}" e6="0"/>'
           '<hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/></hp:renderingInfo>'
           f'<hc:img binaryItemIDRef="{ref}" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/>'
           f'<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="{ow}" y="0"/><hc:pt2 x="{ow}" y="{oh}"/>'
           f'<hc:pt3 x="0" y="{oh}"/></hp:imgRect>'
           f'<hp:imgClip left="0" right="{cw}" top="0" bottom="{ch}"/>'
           '<hp:inMargin left="0" right="0" top="0" bottom="0"/>'
           f'<hp:imgDim dimwidth="{cw}" dimheight="{ch}"/><hp:effects/>'
           f'<hp:sz width="{width}" widthRelTo="ABSOLUTE" height="{height}" heightRelTo="ABSOLUTE" protect="0"/>'
           '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" '
           'vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
           '<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
           f'<hp:shapeComment>{escape(alt)}</hp:shapeComment></hp:pic>')
    return (f'<hp:p id="{pid()}" paraPrIDRef="{P_HCELL}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="0">{pic}</hp:run><hp:run charPrIDRef="0"/></hp:p>')

def build_body(md):
    lines = md.splitlines()
    out, i = [], 0
    bullets = ["•", "-", "ㆍ"]
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s or s == "---":
            i += 1; continue
        if s.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].strip()); i += 1
            rows = [[c.strip() for c in r.strip("|").split("|")] for r in block]
            rows = [r for r in rows if not all(re.fullmatch(r":?-+:?", c) for c in r)]
            out.append(table(rows))
            continue
        m = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", s)
        if m:
            path = os.path.join(os.path.dirname(os.path.abspath(SRC)), m.group(2))
            out.append(picture(path, m.group(1)))
            i += 1; continue
        if s.startswith("#### "):
            out.append(para(s[5:], P_H4, C_H4, C_H4))
        elif s.startswith("### "):
            out.append(para(s[4:], P_H3, C_H3, C_H3))
        elif s.startswith("## "):
            out.append(para(s[3:], P_H2, C_H2, C_H2))
        elif re.match(r"\s*- ", line):
            level = min((len(line) - len(line.lstrip(" "))) // 4, 2)
            text = re.sub(r"^\s*- ", "", line)
            out.append(para(f"{bullets[level]}  {text}", [P_L0, P_L1, P_L2][level]))
        elif re.match(r"\d+\. ", s):
            out.append(para(s, P_L0, C_BOLD, C_BOLD))
        elif s.startswith("**") and s.endswith("**"):
            out.append(para(s, P_H4 if s.startswith("**[") else P_BODY, C_BOLD, C_BOLD))
        else:
            out.append(para(s, P_BODY))
        i += 1
    return out

md = open(SRC, encoding="utf-8").read()
_t = re.search(r"^#{1,4}\s+(.+)$", md, re.M)
TITLE = clean_inline(_t.group(1)).replace("**", "") if _t else os.path.splitext(os.path.basename(SRC))[0]
body = build_body(md)
# first paragraph carries the section/page definition
first = (f'<hp:p id="{pid()}" paraPrIDRef="{P_BODY}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
         f'<hp:run charPrIDRef="0">{SECPR}{COLPR}</hp:run>'
         '<hp:run charPrIDRef="0"><hp:ctrl><hp:pageNum pos="BOTTOM_CENTER" formatType="DIGIT" sideChar="-"/></hp:ctrl></hp:run>'
         '<hp:run charPrIDRef="0"/></hp:p>')
SECTION = DECL + f'<hs:sec {NS}>' + first + "".join(body) + '</hs:sec>'

# ---------------------------------------------------------------- package files
VERSION = (DECL + '<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" '
           'tagetApplication="WORDPROCESSOR" major="5" minor="1" micro="0" buildNumber="1" os="1" '
           'xmlVersion="1.4" application="Hancom Office Hangul" appVersion="11, 0, 0, 0"/>')
CONTAINER = (DECL + '<ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container" '
             'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf"><ocf:rootfiles>'
             '<ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/>'
             '</ocf:rootfiles></ocf:container>')
MANIFEST = DECL + '<odf:manifest xmlns:odf="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>'
CONTENT = (DECL + f'<opf:package {NS} version="" unique-identifier="" id="">'
           f'<opf:metadata><opf:title>{escape(TITLE)}</opf:title><opf:language>ko</opf:language>'
           '<opf:meta name="creator" content="text"/></opf:metadata>'
           '<opf:manifest>'
           '<opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>'
           '<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>'
           '<opf:item id="settings" href="settings.xml" media-type="application/xml"/>' +
           "".join(f'<opf:item id="{os.path.splitext(os.path.basename(n))[0]}" href="{n}" media-type="image/png" '
                   'isEmbeded="1"/>' for n, _ in IMAGES) +
           '</opf:manifest><opf:spine>'
           '<opf:itemref idref="header" linear="yes"/><opf:itemref idref="section0" linear="yes"/>'
           '</opf:spine></opf:package>')
SETTINGS = (DECL + '<ha:HWPApplicationSetting xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
            'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0">'
            '<ha:CaretPosition listIDRef="0" paraIDRef="0" pos="0"/></ha:HWPApplicationSetting>')

with zipfile.ZipFile(DST, "w") as z:
    z.writestr(zipfile.ZipInfo("mimetype"), "application/hwp+zip", compress_type=zipfile.ZIP_STORED)
    for name, data in [("version.xml", VERSION), ("META-INF/container.xml", CONTAINER),
                       ("META-INF/manifest.xml", MANIFEST), ("Contents/content.hpf", CONTENT),
                       ("Contents/header.xml", HEADER), ("Contents/section0.xml", SECTION),
                       ("settings.xml", SETTINGS)]:
        z.writestr(name, data.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)
    for name, path in IMAGES:
        z.write(path, name, compress_type=zipfile.ZIP_STORED)
print("paragraphs:", len(body))
```

### hwpx_dump.py

```python
"""Dump the text of an .hwpx in reading order (paragraphs, tables, equations, pictures).
Usage: python3 hwpx_dump.py file.hwpx > dump.txt"""
import sys, zipfile
from lxml import etree
L = lambda e: etree.QName(e.tag).localname

def ptext(p):
    out = []
    for e in p.iter():
        n = L(e)
        if n == 't':
            out.append((e.text or '') + ''.join((c.tail or '') for c in e))
        elif n == 'script':
            out.append('[EQ:' + (e.text or '') + ']')
        elif n == 'pic':
            out.append('[PIC]')
    return ''.join(out)

z = zipfile.ZipFile(sys.argv[1])
names = sorted(n for n in z.namelist() if n.startswith('Contents/section') and n.endswith('.xml'))
for name in names:
    sec = etree.fromstring(z.read(name))
    for p in sec:
        if L(p) != 'p':
            continue
        tbl = next((e for e in p.iter() if L(e) == 'tbl'), None)
        if tbl is None:
            txt = ptext(p)
            if txt.strip():
                print(txt)
            continue
        print('[TABLE]')
        for tr in (c for c in tbl if L(c) == 'tr'):
            cells = []
            for tc in (c for c in tr if L(c) == 'tc'):
                sub = next(c for c in tc if L(c) == 'subList')
                cells.append(' / '.join(ptext(pp) for pp in sub if L(pp) == 'p'))
            print(' | '.join(cells))
        print('[/TABLE]')
```

### render_png.py

```python
"""Render an HTML file (or one element of it) to a high-resolution PNG and trim empty bottom space.
Usage: python3 render_png.py page.html out.png [css-selector] [width] [height]"""
import sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageOps
src, out = sys.argv[1], sys.argv[2]
sel = sys.argv[3] if len(sys.argv) > 3 else "body > *"
w = int(sys.argv[4]) if len(sys.argv) > 4 else 800
h = int(sys.argv[5]) if len(sys.argv) > 5 else 1200
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2.5)
    pg.goto("file://" + __import__("os").path.abspath(src))
    pg.wait_for_timeout(400)
    pg.locator(sel).first.screenshot(path=out)
    b.close()
im = Image.open(out).convert("RGB")
box = ImageOps.invert(im).getbbox()
if box:
    im.crop((0, 0, im.width, min(im.height, box[3] + 70))).save(out, optimize=True)
```
