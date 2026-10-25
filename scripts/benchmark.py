"""Микробенчмарк: 5 пар MISS/HIT и 5 полных строгих сборок; без искусственной задержки."""
import csv,json,platform,statistics,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def timed(cmd):
    t=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True)
    return time.perf_counter()-t,p.stdout,p.stderr

def main():
    result=[]
    for i in range(1,6):
        for mode in ['MISS','HIT']:
            cmd=[sys.executable,'scripts/experiment.py']+(['--force'] if mode=='MISS' else [])
            wall,stdout,_=timed(cmd);r=json.loads(stdout.splitlines()[-1]);assert r['cache']==mode
            result.append({'run':i,'case':mode,'wall_seconds':wall,'compute_seconds':r['compute_seconds']})
    builds=[]
    for i in range(1,6):
        elapsed,stdout,stderr=timed([sys.executable,'-m','mkdocs','build','--strict'])
        builds.append({'run':i,'wall_seconds':elapsed})
    check=time.perf_counter();subprocess.run([sys.executable,'scripts/check_site.py','site'],cwd=ROOT,check=True)
    files=list((ROOT/'site').rglob('*'));size=sum(p.stat().st_size for p in files if p.is_file())
    with (ROOT/'evidence/benchmark.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    med={mode:statistics.median(r['wall_seconds'] for r in result if r['case']==mode) for mode in ['MISS','HIT']}
    comp={mode:statistics.median(r['compute_seconds'] for r in result if r['case']==mode) for mode in ['MISS','HIT']}
    record={'measured_at':datetime.now(timezone.utc).isoformat(),'environment':platform.platform(),'python':platform.python_version(),
            'scope':'local environment, application cache; no OS cache flush; NOT a GitHub runner benchmark',
            'experiment_runs':result,'medians_wall_seconds':med,'medians_compute_seconds':comp,
            'wall_speedup':med['MISS']/med['HIT'],'compute_speedup':comp['MISS']/comp['HIT'],
            'strict_build_runs':builds,'strict_build_median_seconds':statistics.median(r['wall_seconds'] for r in builds),
            'site_bytes':size,'results_html_bytes':(ROOT/'site/generated/results.html').stat().st_size,
            'figure_html_bytes':(ROOT/'site/generated/home-wins.html').stat().st_size,
            'chart_library_bytes':(ROOT/'site/assets/vendor/chart.umd.js').stat().st_size}
    (ROOT/'evidence/benchmark.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Измерения','',f"Среда: `{record['environment']}`, Python `{record['python']}`. Время UTC: `{record['measured_at']}`.",
           '', '**Это локальные замеры, не результаты GitHub Actions и не время доставки на удалённый сервер.**',
           '', '## Кэш расчётов','', '| Сценарий | Повторы | Медиана полного процесса, с | Медиана чтения/расчёта/кэша, с |',
           '| --- | ---: | ---: | ---: |']
    for mode in ['MISS','HIT']:lines.append(f"| {mode} | 5 | {med[mode]:.6f} | {comp[mode]:.6f} |")
    lines += ['', '| Отношение медиан MISS/HIT | Значение |', '| --- | ---: |',
              f"| Полный процесс | {record['wall_speedup']:.2f}× |",
              f"| Участок чтения/расчёта/кэша | {record['compute_speedup']:.2f}× |", '', 
              'Полный процесс включает запуск Python и запись результатов. Для маленькой таблицы экономия может быть невелика или отсутствовать; искусственного sleep нет.',
              '', 'MISS здесь означает принудительное выполнение расчёта, а не очищенный дисковый кэш ОС. HIT всё равно читает вход для проверки SHA-256.',
              '', '## Сборка и объёмы','', '| Показатель | Значение |','| --- | ---: |',
              f"| Полная mkdocs build --strict, медиана 5 запусков, с | {record['strict_build_median_seconds']:.6f} |",
              f"| Весь каталог site, байт | {size} |",f"| HTML страницы результатов, байт | {record['results_html_bytes']} |",
              f"| HTML графика, байт | {record['figure_html_bytes']} |",f"| Локальная Chart.js, байт | {record['chart_library_bytes']} |",
              ('| Удалённый деплой GitHub Pages | Подтверждён; см. evidence/remote-deployment.json |' if (ROOT/'evidence/remote-deployment.json').exists() else '| Удалённый деплой GitHub Pages | Не выполнен / нет замера |'),
              '| Удалённый деплой отечественный хостинг | Не выполнен / нет замера |',
              '', 'Все пять сборок — полные; это не измерение инкрементального live-reload. Размер — несжатые байты на диске, не трафик с gzip.',
              'JSON и CSV с отдельными повторами лежат в `evidence/benchmark.json` и `evidence/benchmark.csv` репозитория.']
    remote_path=ROOT/'evidence/remote-deployment.json'
    if remote_path.exists():
        remote=json.loads(remote_path.read_text(encoding='utf-8'))
        lines += ['', '## Реальный GitHub Actions запуск', '', f"[Источник времён job]({remote['workflow']}). Один исторический запуск; включает настройку и проверки, не только передачу файлов.", '', '| Job | Длительность, с | Результат |', '| --- | ---: | --- |']
        for job in remote['jobs']:
            elapsed=(datetime.fromisoformat(job['completed_at'].replace('Z','+00:00'))-datetime.fromisoformat(job['started_at'].replace('Z','+00:00'))).total_seconds()
            lines.append(f"| {job['name']} | {elapsed:.0f} | {job['conclusion']} |")
    (ROOT/'docs/generated/measurements.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:record[k] for k in ['medians_wall_seconds','medians_compute_seconds','wall_speedup','strict_build_median_seconds','site_bytes']},ensure_ascii=False))
if __name__=='__main__':main()
