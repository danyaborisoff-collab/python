"""Реальные намеренные отказы: не повреждают рабочие файлы проекта."""
import csv,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    records=[]
    with tempfile.TemporaryDirectory() as tmp:
        t=Path(tmp)
        for name in ['data','scripts','templates','docs','overrides']:
            shutil.copytree(ROOT/name,t/name)
        for name in ['requirements.txt','mkdocs.yml']:
            shutil.copy2(ROOT/name,t/name)
        rows=list(csv.DictReader((t/'data/matches.csv').open(encoding='utf-8')))
        def write(data):
            with (t/'data/matches.csv').open('w',encoding='utf-8',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
        def probe(name,cmd):
            p=subprocess.run(cmd,cwd=t,text=True,capture_output=True)
            assert p.returncode!=0, f'{name} unexpectedly passed'
            log=p.stdout+p.stderr
            (ROOT/'evidence'/f'{name}.log').write_text(log,encoding='utf-8')
            errors=[s for s in log.splitlines() if 'ValueError:' in s or 'WARNING' in s or 'Aborted' in s]
            records.append({'name':name,'exit_code':p.returncode,'errors':errors})
        write(rows+[rows[0]])
        probe('duplicate',[sys.executable,'scripts/experiment.py','--force'])
        rows[0]['home_club_goals']='-1';write(rows)
        probe('invalid-score',[sys.executable,'scripts/experiment.py','--force'])
        # Исходные валидные данные возвращаются до теста строгих ссылок.
        shutil.copy2(ROOT/'data/matches.csv',t/'data/matches.csv')
        with (t/'docs/index.md').open('a',encoding='utf-8') as f:f.write('\n[Intentional broken link](missing-page.md)\n')
        probe('strict-broken-link',[sys.executable,'-m','mkdocs','build','--strict'])
    (ROOT/'evidence/negative-checks.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(records,ensure_ascii=False))
if __name__=='__main__':main()
