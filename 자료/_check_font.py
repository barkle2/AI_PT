import urllib.request, re

FONT_CSS_URL = "https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/css,*/*;q=0.1',
    'Referer': 'https://cdn.jsdelivr.net/',
}

req = urllib.request.Request(FONT_CSS_URL, headers=headers)
with urllib.request.urlopen(req, timeout=30) as r:
    css = r.read().decode('utf-8')

print("CSS 길이:", len(css))
print("처음 500자:")
print(css[:500])
print("\n---woff2 URLs---")
for url in re.findall(r"url\(['\"]?([^'\")\s]+\.woff2)['\"]?\)", css):
    print(url)
