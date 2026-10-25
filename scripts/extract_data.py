"""Повторное извлечение минимального среза из пользовательского ZIP; stdlib only."""
import argparse,csv,hashlib,io,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    a=argparse.ArgumentParser();a.add_argument('archive',type=Path);args=a.parse_args()
    archive=args.archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        # Нет extractall: архив не может перезаписать файлы проекта.
        source=z.read('games.csv')
        inventory=[{'file':x.filename,'bytes':x.file_size} for x in z.infolist()]
    selected=[];fields=['game_id','competition_id','season','date','home_club_goals','away_club_goals']
    for row in csv.DictReader(io.StringIO(source.decode('utf-8-sig'))):
        if row['competition_id']=='GB1' and 2012<=int(row['season'])<=2024:
            selected.append({k:row[k] for k in fields})
    selected.sort(key=lambda r:(int(r['season']),r['date'],int(r['game_id'])))
    target=ROOT/'data/matches.csv'
    with target.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(selected)
    manifest={'dataset_version':'football-gb1-2012-2024-v1',
              'source':'User attachment archive.zip; original publisher and redistribution license not supplied',
              'original_archive_sha256':sha(archive),'original_games_sha256':sha(source),
              'subset_sha256':sha(target.read_bytes()),
              'selection':'competition_id = GB1; 2012 <= season <= 2024; 6 columns; sorted by season,date,game_id',
              'rows':len(selected),'original_files':inventory,
              'license':'UNKNOWN: third-party data not relicensed under MIT or CC BY. Confirm source and terms before wider redistribution.'}
    (ROOT/'data/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'extracted {len(selected)} matches; sha256={manifest["subset_sha256"]}')
if __name__=='__main__':main()
