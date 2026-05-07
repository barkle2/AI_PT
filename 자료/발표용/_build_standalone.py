"""
발표_off.html + 외부 자원(이미지 4, 데이터맵 트리 1)을 단일 HTML로 인라인.
결과: 발표용_standalone.html
"""
from pathlib import Path
import base64
import sys

DIR = Path(__file__).parent
SRC = DIR / "발표_off.html"
DST = DIR / "발표용_standalone.html"
TREE = DIR / "데이터맵_트리.html"

IMAGES = [
    ("고용노동부.png",                "image/png",  "url"),   # CSS background
    ("AI검색2.png",                   "image/png",  "img"),
    ("해커톤.png",                    "image/png",  "img"),
    ("산재위험사진/바닥기름.jpg",      "image/jpeg", "img"),
]


def to_data_url(path: Path, mime: str) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def main() -> int:
    html = SRC.read_text(encoding="utf-8")
    original_size = len(html)

    # 1) 이미지 인라인
    replacements = []
    for rel, mime, kind in IMAGES:
        p = DIR / rel
        if not p.exists():
            print(f"[!] 누락: {p}", file=sys.stderr)
            return 1
        data_url = to_data_url(p, mime)
        if kind == "url":
            old = f"url('{rel}')"
            new = f"url('{data_url}')"
        else:
            old = f'src="{rel}"'
            new = f'src="{data_url}"'
        if old not in html:
            print(f"[!] 참조 미발견: {old[:60]}...", file=sys.stderr)
            return 1
        count = html.count(old)
        html = html.replace(old, new)
        replacements.append((rel, count, len(data_url)))

    # 2) 데이터맵 트리 인라인 (iframe srcdoc)
    tree_html = TREE.read_text(encoding="utf-8")
    # ?embed=1 쿼리스트링이 srcdoc에서는 적용 안 되므로 body에 직접 클래스 부여
    if "<body>" not in tree_html:
        print("[!] <body> 태그를 찾을 수 없음", file=sys.stderr)
        return 1
    tree_html = tree_html.replace("<body>", '<body class="embed">', 1)
    # srcdoc 속성용 이스케이프: & 먼저, 그 다음 "
    tree_escaped = tree_html.replace("&", "&amp;").replace('"', "&quot;")

    old_iframe = '<iframe src="데이터맵_트리.html?embed=1" title="고용노동부 데이터맵 인터랙티브 트리"></iframe>'
    new_iframe = f'<iframe srcdoc="{tree_escaped}" title="고용노동부 데이터맵 인터랙티브 트리"></iframe>'
    if old_iframe not in html:
        print("[!] iframe 참조 미발견", file=sys.stderr)
        return 1
    html = html.replace(old_iframe, new_iframe)

    # 3) 결과 저장 (UTF-8, BOM 없음)
    DST.write_text(html, encoding="utf-8")

    # 4) 리포트
    print(f"원본 크기 : {original_size:>12,} bytes  ({SRC.name})")
    print(f"결과 크기 : {len(html):>12,} bytes  ({DST.name})")
    print()
    print("인라인 자원:")
    for rel, count, dsize in replacements:
        print(f"  - {rel:35s} x{count}  data URL {dsize:,} chars")
    print(f"  - 데이터맵_트리.html               x1  srcdoc {len(tree_escaped):,} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
