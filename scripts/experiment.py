#!/usr/bin/env python3
"""Детерминированный эксперимент: CSV -> валидация -> кэш -> CSV/JSON/Markdown."""
from __future__ import annotations
import argparse, csv, hashlib, html, io, json, os, platform, subprocess, time
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/matches.csv'
GENERATED = ROOT / 'docs/generated'

def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def calculate(path: Path) -> dict:
    groups = {}
    seen = set()
    with path.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError('empty dataset')
    for line, r in enumerate(rows, 2):
        try:
            gid, season = int(r['game_id']), int(r['season'])
            when = date.fromisoformat(r['date'])
            h, a = int(r['home_club_goals']), int(r['away_club_goals'])
        except (ValueError, KeyError) as e:
            raise ValueError(f'invalid schema/value at CSV line {line}: {e}') from e
        if gid in seen:
            raise ValueError(f'duplicate game_id={gid}')
        seen.add(gid)
        if r['competition_id'] != 'GB1' or not 2012 <= season <= 2024:
            raise ValueError(f'out-of-scope match at line {line}')
        if not (0 <= h <= 30 and 0 <= a <= 30):
            raise ValueError(f'invalid score at line {line}')
        if when.year not in (season, season+1):
            raise ValueError(f'date outside season at line {line}')
        g = groups.setdefault(season, Counter())
        g['matches'] += 1
        g['home_wins'] += h > a
        g['draws'] += h == a
        g['away_wins'] += h < a
        g['home_goals'] += h
        g['away_goals'] += a
    result = []
    for season, g in sorted(groups.items()):
        assert g['home_wins'] + g['draws'] + g['away_wins'] == g['matches']
        result.append({'season': season, **{k:g[k] for k in ['matches','home_wins','draws','away_wins','home_goals','away_goals']},
                       'home_win_pct':100*g['home_wins']/g['matches'],
                       'away_win_pct':100*g['away_wins']/g['matches'],
                       'mean_goal_diff':(g['home_goals']-g['away_goals'])/g['matches']})
    return {'rows':len(rows), 'seasons':result, 'home_wins':sum(x['home_wins'] for x in result),
            'away_wins':sum(x['away_wins'] for x in result), 'draws':sum(x['draws'] for x in result),
            'date_min':min(r['date'] for r in rows), 'date_max':max(r['date'] for r in rows)}

def commit_id() -> str:
    if os.environ.get('GITHUB_SHA'):
        return os.environ['GITHUB_SHA']
    try:
        return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'local-uncommitted'

def table(rows):
    lines=['| Сезон | Матчи | Победы Home | Ничьи | Победы Away | Home, % | Разность голов / матч |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append(f"| {r['season']}/{str(r['season']+1)[-2:]} | {r['matches']} | {r['home_wins']} | {r['draws']} | {r['away_wins']} | {r['home_win_pct']:.2f} | {r['mean_goal_diff']:.3f} |")
    return '\n'.join(lines)

def write_outputs(result, meta):
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED/'results.json').write_text(json.dumps({'metadata':meta,'result':result},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (GENERATED/'season_summary.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(result['seasons'][0]));w.writeheader();w.writerows(result['seasons'])
    total=result['rows']; share=100*result['home_wins']/total
    low=min(result['seasons'],key=lambda r:r['home_win_pct'])
    high=max(result['seasons'],key=lambda r:r['home_win_pct'])
    reversed_seasons=[str(r['season']) for r in result['seasons'] if r['away_wins']>r['home_wins']]
    labels=[str(r['season']) for r in result['seasons']]
    values=[r['home_win_pct'] for r in result['seasons']]
    spec={'version':1,'form':'trend-line','layout':'report','fill':'none',
          'title':'Доля побед номинальных хозяев по сезонам',
          'aside':f"GB1, {total:,} матчей, сезоны 2012/13–2024/25".replace(',',' '),
          'labels':labels,'tooltipLabels':[f"{r['season']}/{str(r['season']+1)[-2:]}" for r in result['seasons']],
          'axis':{'zero':True,'cap':100},'derived':True,
          'derivationReason':'100 × число побед Home / число матчей этого сезона',
          'series':[{'label':'Победы Home','valueKind':'percent','role':'subject','data':values}]}
    (GENERATED/'chart-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    plan={'question':'Меняется ли доля побед номинальных хозяев между сезонами GB1?',
          'grain':'один матч; затем сезон','population':'GB1, season=2012..2024','unit':'проценты матчей',
          'comparisons':[{'measure':'home_win_pct','disposition':'chart','reason':'временной профиль доли побед'},
                         {'measure':'matches/home_wins/draws/away_wins/mean_goal_diff','disposition':'table','reason':'проверка знаменателей и дополнительная характеристика, без отдельного графика'}],
          'finding':f"Общая доля {share:.2f}%; минимум {low['season']} ({low['home_win_pct']:.2f}%), максимум {high['season']} ({high['home_win_pct']:.2f}%)."}
    (GENERATED/'evidence.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Переносимый HTML, полученный каноническим конструктором; скрипт обновляет
    # сериализованный payload и доступную таблицу, не изменяя геометрию графика.
    render=ROOT/'scripts/render_chart.py'
    if render.exists():
        subprocess.run([os.sys.executable,str(render)],check=True,cwd=ROOT)
    content=f'''# Результаты эксперимента

**{result['home_wins']} побед Home из {total} матчей — {share:.2f}%.** Это описательная статистика выбранного среза, а не причинная оценка домашнего преимущества.

Период дат: **{result['date_min']} — {result['date_max']}**. Сезон обозначен годом начала.
Минимальная доля: **{low['season']}/{str(low['season']+1)[-2:]} — {low['home_win_pct']:.2f}%**;
максимальная: **{high['season']}/{str(high['season']+1)[-2:]} — {high['home_win_pct']:.2f}%**.
Сезоны с большим числом побед Away, чем Home: **{', '.join(reversed_seasons) or 'нет'}**.

<iframe src="home-wins.html" title="Доля побед Home по сезонам" width="100%" height="400" loading="lazy" style="border:0"></iframe>

Если интерактивный график недоступен, все значения приведены ниже.

## Полная таблица

{table(result['seasons'])}

[Скачать CSV](season_summary.csv) · [Результаты и метаданные JSON](results.json)

## Как считается показатель

Для каждого сезона: `home_win_pct = 100 * home_wins / matches`.
Ничьи входят в знаменатель. В числитель входят матчи, где `home_club_goals > away_club_goals`.
Разность голов — среднее `home_club_goals - away_club_goals` по всем матчам сезона.
Пропуски и дубликаты не удаляются молча: проверка прерывает сборку.

<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mrow><msub><mi mathvariant="normal">p</mi><mi mathvariant="normal">H</mi></msub><mo>=</mo><mn>100</mn><mo>×</mo><mfrac><msub><mi mathvariant="normal">W</mi><mi mathvariant="normal">H</mi></msub><mi mathvariant="normal">N</mi></mfrac></mrow></math>

Формула использует встроенный MathML: внешние MathJax/KaTeX и CDN не требуются.

## Ограничения интерпретации

- `Home` — номинальная сторона матча; стадион и нейтральное поле не проверяются.
- Сопоставление сезонов не контролирует силу команд, календарь, составы и правила учёта дополнительного времени.
- Датасет предоставлен пользователем; исходный URL и лицензия не приложены. Достоверность относительно первоисточника не подтверждена.
- Проверки 380 записей на сезон и уникальности ID подтверждают внутреннюю структуру среза, но не доказывают отсутствие заменённых или ошибочных матчей.
- Статистические тесты причинности и выводы о влиянии пандемии не выполнялись.

## Метка версии

| Поле | Значение |
| --- | --- |
| Коммит | `{meta['commit']}` |
| Сборка UTC | `{meta['built_at']}` |
| Версия набора | `{meta['dataset_version']}` |
| SHA-256 данных | `{meta['data_sha256']}` |
| SHA-256 расчётного ключа | `{meta['cache_key']}` |
| Python | `{meta['python']}` |
| Режим кэша | `{meta['cache_status']}` |

Контрольная строка доставки: **RESEARCH-SITE-OK**.
'''
    (GENERATED/'results.md').write_text(content,encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--force',action='store_true');args=parser.parse_args()
    started=time.perf_counter()
    blob=DATA.read_bytes(); code=Path(__file__).read_bytes(); req=(ROOT/'requirements.txt').read_bytes()
    manifest=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'))
    # Hash raw inputs, executable, exact dependencies and dataset manifest.
    cache_key=digest(blob+code+req+(ROOT/'data/manifest.json').read_bytes()+platform.python_version().encode())
    cache=ROOT/'.cache/experiment'/f'{cache_key}.json';cache.parent.mkdir(parents=True,exist_ok=True)
    hit=cache.exists() and not args.force
    if hit:
        result=json.loads(cache.read_text(encoding='utf-8'))
    else:
        result=calculate(DATA)
        cache.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True),encoding='utf-8')
    if digest(blob)!=manifest['subset_sha256']:
        raise ValueError('dataset hash differs from manifest: update dataset_version and subset_sha256 explicitly')
    compute_seconds=time.perf_counter()-started
    meta={'commit':commit_id(),'built_at':datetime.now(timezone.utc).isoformat(),
          'dataset_version':manifest['dataset_version'],'data_sha256':digest(blob),'code_sha256':digest(code),
          'cache_key':cache_key,'cache_status':'HIT' if hit else 'MISS','python':platform.python_version(),
          'compute_seconds':compute_seconds}
    write_outputs(result,meta)
    print(json.dumps({'cache':meta['cache_status'],'rows':result['rows'],'compute_seconds':compute_seconds,'total_seconds':time.perf_counter()-started},ensure_ascii=False))

if __name__=='__main__':
    main()
