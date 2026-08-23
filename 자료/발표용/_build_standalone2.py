#!/usr/bin/env python3
"""
자료/슬라이드/*.html → 자료/발표용/발표용2_standalone.html

각 슬라이드를 srcdoc iframe으로 임베드:
- venue 섹션 제거 (국가인공지능전략위원회 세미나)
- 이미지 base64 인라인 (로고·AI검색·해커톤·산재사진)
- 데이터맵_트리.html srcdoc 인라인
- 오프라인 완전 독립 HTML
"""
import re
import base64
import sys
from pathlib import Path

DIR        = Path(__file__).parent           # 자료/발표용/
SLIDES_DIR = DIR.parent / "슬라이드"         # 자료/슬라이드/
ASSETS_DIR = DIR.parent                      # 자료/
DST        = DIR / "발표용2_standalone.html"

SLIDE_ORDER = [
    "01_표지.html",
    "02_순서.html",
    "03_문제정의.html",
    "04_AI로_풀_수_있는가.html",
    "05_고용노동부와_AX.html",
    "06_데이터맵.html",
    "07_핵심서비스.html",
    "08_현장작동.html",
    "09_법령현황.html",
    "10_예산.html",
    "10_1_정보화예산현황.html",
    "11_AI노동법상담.html",
    "12_3월이용현황.html",
    "13_산업안전AI.html",
    "14_AI직원검색.html",
    "15_AX기본전략.html",
    "16_현장중심_신속피드백.html",
    "17_지속가능한혁신.html",
    "18_마무리.html",
]

MIME = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".svg":  "image/svg+xml",
}


def to_data_url(path: Path) -> str:
    mime = MIME.get(path.suffix.lower(), "application/octet-stream")
    b64  = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def inline_css_urls(html: str) -> str:
    """url('../xxx.png') → data URL (단, url(#...) 등 fragment는 건너뜀)."""
    def replacer(m):
        raw  = m.group(1)          # 따옴표 포함 원본
        path = raw.strip("'\"")
        # fragment / 절대 URL / data URI는 건너뜀
        if path.startswith("#") or path.startswith("http") or path.startswith("data:"):
            return m.group(0)
        # 슬라이드 기준 상대경로 해결 (자료/슬라이드/ 기준)
        img_path = (SLIDES_DIR / path).resolve()
        if not img_path.exists():
            print(f"  [!] CSS url 누락: {path}", file=sys.stderr)
            return m.group(0)
        return f"url('{to_data_url(img_path)}')"

    return re.sub(r"url\((['\"]?[^)\"']+['\"]?)\)", replacer, html)


def inline_img_srcs(html: str) -> str:
    """<img src="..."> → base64 (http / data: / fragment / .html / 쿼리스트링은 건너뜀)."""
    def replacer(m):
        src = m.group(1)
        # 건너뛸 케이스
        if (src.startswith("http") or src.startswith("data:")
                or src.startswith("#") or "?" in src
                or src.lower().endswith(".html")):
            return m.group(0)
        img_path = (SLIDES_DIR / src).resolve()
        if not img_path.exists():
            print(f"  [!] img src 누락: {src}", file=sys.stderr)
            return m.group(0)
        return f'src="{to_data_url(img_path)}"'

    return re.sub(r'src="([^"]+)"', replacer, html)


def inline_datamap_iframe(html: str) -> str:
    """06_데이터맵의 <iframe src="../데이터맵_트리.html?..."> → data URI 인라인.

    srcdoc-in-srcdoc은 이중 escape로 내용이 깨지므로,
    base64 data URI(src=)를 사용해 중첩 escape 문제를 회피한다.
    """
    pattern = r'<iframe\s+src="../데이터맵_트리\.html[^"]*"([^>]*)>'
    m = re.search(pattern, html)
    if not m:
        return html

    # 트리 파일 탐색: 자료/ 또는 자료/발표용/
    for candidate in [ASSETS_DIR / "데이터맵_트리.html", DIR / "데이터맵_트리.html"]:
        if candidate.exists():
            tree_html = candidate.read_text(encoding="utf-8")
            break
    else:
        print("  [!] 데이터맵_트리.html 누락", file=sys.stderr)
        return html

    # embed 클래스 부여 (헤더 숨김 · fit-to-view 동작)
    tree_html = tree_html.replace("<body>", '<body class="embed">', 1)

    # base64 data URI → srcdoc 이중 escape 없이 중첩 가능
    b64 = base64.b64encode(tree_html.encode("utf-8")).decode("ascii")
    data_uri = f"data:text/html;charset=utf-8;base64,{b64}"

    attrs = m.group(1)  # title="..." 등 나머지 속성
    new_iframe = f'<iframe src="{data_uri}"{attrs}>'
    return re.sub(pattern, new_iframe, html, count=1)


def remove_venue(html: str) -> str:
    """<div class="venue">...</div> 제거."""
    return re.sub(
        r'<div\s+class="venue">.*?</div>',
        '',
        html,
        flags=re.DOTALL,
    )


def escape_srcdoc(html: str) -> str:
    """srcdoc 속성값용 이스케이프."""
    return html.replace("&", "&amp;").replace('"', "&quot;")


def process_slide(fname: str) -> str:
    path = SLIDES_DIR / fname
    html = path.read_text(encoding="utf-8")

    html = remove_venue(html)
    html = inline_css_urls(html)
    if fname == "06_데이터맵.html":
        html = inline_datamap_iframe(html)
    html = inline_img_srcs(html)

    return escape_srcdoc(html)


def build() -> int:
    n = len(SLIDE_ORDER)
    pages_html = []

    for i, fname in enumerate(SLIDE_ORDER):
        path = SLIDES_DIR / fname
        if not path.exists():
            print(f"[!] 누락: {path}", file=sys.stderr)
            return 1
        print(f"  [{i+1:02d}/{n}] {fname}")
        srcdoc = process_slide(fname)
        active = ' active' if i == 0 else ''
        pages_html.append(
            f'  <div class="slide-page{active}" id="p{i+1}">\n'
            f'    <iframe srcdoc="{srcdoc}" scrolling="no"></iframe>\n'
            f'  </div>'
        )

    output = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>고용노동부 AX 전략 발표</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      width: 100%; height: 100%;
      background: #000;
      overflow: hidden;
      font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
    }}
    .slide-page {{
      display: none;
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
    }}
    .slide-page.active {{ display: block; }}
    .slide-page iframe {{
      width: 100%; height: 100%;
      border: none;
      display: block;
      background: #050a16;
    }}

    /* 내비게이션 바 */
    #nav {{
      position: fixed; bottom: 22px; left: 50%; transform: translateX(-50%);
      z-index: 99999;
      display: flex; align-items: center; gap: 14px;
      background: rgba(5,10,22,0.80);
      border: 1px solid rgba(56,189,248,0.22);
      border-radius: 40px; padding: 8px 22px;
      backdrop-filter: blur(12px);
      opacity: 0; transition: opacity 0.25s;
      pointer-events: none;
    }}
    body:hover #nav {{ opacity: 1; pointer-events: auto; }}
    #nav button {{
      background: none;
      border: 1px solid rgba(56,189,248,0.32);
      color: #7dd3fc; border-radius: 50%;
      width: 32px; height: 32px;
      font-size: 14px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: background 0.15s;
    }}
    #nav button:hover {{ background: rgba(56,189,248,0.18); }}
    #ctr {{
      color: #94a3b8; font-size: 13px;
      letter-spacing: 0.14em; min-width: 56px; text-align: center;
    }}

    /* 진행 바 */
    #progress {{
      position: fixed; bottom: 0; left: 0; height: 3px;
      background: linear-gradient(90deg, #38bdf8, #60a5fa);
      transition: width 0.28s ease; z-index: 99999; pointer-events: none;
    }}
  </style>
</head>
<body>

{chr(10).join(pages_html)}

  <div id="nav">
    <button id="btn-first" title="처음으로 (Home)">⏮</button>
    <button id="btn-prev"  title="이전 (←)">◀</button>
    <span   id="ctr">1 / {n}</span>
    <button id="btn-next"  title="다음 (→)">▶</button>
    <button id="btn-last"  title="마지막으로 (End)">⏭</button>
  </div>
  <div id="progress"></div>

  <script>
    const TOTAL = {n};
    let cur = 1;
    const pages = document.querySelectorAll('.slide-page');
    const ctr   = document.getElementById('ctr');
    const prog  = document.getElementById('progress');

    function go(n) {{
      n = Math.max(1, Math.min(TOTAL, n));
      if (n === cur) return;
      pages[cur - 1].classList.remove('active');
      cur = n;
      pages[cur - 1].classList.add('active');
      ctr.textContent  = cur + ' / ' + TOTAL;
      prog.style.width = (cur / TOTAL * 100) + '%';
    }}

    document.getElementById('btn-first').onclick = () => go(1);
    document.getElementById('btn-prev') .onclick = () => go(cur - 1);
    document.getElementById('btn-next') .onclick = () => go(cur + 1);
    document.getElementById('btn-last') .onclick = () => go(TOTAL);

    document.addEventListener('keydown', e => {{
      const fwd = ['ArrowRight', 'ArrowDown', ' ', 'PageDown'];
      const bwd = ['ArrowLeft',  'ArrowUp',        'PageUp'];
      if (fwd.includes(e.key)) {{ e.preventDefault(); go(cur + 1); }}
      else if (bwd.includes(e.key)) {{ e.preventDefault(); go(cur - 1); }}
      else if (e.key === 'Home') {{ e.preventDefault(); go(1); }}
      else if (e.key === 'End')  {{ e.preventDefault(); go(TOTAL); }}
    }});

    // 초기 진행 상태
    prog.style.width = (1 / TOTAL * 100) + '%';
  </script>
</body>
</html>"""

    DST.write_text(output, encoding="utf-8")
    size_mb = len(output.encode("utf-8")) / 1024 / 1024
    print(f"\n[OK] {DST.name}  ({size_mb:.1f} MB, {n} slides)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
