from pathlib import Path
from PyPDF2 import PdfMerger
from playwright.sync_api import sync_playwright

base = Path(r'D:\Workspace\AI_PT\자료\발표용_v2')
slides = [
    base / '01_표지.html',
    base / '02_필요성.html',
    base / '03_데이터맵.html',
    base / '04_고용노동부_메타데이터.html',
    base / '05_고용노동_AX_공통기반_플랫폼.html',
    base / '06_AI_노동법_상담_고도화.html',
    base / '07_지식서재_구축_추진.html',
    base / '08_행정업무_효율화_산업안전.html',
    base / '09_노동법_자율점검_AI.html',
    base / '10_판례질의회시_검색.html',
    base / '11_감사합니다.html',
]

out_dir = base / 'pdf_export_simple'
out_dir.mkdir(exist_ok=True)

print(f'총 슬라이드: {len(slides)}')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for idx, path in enumerate(slides, 1):
        page = browser.new_page(viewport={'width': 1680, 'height': 945}, device_scale_factor=2)
        page.goto(path.as_uri(), wait_until='domcontentloaded', timeout=6000)
        page.emulate_media(media='print')
        pdf_path = out_dir / f'{idx:02d}.pdf'
        page.pdf(
            path=str(pdf_path),
            format='A4',
            landscape=True,
            print_background=True,
            margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'},
            prefer_css_page_size=False,
        )
        print(f'생성: {pdf_path.name}')
        page.close()
    browser.close()

merger = PdfMerger()
for pdf in sorted(out_dir.glob('*.pdf')):
    merger.append(str(pdf))

final_pdf = base / '고용노동부_AX_발표자료_1_11_화면기준.pdf'
merger.write(str(final_pdf))
merger.close()

print(f'최종 PDF: {final_pdf}')
print(f'크기: {final_pdf.stat().st_size / 1024:.1f} KB')
