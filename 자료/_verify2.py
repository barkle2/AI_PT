import sys, json, re, base64
sys.stdout.reconfigure(encoding='utf-8')
with open('C:/Workspace/AI_PT/자료/발표용/발표.html', encoding='utf-8') as f:
    html = f.read()
m = re.search(r'const SLIDES = (\[.*?\]);', html, re.DOTALL)
slides = json.loads(m.group(1))
print(f'슬라이드 수: {len(slides)}')
for i in [0, -1]:
    s = base64.b64decode(slides[i]).decode('utf-8')
    t = re.search(r'<title>(.*?)</title>', s)
    print(f'  [{1 if i==0 else 18}] {t.group(1) if t else "없음"}')
s6 = base64.b64decode(slides[5]).decode('utf-8')
has_tree = 'src="데이터맵_트리.html' in s6
print(f'슬라이드06 데이터맵_트리 참조: {has_tree}')
img_slides = sum(1 for s in slides if 'data:image' in base64.b64decode(s).decode('utf-8'))
print(f'이미지 인라인 슬라이드: {img_slides}개')
print(f'파일 크기: {len(html)/1024/1024:.1f} MB')
