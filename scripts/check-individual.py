from pathlib import Path
import ast,json,math,csv
ROOT=Path(__file__).resolve().parents[1]
module=ast.parse((ROOT/'scripts/prepare-pedro.py').read_text(encoding='utf8'))
fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='vote_share')
ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<vote_share>','exec'),ns)
share=ns['vote_share'];assert share(10,100)==10 and share(0,100)==0
assert share(10,0) is None and share(10,None) is None and share(None,100) is None
p=json.loads((ROOT/'data/processed/pedro-porto-2024-capital.json').read_text(encoding='utf8'))
assert len(p['zones'])==49 and sum(r['candidate_valid_votes'] for r in p['zones'])==4220
assert sum(r['office_valid_votes'] for r in p['zones'])==3016873
for r in p['zones']:
 assert r['office_valid_votes']==r['office_nominal_votes']+r['office_party_list_votes']
 assert math.isclose(r['vote_share_percent'],share(r['candidate_valid_votes'],r['office_valid_votes']))
for root in [ROOT,ROOT/'map']:
 with (root/'pedro-porto-2024-capital.csv').open(encoding='utf-8-sig') as f:assert len(list(csv.DictReader(f)))==49
print('PASS: Pedro totals, all 49 denominators/shares, missing/zero denominator, CSV copies')
