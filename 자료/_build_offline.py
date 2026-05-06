#!/usr/bin/env python3
"""
발표_off.html 빌더 (직접 삽입 방식 기반)
발표.html의 @import CDN 줄 하나만 inline font-face CSS로 교체
폰트는 외부 <style>에 1회만 내장 → 최소 파일 크기
"""
import os, re, base64, urllib.request, time
from urllib.parse import urljoin

INPUT  = r"C:\Workspace\AI_PT\자료\발표용\발표.html"
OUTPUT = r"C:\Workspace\AI_PT\자료\발표용\발표_off.html"

FONT_CSS_URL     = "https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css"
REQUIRED_WEIGHTS = {500, 600, 700, 800, 900}

HEADERS_CSS  = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0'}
HEADERS_FONT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0',
    'Accept': '*/*',
    'Referer': 'https://cdn.jsdelivr.net/',
}

def fetch_text(url):
    req = urllib.request.Request(url, headers=HEADERS_CSS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8')

def fetch_binary(url):
    req = urllib.request.Request(url, headers=HEADERS_FONT)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

# ── 폰트 다운로드 ──────────────────────────────────────────────────────────
print("Pretendard CSS 다운로드...")
css_raw = fetch_text(FONT_CSS_URL)
face_blocks = re.findall(r'@font-face\s*\{[^}]+\}', css_raw, re.DOTALL)
print(f"  font-face {len(face_blocks)}개 중 weight {sorted(REQUIRED_WEIGHTS)} 선택")

inline_faces = []
for block in face_blocks:
    wm = re.search(r'font-weight:\s*(\d+)', block)
    if not wm or int(wm.group(1)) not in REQUIRED_WEIGHTS:
        continue
    weight = int(wm.group(1))
    woff2_m = re.search(r"url\(['\"]?([^'\")\s]+\.woff2)['\"]?\)", block)
    if not woff2_m:
        continue

    abs_url = urljoin(FONT_CSS_URL, woff2_m.group(1))
    fname   = abs_url.split('/')[-1]
    print(f"  다운로드 weight {weight}: {fname}", end='', flush=True)
    try:
        raw = fetch_binary(abs_url)
        b64 = base64.b64encode(raw).decode('ascii')
        print(f"  ({len(raw)//1024} KB)")
        time.sleep(0.1)
    except Exception as e:
        print(f"  실패: {e}")
        continue

    fm = re.search(r"font-family:\s*([^;]+);", block)
    family = fm.group(1).strip() if fm else "'Pretendard'"
    inline_faces.append(
        f"@font-face{{"
        f"font-family:{family};"
        f"font-weight:{weight};"
        f"font-style:normal;"
        f"font-display:swap;"
        f"src:url('data:font/woff2;base64,{b64}') format('woff2');"
        f"}}"
    )

FONT_CSS_INLINE = "\n".join(inline_faces)
print(f"\n폰트 {len(inline_faces)}개 내장 완료: {len(FONT_CSS_INLINE)//1024} KB")

# ── 발표.html 읽기 & @import 교체 ─────────────────────────────────────────
print("발표.html 읽는 중...")
with open(INPUT, encoding='utf-8') as f:
    html = f.read()

# 외부 <style>의 @import 한 줄만 교체
IMPORT_RE = re.compile(
    r"@import\s+url\(['\"][^'\"]*pretendard[^'\"]*['\"][^)]*\)\s*;?",
    re.IGNORECASE,
)
html_off = IMPORT_RE.sub(FONT_CSS_INLINE, html, count=1)

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html_off)

size_mb = os.path.getsize(OUTPUT) / 1024 / 1024
print(f"\n완료! → {OUTPUT}")
print(f"파일 크기: {size_mb:.1f} MB")
