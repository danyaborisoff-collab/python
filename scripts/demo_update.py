"""Безопасная локальная демонстрация изменения CSV: оригинал не меняется."""
import csv,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    with tempfile.TemporaryDirectory() as tmp:
        target=Path(tmp)
        for name in ['data','scripts','templates']:
            shutil.copytree(ROOT/name,target/name)
        shutil.copy2(ROOT/'requirements.txt',target/'requirements.txt')
        (target/'docs/generated').mkdir(parents=True)
        def run():
            p=subprocess.run([sys.executable,str(target/'scripts/experiment.py')],capture_output=True,text=True,check=True)
            rec=json.loads((target/'docs/generated/results.json').read_text(encoding='utf-8'))
            return json.loads(p.stdout.splitlines()[-1]),rec,hashlib.sha256((target/'docs/generated/home-wins.html').read_bytes()).hexdigest()
        first,a,chart_a=run()
        rows=list(csv.DictReader((target/'data/matches.csv').open(encoding='utf-8')))
        row=next(r for r in rows if int(r['home_club_goals'])<=int(r['away_club_goals']))
        before=row.copy();row['home_club_goals']=str(int(row['away_club_goals'])+1)
        with (target/'data/matches.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
        manifest=json.loads((target/'data/manifest.json').read_text(encoding='utf-8'))
        manifest['dataset_version']='football-demo-synthetic-score-not-real'
        manifest['subset_sha256']=hashlib.sha256((target/'data/matches.csv').read_bytes()).hexdigest()
        (target/'data/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        changed,b,chart_b=run(); warm,c,_=run()
        assert first['cache']=='MISS' and changed['cache']=='MISS' and warm['cache']=='HIT'
        assert a['metadata']['data_sha256']!=b['metadata']['data_sha256']
        assert b['result']['home_wins']==a['result']['home_wins']+1
        assert chart_a!=chart_b
        record={'scope':'local temporary copy, not a remote push/deploy',
                'changed_match_id':before['game_id'],'before_score':[before['home_club_goals'],before['away_club_goals']],
                'after_score':[row['home_club_goals'],row['away_club_goals']],
                'home_wins_before':a['result']['home_wins'],'home_wins_after':b['result']['home_wins'],
                'hash_before':a['metadata']['data_sha256'],'hash_after':b['metadata']['data_sha256'],
                'graph_changed':chart_a!=chart_b,'run_sequence':[first['cache'],changed['cache'],warm['cache']]}
        (ROOT/'evidence/update-demo.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(record,ensure_ascii=False))
if __name__=='__main__':main()
