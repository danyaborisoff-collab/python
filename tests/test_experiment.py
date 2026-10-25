import csv,importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('experiment',ROOT/'scripts/experiment.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

class ExperimentTests(unittest.TestCase):
    def test_fixture(self):
        out=e.calculate(ROOT/'data/matches.csv')
        self.assertEqual(out['rows'],4940)
        self.assertEqual(len(out['seasons']),13)
        self.assertTrue(all(s['matches']==380 for s in out['seasons']))
    def test_invalid_score(self):
        self.run_bad('home_club_goals','-1','invalid score')
    def test_invalid_date(self):
        self.run_bad('date','not-a-date','invalid schema/value')
    def run_bad(self,key,value,message):
        rows=list(csv.DictReader((ROOT/'data/matches.csv').open(encoding='utf-8')))
        rows[0][key]=value
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv'
            with p.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
            with self.assertRaisesRegex(ValueError,message):e.calculate(p)
    def test_duplicate(self):
        rows=list(csv.DictReader((ROOT/'data/matches.csv').open(encoding='utf-8')))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'duplicate.csv'
            with p.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows+[rows[0]])
            with self.assertRaisesRegex(ValueError,'duplicate game_id'):e.calculate(p)

if __name__=='__main__':unittest.main()
