"""Обновление данных в каноническом HTML без изменения его стилей/геометрии."""
import html,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    spec=json.loads((ROOT/'docs/generated/chart-spec.json').read_text(encoding='utf-8'))
    text=(ROOT/'templates/home-wins.html').read_text(encoding='utf-8')
    match=re.search(r'const panel = (\{[^\n]+\})',text)
    if not match: raise RuntimeError('canonical chart payload not found')
    panel=json.loads(match[1])
    panel['labels']=spec['tooltipLabels'];panel['tickLabels']=spec['labels']
    panel['series'][0]['data']=spec['series'][0]['data']
    text=text[:match.start(1)]+json.dumps(panel,ensure_ascii=False,separators=(',',':'))+text[match.end(1):]
    table='<table class="sr-only">\n<caption>'+html.escape(spec['title'])+'</caption>\n<tr><th>Observation</th><th>Победы Home</th></tr>\n'
    for label,value in zip(spec['tooltipLabels'],spec['series'][0]['data']):
        table+=f'<tr><td>{html.escape(label)}</td><td data-observation-key="{html.escape(label)}" data-series-key="Победы Home" data-raw-value="{value}" data-value-kind="percent">{value:.2f}%</td></tr>\n'
    table+='</table>'
    text,n=re.subn(r'<table class="sr-only">.*?</table>',lambda _:table,text,count=1,flags=re.S)
    if n!=1: raise RuntimeError('accessible table not found')
    summary='Победы Home: '+ '; '.join(f'{l}: {v:.2f}%' for l,v in zip(spec['tooltipLabels'],spec['series'][0]['data']))
    text=re.sub(r'<p class="sr-only">.*?</p>',lambda _:f'<p class="sr-only">{html.escape(summary)}</p>',text,count=1,flags=re.S)
    text=re.sub(r'(<canvas [^>]*aria-label=")[^"]*("[^>]*>).*?(</canvas>)',lambda m:m[1]+html.escape(spec['title']+'. '+summary,quote=True)+m[2]+html.escape(summary)+m[3],text,count=1,flags=re.S)
    # На сайте библиотека локальная. Исходный шаблон сохраняется неизменным.
    text=text.replace('https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js','../assets/vendor/chart.umd.js')
    text='<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Доля побед Home</title></head><body>'+text+'</body></html>'
    (ROOT/'docs/generated/home-wins.html').write_text(text,encoding='utf-8')

if __name__=='__main__':main()
