import csv, json, collections

with open('C:/Workspace/AI_PT/자료/2601_2604.csv', encoding='cp949') as f:
    rows = list(csv.DictReader(f))

# keyword -> romanized mapping to avoid encoding issues
keywords = {
    '급여':'geubyeo', '퇴사':'toesa', '임금':'imgeum', '연차':'yeoncha',
    '퇴직금':'toejikgeum', '근로계약':'geulloyeayak', '주휴수당':'juhyusudang',
    '휴일':'hyuil', '실업급여':'sileobgeubyeo', '해고':'haego',
    '근로시간':'geullosigan', '휴가':'hyuga', '사직':'sajik',
    '육아':'yuga', '체불':'chebul', '최저임금':'choejeoImgeum',
    '포괄임금':'pogwalimgeum', '부당해고':'budanghaego',
    '계약직':'gyeyakjik', '아르바이트':'areubaitu'
}

kw_cnt = collections.Counter()
for r in rows:
    try:
        msgs = json.loads(r['request_message'])
        last_user = ''
        for m in reversed(msgs):
            if isinstance(m, dict) and m.get('role') == 'user':
                last_user = m.get('content', '')
                break
        for kr, en in keywords.items():
            if kr in last_user:
                kw_cnt[en] += 1
    except:
        pass

# reverse mapping
en_to_kr = {v: k for k, v in keywords.items()}
print("Top 15 keywords (last user message):")
for en, cnt in kw_cnt.most_common(15):
    print(f"  {en_to_kr[en]}: {cnt}")
