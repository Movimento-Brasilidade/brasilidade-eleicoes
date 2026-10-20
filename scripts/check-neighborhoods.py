"""Validate exported spatial relationships and unchanged vote totals."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/processed/capital-neighborhood-crosswalk.json').read_text(encoding='utf8'))
neighborhoods={n['code']:n for n in data['neighborhoods']}
relations=data['relations']
zones=json.loads((ROOT/'data/processed/leo-lupi-2026-rj-zones.json').read_text(encoding='utf8'))['zones']
capital={z['id'] for z in zones if z['capital']}
assert len(neighborhoods)==data['metadata']['source']['count']
assert len({(r['neighborhood_code'],r['zone_id']) for r in relations})==len(relations)
for r in relations:
    assert r['zone_id'] in capital and r['neighborhood_code'] in neighborhoods
    assert r['intersection_area_m2']>0
    pct=100*r['intersection_area_m2']/r['neighborhood_area_m2']
    assert abs(pct-r['neighborhood_area_percent'])<1e-9
    assert r['classification']==('integral' if pct>=99.9 else 'parcial')
    assert r['residual']==(pct<.1)
for n in neighborhoods.values():
    hits=[r for r in relations if r['neighborhood_code']==n['code']]
    assert len(hits)==n['zone_count']
    assert abs(sum(r['neighborhood_area_percent'] for r in hits)-n['area_percent_sum'])<1e-8
    covered=n['area_m2']*n['covered_percent']/100
    assert abs(covered+n['uncovered_area_m2']-n['area_m2'])<.01
    assert abs(sum(r['intersection_area_m2'] for r in hits)-covered-n['overlap_area_m2'])<.01
assert any(r['classification']=='integral' for r in relations)
assert any(n['zone_count']>1 for n in neighborhoods.values())
assert any(r['residual'] for r in relations)
assert any(n['covered_percent']<90 for n in neighborhoods.values())
assert sum(z['candidate_valid_votes'] for z in zones)==23105
assert sum(z['candidate_valid_votes'] for z in zones if z['capital'])==13195
with (ROOT/'map/capital-neighborhood-crosswalk.csv').open(encoding='utf-8-sig') as f:
    assert len(list(csv.DictReader(f)))==len(relations)
print(f'PASS: {len(neighborhoods)} bairros; {len(relations)} relações; percentuais, tolerâncias, lacunas, sobreposições e votos conferidos.')
