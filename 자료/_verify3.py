import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Workspace\AI_PT\자료\발표용\발표.html', encoding='utf-8') as f:
    html = f.read()

# 슬라이드 섹션 수
sections = re.findall(r'<section class="slide-page', html)
print(f'슬라이드 섹션: {len(sections)}개')

# active 슬라이드 확인
active = re.findall(r'class="slide-page ([^"]+) active"', html)
print(f'active 슬라이드: {active}')

# CSS 스코핑 확인 (s01, s18)
s01_rules = re.findall(r'\.s01 \.[a-z]', html)
s18_rules = re.findall(r'\.s18 \.[a-z]', html)
print(f'.s01 규칙 수: {len(s01_rules)}')
print(f'.s18 규칙 수: {len(s18_rules)}')

# keyframes 이름 충돌 확인
kf_names = re.findall(r'@keyframes ([\w-]+)', html)
print(f'@keyframes: {sorted(set(kf_names))}')

# 이미지 인라인 확인
data_imgs = len(re.findall(r'data:image', html))
print(f'data:image 참조 수: {data_imgs}')

# 데이터맵 트리 주입 확인
has_tree = 'data-tree' in html
print(f'데이터맵 트리 주입: {has_tree}')

# 파일 크기
import os
mb = os.path.getsize(r'C:\Workspace\AI_PT\자료\발표용\발표.html') / 1024 / 1024
print(f'파일 크기: {mb:.1f} MB')
