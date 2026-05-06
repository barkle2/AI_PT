import csv, json, collections, re

with open('C:/Workspace/AI_PT/자료/2601_2604.csv', encoding='cp949') as f:
    rows = list(csv.DictReader(f))

# 마지막 user 메시지만 추출
keywords = ['급여','퇴사','임금','연차','퇴직금','근로계약','주휴수당','휴일','실업급여','해고',
            '근로시간','휴가','사직','육아','체불','최저임금','포괄임금','부당해고','계약직','아르바이트']
kw_cnt = collections.Counter()
parsed = 0
failed = 0

for r in rows:
    try:
        msgs = json.loads(r['request_message'])
        # 마지막 user role 메시지 추출
        last_user = ''
        for m in reversed(msgs):
            if isinstance(m, dict) and m.get('role') == 'user':
                last_user = m.get('content', '')
                break
        for kw in keywords:
            if kw in last_user:
                kw_cnt[kw] += 1
        parsed += 1
    except:
        failed += 1

print(f"파싱 성공: {parsed}, 실패: {failed}")
print("\n키워드 순위 (마지막 user 메시지 기준):")
for kw, cnt in kw_cnt.most_common(15):
    print(f"  {kw}: {cnt}")
