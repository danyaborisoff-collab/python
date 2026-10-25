"""Независимый пересчёт без использования calculate(): другой путь агрегации."""
import csv,hashlib,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((R/'data/matches.csv').open(encoding='utf-8')))
record=json.loads((R/'docs/generated/results.json').read_text(encoding='utf-8'))
out=record['result']
assert hashlib.sha256((R/'data/matches.csv').read_bytes()).hexdigest()==record['metadata']['data_sha256']
assert len(rows)==out['rows']
assert len({r['game_id'] for r in rows})==len(rows)
for s in out['seasons']:
    selected=[r for r in rows if int(r['season'])==s['season']]
    home=sum(1 for r in selected if int(r['home_club_goals'])>int(r['away_club_goals']))
    away=sum(1 for r in selected if int(r['home_club_goals'])<int(r['away_club_goals']))
    draws=sum(1 for r in selected if int(r['home_club_goals'])==int(r['away_club_goals']))
    assert len(selected)==s['matches']==home+away+draws
    assert home==s['home_wins'] and away==s['away_wins'] and draws==s['draws']
    assert math.isclose(home/len(selected)*100,s['home_win_pct'],abs_tol=1e-12)
assert sum(int(r['home_club_goals'])>int(r['away_club_goals']) for r in rows)==out['home_wins']
# Привязка графика к пересчитанной таблице, а не к вручную переписанным числам.
spec=json.loads((R/'docs/generated/chart-spec.json').read_text(encoding='utf-8'))
assert spec['series'][0]['data']==[s['home_win_pct'] for s in out['seasons']]
print(f"PASS independent verification: {out['rows']} matches, {out['home_wins']} home wins")
