import csv, collections, re, json
from datetime import datetime, timedelta

with open('C:/Workspace/AI_PT/자료/2601_2604.csv', encoding='cp949') as f:
    rows = list(csv.DictReader(f))

# ── 기본 수치 ──
total_msgs = len(rows)
total_convs = len(set(r['conversation_id'] for r in rows))
all_dates = set(r['created_at'] for r in rows)
total_days = len(all_dates)
print(f"총 메시지: {total_msgs}")
print(f"총 대화: {total_convs}")
print(f"총 일수: {total_days}")
print(f"일평균 메시지: {total_msgs/total_days:.0f}")
print(f"일평균 대화: {total_convs/total_days:.0f}")
print(f"대화당 평균 메시지: {total_msgs/total_convs:.1f}")

# ── 요일별 메시지 (created_at 기준) ──
day_names = ['월','화','수','목','금','토','일']
day_msg = collections.Counter()
for r in rows:
    d = datetime.strptime(r['created_at'], '%Y-%m-%d')
    day_msg[d.weekday()] += 1
print("\n요일별 메시지:")
grand = sum(day_msg.values())
for i, name in enumerate(day_names):
    print(f"  {name}: {day_msg[i]} ({day_msg[i]/grand*100:.1f}%)")

# ── 시간대 분석 (modified_at UTC -> KST) ──
biz, night, wknd = 0, 0, 0
hour_cnt = collections.Counter()
dow_biz = collections.Counter()
dow_night = collections.Counter()

for r in rows:
    try:
        dt_utc = datetime.strptime(r['modified_at'][:19], '%Y/%m/%d %H:%M:%S')
        dt = dt_utc + timedelta(hours=9)
        h = dt.hour
        wd = dt.weekday()
        hour_cnt[h] += 1
        if wd >= 5:
            wknd += 1
        elif 9 <= h < 18:
            biz += 1
            dow_biz[wd] += 1
        else:
            night += 1
            dow_night[wd] += 1
    except:
        pass

total_t = biz + night + wknd
print(f"\n업무시간(평일 9-18): {biz} ({biz/total_t*100:.1f}%)")
print(f"야간(평일 외): {night} ({night/total_t*100:.1f}%)")
print(f"주말: {wknd} ({wknd/total_t*100:.1f}%)")
print(f"비업무시간 합계: {night+wknd} ({(night+wknd)/total_t*100:.1f}%)")

print("\n시간대별(KST):")
for h in range(24):
    print(f"  {h:02d}시: {hour_cnt[h]}")

print("\n요일별 biz/night 비율 (평일):")
for wd in range(5):
    b = dow_biz[wd]
    n = dow_night[wd]
    t2 = b + n
    if t2 > 0:
        print(f"  {day_names[wd]}: biz={b/t2*100:.1f}% night={n/t2*100:.1f}% total={t2}")

# ── 키워드 분석 ──
keywords = ['급여','퇴사','임금','연차','퇴직금','근로계약','주휴수당','휴일','실업급여','해고',
            '근로시간','휴가','사직','육아','체불','최저임금','포괄임금','부당해고','계약직','아르바이트']
kw_cnt = collections.Counter()
for r in rows:
    txt = r['request_message']
    for kw in keywords:
        if kw in txt:
            kw_cnt[kw] += 1
print("\n키워드 상위 15:")
for kw, cnt in kw_cnt.most_common(15):
    print(f"  {kw}: {cnt}")

# ── 답변 길이 분석 ──
resp_lens = [len(r['response_message']) for r in rows]
avg_len = sum(resp_lens) / len(resp_lens)
print(f"\n평균 답변 길이: {avg_len:.0f}자")
ranges = [(0,200),(200,500),(500,1000),(1000,2000),(2000,99999)]
labels = ['~200자','200~500자','500~1000자','1000~2000자','2000자 이상']
for (lo,hi), lab in zip(ranges, labels):
    cnt = sum(1 for l in resp_lens if lo <= l < hi)
    print(f"  {lab}: {cnt} ({cnt/len(resp_lens)*100:.1f}%)")

# ── 대화 깊이 (conversation_id별 메시지 수) ──
conv_depth = collections.Counter()
for r in rows:
    conv_depth[r['conversation_id']] += 1
depths = list(conv_depth.values())
print(f"\n대화당 메시지 분포:")
for label, lo, hi in [('1개',1,2),('2개',2,3),('3개',3,4),('4~5개',4,6),('6~10개',6,11),('11개 이상',11,9999)]:
    cnt = sum(1 for d in depths if lo <= d < hi)
    print(f"  {label}: {cnt} ({cnt/len(depths)*100:.1f}%)")
print(f"  평균: {sum(depths)/len(depths):.1f}개")
print(f"  최대: {max(depths)}개")
