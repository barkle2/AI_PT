#!/usr/bin/env python3
"""
발표.html 빌더 (직접 삽입 방식)
- 각 슬라이드의 HTML을 <section> 블록으로 그대로 삽입
- CSS는 .s01 / .s02 ... prefix로 스코핑해서 충돌 방지
- 이미지는 발표용 폴더로 복사 후 상대경로 참조
- 데이터맵 트리는 발표용 폴더의 파일 직접 참조
"""
import os, re, shutil

SLIDE_DIR  = r"C:\Workspace\AI_PT\자료\슬라이드"
ASSET_DIR  = r"C:\Workspace\AI_PT\자료"
OUTPUT_DIR = r"C:\Workspace\AI_PT\자료\발표용"
OUTPUT     = os.path.join(OUTPUT_DIR, '발표.html')

slide_names = sorted(f for f in os.listdir(SLIDE_DIR) if f.endswith('.html'))
IMG_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}

# ────────────────────────────────────────────────────────────────────────────
# 이미지 → 발표용 폴더로 복사 + 상대경로 반환
# ────────────────────────────────────────────────────────────────────────────
_copied = set()

def copy_asset(clean_path):
    """clean_path: 'go용노동부.png' 또는 '산재위험사진/바닥기름.jpg' 형태
    발표용 폴더로 복사하고 상대경로(발표.html 기준)를 반환."""
    src = os.path.join(ASSET_DIR, *clean_path.replace('/', os.sep).split(os.sep))
    dst = os.path.join(OUTPUT_DIR, *clean_path.replace('/', os.sep).split(os.sep))
    if clean_path not in _copied and os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        _copied.add(clean_path)
        print(f'    복사: {clean_path}')
    return clean_path   # 발표.html 기준 상대경로

def fix_assets(html):
    """../x.png → 복사 후 상대경로  |  ../데이터맵_트리.html → 직접 참조"""
    def fix_src(m):
        ref = m.group(1)
        if not ref.startswith('../'):
            return m.group(0)
        clean = ref[3:].split('?')[0]
        ext   = os.path.splitext(clean)[1].lower()
        if ext in IMG_EXTS:
            return f'src="{copy_asset(clean)}"'
        if '데이터맵_트리' in clean:
            qs = ('?' + ref[3:].split('?', 1)[1]) if '?' in ref[3:] else ''
            return f'src="데이터맵_트리.html{qs}"'
        return m.group(0)

    def fix_url(m):
        q, ref = m.group(1), m.group(2)
        if not ref.startswith('../'):
            return m.group(0)
        clean = ref[3:].split('?')[0]
        ext   = os.path.splitext(clean)[1].lower()
        if ext in IMG_EXTS:
            return f"url({q}{copy_asset(clean)}{q})"
        return m.group(0)

    html = re.sub(r'src="(\.\.[^"]+)"',            fix_src, html)
    html = re.sub(r"url\((['\"])(\.\.[^'\"]+)\1\)", fix_url, html)
    return html

# ────────────────────────────────────────────────────────────────────────────
# CSS 스코핑
# ────────────────────────────────────────────────────────────────────────────

def scope_selector(sel_str, sid):
    """콤마로 분리된 선택자 각각에 .sid 붙이기. html/body 선택자는 제거."""
    parts = [p.strip() for p in sel_str.split(',')]
    out = []
    for p in parts:
        if not p:
            continue
        # html, body 선택자 → 외부 셸이 관리하므로 제거
        p2 = re.sub(r'^\s*html\s*$', '', p).strip()
        p2 = re.sub(r'^\s*body\s*$', '', p2).strip()
        # "html, body" 조합도 제거
        if not p2 or p2 in ('html', 'body', 'html body'):
            continue
        # :root → .sid 로 교체
        p2 = re.sub(r':root\b', f'.{sid}', p2)
        # 이미 .sid 로 시작하면 그대로
        if p2.startswith(f'.{sid}'):
            out.append(p2)
        else:
            out.append(f'.{sid} {p2}')
    return ', '.join(out) if out else None


def scope_css_block(css, sid):
    """
    CSS 문자열을 파싱하여 선택자에 .sid를 붙여 반환.
    @keyframes 이름 충돌 방지, @media 재귀 처리.
    """
    # 1) @import 제거 (외부 셸의 <style>에 1회 선언)
    css = re.sub(r'@import\s+url\([^)]+\)\s*;?', '', css)

    # 2) @keyframes 이름 변경 + animation 참조 갱신
    kf_names = re.findall(r'@keyframes\s+([\w-]+)', css)
    for name in kf_names:
        css = re.sub(
            rf'@keyframes\s+{re.escape(name)}\b',
            f'@keyframes {sid}-{name}', css)
        css = re.sub(
            rf'(animation(?:-name)?)\s*:\s*{re.escape(name)}\b',
            rf'\1: {sid}-{name}', css)

    # 3) 선택자 스코핑 — 문자 단위 파서
    out = []
    i, n = 0, len(css)

    while i < n:
        # 공백
        if css[i].isspace():
            out.append(css[i]); i += 1; continue

        # 주석
        if css[i:i+2] == '/*':
            end = css.find('*/', i+2)
            end = end + 2 if end != -1 else n
            out.append(css[i:end]); i = end; continue

        # @-규칙
        if css[i] == '@':
            j = i + 1
            while j < n and css[j] not in '{;':
                j += 1
            at_hdr = css[i:j].strip()

            if j >= n or css[j] == ';':               # @import, @charset 등
                out.append(css[i:j+1] if j < n else css[i:])
                i = j + 1 if j < n else n
                continue

            # { 블록 — 깊이 추적
            depth, k = 1, j + 1
            while k < n and depth:
                if css[k] == '{': depth += 1
                elif css[k] == '}': depth -= 1
                k += 1
            inner = css[j+1:k-1]

            if 'keyframes' in at_hdr:
                out.append(f'{at_hdr} {{{inner}}}')
            elif 'media' in at_hdr or 'supports' in at_hdr:
                out.append(f'{at_hdr} {{{scope_css_block(inner, sid)}}}')
            else:
                out.append(f'{at_hdr} {{{inner}}}')   # @font-face 등 유지
            i = k
            continue

        # 일반 규칙: 선택자 { 속성 }
        j = i
        while j < n and css[j] != '{':
            if css[j:j+2] == '/*':                    # 선택자 안 주석 건너뜀
                end = css.find('*/', j+2)
                j = (end + 2) if end != -1 else n
            else:
                j += 1

        if j >= n:
            out.append(css[i:]); break

        sel_raw = css[i:j].strip()

        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == '{': depth += 1
            elif css[k] == '}': depth -= 1
            k += 1
        props = css[j+1:k-1]

        if sel_raw:
            scoped = scope_selector(sel_raw, sid)
            if scoped:
                out.append(f'{scoped} {{{props}}}')
        i = k

    return ''.join(out)

# ────────────────────────────────────────────────────────────────────────────
# 슬라이드 처리 준비
# ────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────
# 슬라이드 처리
# ────────────────────────────────────────────────────────────────────────────
all_styles = []
all_sections = []

for idx, name in enumerate(slide_names, 1):
    sid  = f's{idx:02d}'
    path = os.path.join(SLIDE_DIR, name)

    with open(path, encoding='utf-8') as f:
        raw = f.read()

    raw = fix_assets(raw)

    # <style> 추출 및 스코핑
    style_m = re.search(r'<style>(.*?)</style>', raw, re.DOTALL)
    css_raw = style_m.group(1) if style_m else ''
    scoped  = scope_css_block(css_raw, sid)
    all_styles.append(f'/* ══ 슬라이드 {idx:02d}: {name} ══ */\n{scoped}')

    # <body> 내용 추출
    body_m = re.search(r'<body[^>]*>(.*?)</body>', raw, re.DOTALL)
    body   = body_m.group(1).strip() if body_m else ''

    active = ' active' if idx == 1 else ''
    section = (
        f'  <!-- ══ 슬라이드 {idx:02d}: {name} ══ -->\n'
        f'  <section class="slide-page {sid}{active}" id="page-{idx:02d}">\n'
        f'{body}\n'
        f'  </section>'
    )
    all_sections.append(section)
    print(f'  [{idx:02d}] {name}')

N = len(all_sections)

# ────────────────────────────────────────────────────────────────────────────
# 최종 HTML 조립
# ────────────────────────────────────────────────────────────────────────────
COMBINED_CSS = '\n\n'.join(all_styles)
COMBINED_HTML = '\n\n'.join(all_sections)

output_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>고용노동부 AX 전략 발표 | 국가인공지능전략위원회</title>
  <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    /* ── 발표 셸 ─────────────────────────────────────────────── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      width: 100%; height: 100%;
      background: #000;
      overflow: hidden;
      font-family: 'Pretendard', 'Malgun Gothic', '맑은 고딕', sans-serif;
    }}
    .slide-page {{
      display: none;
      position: absolute; top: 0; left: 0;
      width: 100%; height: 100%;
    }}
    .slide-page.active {{ display: block; }}

    /* 내비게이션 */
    #nav {{
      position: fixed; bottom: 22px; left: 50%; transform: translateX(-50%);
      z-index: 99999;
      display: flex; align-items: center; gap: 14px;
      background: rgba(5,10,22,0.70);
      border: 1px solid rgba(56,189,248,0.20);
      border-radius: 40px; padding: 8px 22px;
      backdrop-filter: blur(10px);
      opacity: 0; transition: opacity 0.25s;
      pointer-events: none;
    }}
    body:hover #nav {{ opacity: 1; pointer-events: auto; }}
    #nav button {{
      background: none; border: 1px solid rgba(56,189,248,0.30);
      color: #7dd3fc; border-radius: 50%;
      width: 30px; height: 30px; font-size: 13px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
    }}
    #nav button:hover {{ background: rgba(56,189,248,0.15); }}
    #ctr {{
      color: #94a3b8; font-size: 13px;
      letter-spacing: 0.14em; min-width: 52px; text-align: center;
    }}
    #progress {{
      position: fixed; bottom: 0; left: 0; height: 3px;
      background: linear-gradient(90deg, #38bdf8, #60a5fa);
      transition: width 0.25s; z-index: 99999; pointer-events: none;
    }}

    /* ── 슬라이드별 스코프 CSS ──────────────────────────────── */

{COMBINED_CSS}

  </style>
</head>
<body>

{COMBINED_HTML}

  <!-- 내비게이션 -->
  <div id="nav">
    <button id="btn-prev" title="이전 슬라이드 (←)">&#9664;</button>
    <span id="ctr">1 / {N}</span>
    <button id="btn-next" title="다음 슬라이드 (→)">&#9654;</button>
  </div>
  <div id="progress"></div>

  <script>
    var pages = document.querySelectorAll('.slide-page');
    var N = pages.length;
    var cur = 0;

    function show(n) {{
      n = Math.max(0, Math.min(N - 1, n));
      pages[cur].classList.remove('active');
      cur = n;
      pages[cur].classList.add('active');
      document.getElementById('ctr').textContent = (cur + 1) + ' / ' + N;
      document.getElementById('progress').style.width = ((cur + 1) / N * 100).toFixed(1) + '%';
    }}

    document.getElementById('btn-prev').onclick = function() {{ show(cur - 1); }};
    document.getElementById('btn-next').onclick = function() {{ show(cur + 1); }};

    document.addEventListener('keydown', function(e) {{
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {{
        e.preventDefault(); show(cur + 1);
      }}
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
        e.preventDefault(); show(cur - 1);
      }}
      if (e.key === 'Home') show(0);
      if (e.key === 'End')  show(N - 1);
    }});

    show(0);
  </script>

</body>
</html>"""

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(output_html)

mb = os.path.getsize(OUTPUT) / 1024 / 1024
print(f'\n완료! → {OUTPUT}')
print(f'파일 크기: {mb:.1f} MB  |  슬라이드: {N}개')
