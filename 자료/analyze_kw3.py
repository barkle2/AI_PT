import csv, json, collections, sys

with open('C:/Workspace/AI_PT/자료/2601_2604.csv', encoding='cp949') as f:
    rows = list(csv.DictReader(f))

keywords = ['급여','퇴사','임금','연차','퇴직금','근로계약','주휴수당','휴일','실업급여','해고',
            '근로시간','휴가','사직','육아','체불','최저임금','포괄임금','부당해고','계약직','아르바이트']

kw_cnt = collections.Counter()
for r in rows:
    try:
        msgs = json.loads(r['request_message'])
        last_user = ''
        for m in reversed(msgs):
            if isinstance(m, dict) and m.get('role') == 'user':
                last_user = m.get('content', '')
                break
        for kw in keywords:
            if kw in last_user:
                kw_cnt[kw] += 1
    except:
        pass

with open('C:/Workspace/AI_PT/자료/kw_result.txt', 'w', encoding='utf-8') as out:
    out.write("Top 15 keywords:\n")
    for kw, cnt in kw_cnt.most_common(15):
        out.write(f"  {kw}: {cnt}\n")
print("Done - check kw_result.txt")
