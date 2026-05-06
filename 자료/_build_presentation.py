#!/usr/bin/env python3
"""
고용노동부 AX 슬라이드 발표용 단일 HTML 빌더
- 18개 슬라이드를 srcdoc iframe으로 통합
- 이미지(png/jpg/webp)는 base64 data URI로 인라인
- 데이터맵_트리.html도 슬라이드 06 안에 srcdoc으로 완전 인라인
→ 발표.html 파일 하나만 있으면 발표 가능
"""
import os, base64, re, mimetypes, json, shutil

SLIDE_DIR  = r"C:\Workspace\AI_PT\자료\슬라이드"
ASSET_DIR  = r"C:\Workspace\AI_PT\자료"
OUTPUT_DIR = r"C:\Workspace\AI_PT\자료\발표용"

os.makedirs(OUTPUT_DIR, exist_ok=True)

slide_names = sorted(f for f in os.listdir(SLIDE_DIR) if f.endswith('.html'))
print(f"슬라이드 {len(slide_names)}개 발견")

# ---------- 이미지 → base64 data URI ----------
_img_cache = {}
IMG_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}

def to_data_uri(abs_path):
    key = abs_path.split('?')[0].replace('\\', '/')
    if key in _img_cache:
        return _img_cache[key]
    mime = mimetypes.guess_type(key)[0] or 'application/octet-stream'
    with open(key, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    uri = f"data:{mime};base64,{b64}"
    _img_cache[key] = uri
    return uri

# ---------- 데이터맵_트리.html → base64 ----------
TREE_PATH = os.path.join(ASSET_DIR, '데이터맵_트리.html')
with open(TREE_PATH, encoding='utf-8') as f:
    tree_html_raw = f.read()

# 트리 HTML 자체도 이미지가 있으면 인라인 처리
def fix_tree_images(html):
    def fix_src(m):
        ref = m.group(1)
        if ref.startswith('../'):
            relative = ref[3:].split('?')[0]
            abs_path = os.path.join(ASSET_DIR, *relative.split('/'))
            ext = os.path.splitext(relative)[1].lower()
            if ext in IMG_EXTS and os.path.exists(abs_path):
                return f'src="{to_data_uri(abs_path)}"'
        return m.group(0)
    html = re.sub(r'src="(\.\.[^"]+)"', fix_src, html)
    return html

tree_html_processed = fix_tree_images(tree_html_raw)
TREE_B64 = base64.b64encode(tree_html_processed.encode('utf-8')).decode('ascii')
print(f"  데이터맵_트리.html 인라인 준비: {len(TREE_B64):,} chars b64")

# ---------- 슬라이드 HTML 전처리 ----------
def process_slide(html_path):
    with open(html_path, encoding='utf-8') as f:
        html = f.read()

    # src="../..." → data URI (이미지) 또는 내부 처리 (html)
    def fix_src(m):
        ref = m.group(1)
        if not ref.startswith('../'):
            return m.group(0)
        relative = ref[3:].split('?')[0]
        abs_path = os.path.join(ASSET_DIR, *relative.replace('/', os.sep).split(os.sep))
        ext = os.path.splitext(relative)[1].lower()

        if ext in IMG_EXTS and os.path.exists(abs_path):
            return f'src="{to_data_uri(abs_path)}"'

        if '데이터맵_트리' in relative:
            # 이 src 속성을 id 기반으로 교체하고 나중에 srcdoc 주입
            return 'src="" id="_tree_frame"'

        return m.group(0)

    html = re.sub(r'src="(\.\.[^"]+)"', fix_src, html)

    # url('../...') in CSS
    def fix_url(m):
        q   = m.group(1)
        ref = m.group(2)
        if not ref.startswith('../'):
            return m.group(0)
        relative = ref[3:].split('?')[0]
        abs_path = os.path.join(ASSET_DIR, *relative.replace('/', os.sep).split(os.sep))
        ext = os.path.splitext(relative)[1].lower()
        if ext in IMG_EXTS and os.path.exists(abs_path):
            return f"url({q}{to_data_uri(abs_path)}{q})"
        return m.group(0)

    html = re.sub(r"url\((['\"])(\.\.[^'\"]+)\1\)", fix_url, html)

    # 슬라이드 06: _tree_frame이 있으면 srcdoc 주입 스크립트 삽입
    if 'id="_tree_frame"' in html:
        inject = f"""
<script>
(function(){{
  var b = '{TREE_B64}';
  var bytes = Uint8Array.from(atob(b), function(c){{return c.charCodeAt(0);}});
  var h = new TextDecoder('utf-8').decode(bytes);
  var f = document.getElementById('_tree_frame');
  if (f) f.srcdoc = h;
}})();
</script>"""
        html = html.replace('</body>', inject + '\n</body>')
        print("  → 슬라이드 06: 데이터맵_트리.html srcdoc 주입 완료")

    return html

# ---------- 슬라이드 처리 & b64 인코딩 ----------
slides_b64 = []
for name in slide_names:
    path = os.path.join(SLIDE_DIR, name)
    processed = process_slide(path)
    encoded = base64.b64encode(processed.encode('utf-8')).decode('ascii')
    slides_b64.append(encoded)
    print(f"  처리 완료: {name}  ({len(encoded):,} chars b64)")

N = len(slides_b64)
slides_json = json.dumps(slides_b64, ensure_ascii=True)

# ---------- 발표용 HTML 생성 ----------
html_out = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>고용노동부 AX 전략 발표 | 국가인공지능전략위원회</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ width: 100%; height: 100%; background: #000; overflow: hidden; font-family: sans-serif; }}
    #deck {{ width: 100%; height: 100%; position: relative; }}
    iframe.frame {{
      position: absolute; width: 100%; height: 100%;
      border: none; display: none;
    }}
    iframe.frame.active {{ display: block; }}

    /* 내비게이션 — 마우스 올릴 때만 표시 */
    #nav {{
      position: fixed; bottom: 22px; left: 50%; transform: translateX(-50%);
      z-index: 9999;
      display: flex; align-items: center; gap: 14px;
      background: rgba(5, 10, 22, 0.70);
      border: 1px solid rgba(56, 189, 248, 0.20);
      border-radius: 40px; padding: 8px 22px;
      backdrop-filter: blur(10px);
      opacity: 0; transition: opacity 0.25s;
      pointer-events: none;
    }}
    body:hover #nav {{ opacity: 1; pointer-events: auto; }}
    #nav button {{
      background: none;
      border: 1px solid rgba(56, 189, 248, 0.30);
      color: #7dd3fc; border-radius: 50%;
      width: 30px; height: 30px; font-size: 13px;
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      transition: background 0.15s;
    }}
    #nav button:hover {{ background: rgba(56, 189, 248, 0.15); }}
    #ctr {{
      color: #94a3b8; font-size: 13px;
      letter-spacing: 0.14em; min-width: 52px; text-align: center;
    }}
    #progress {{
      position: fixed; bottom: 0; left: 0; height: 3px;
      background: linear-gradient(90deg, #38bdf8, #60a5fa);
      transition: width 0.25s ease; z-index: 9999;
      pointer-events: none;
    }}
  </style>
</head>
<body>
  <div id="deck"></div>

  <div id="nav">
    <button id="btn-prev" title="이전 슬라이드 (←)">&#9664;</button>
    <span id="ctr">1 / {N}</span>
    <button id="btn-next" title="다음 슬라이드 (→)">&#9654;</button>
  </div>
  <div id="progress"></div>

  <script>
    const SLIDES = {slides_json};
    const N = SLIDES.length;
    let cur = 0;

    function b64decode(b64) {{
      var bytes = Uint8Array.from(atob(b64), function(c) {{ return c.charCodeAt(0); }});
      return new TextDecoder('utf-8').decode(bytes);
    }}

    var deck = document.getElementById('deck');
    var frames = SLIDES.map(function(_, i) {{
      var f = document.createElement('iframe');
      f.className = 'frame';
      f.id = 'f' + i;
      deck.appendChild(f);
      return f;
    }});

    var loaded = new Set();
    function load(i) {{
      if (i < 0 || i >= N || loaded.has(i)) return;
      loaded.add(i);
      frames[i].srcdoc = b64decode(SLIDES[i]);
    }}

    function show(n) {{
      n = Math.max(0, Math.min(N - 1, n));
      frames[cur].classList.remove('active');
      cur = n;
      frames[cur].classList.add('active');
      load(cur);
      load(cur + 1);
      load(cur - 1);
      document.getElementById('ctr').textContent = (cur + 1) + ' / ' + N;
      document.getElementById('progress').style.width = ((cur + 1) / N * 100).toFixed(1) + '%';
    }}

    document.getElementById('btn-prev').onclick = function() {{ show(cur - 1); }};
    document.getElementById('btn-next').onclick = function() {{ show(cur + 1); }};

    document.addEventListener('keydown', function(e) {{
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {{ e.preventDefault(); show(cur + 1); }}
      if (e.key === 'ArrowLeft'  || e.key === 'PageUp')                   {{ e.preventDefault(); show(cur - 1); }}
      if (e.key === 'Home') show(0);
      if (e.key === 'End')  show(N - 1);
    }});

    show(0);
  </script>
</body>
</html>"""

out_path = os.path.join(OUTPUT_DIR, '발표.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html_out)

size_mb = os.path.getsize(out_path) / 1024 / 1024
print(f"\n완료! → {out_path}")
print(f"파일 크기: {size_mb:.1f} MB  |  슬라이드: {N}개")
print("발표용 폴더 내용:")
for fn in os.listdir(OUTPUT_DIR):
    fp = os.path.join(OUTPUT_DIR, fn)
    print(f"  {fn}  ({os.path.getsize(fp)/1024:.0f} KB)")
