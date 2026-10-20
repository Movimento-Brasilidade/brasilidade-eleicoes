"""Regression checks for the prepared comparison and diverging color scale."""
import csv,json,math,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/processed/capital-comparison.json').read_text(encoding='utf8'))
rows=d['rows'];assert len(rows)==49 and len({r['id'] for r in rows})==49
assert sum(r['leo_votes'] for r in rows)==13195
assert sum(r['pedro_votes'] for r in rows)==4220
for r in rows:
    assert math.isclose(r['difference_pp'],100*r['leo_votes']/13195-100*r['pedro_votes']/4220,abs_tol=1e-12)
    assert r['difference_votes']==r['leo_votes']-r['pedro_votes']
for key in ['leo_distribution','pedro_distribution']:assert math.isclose(sum(r[key] for r in rows),100)
assert any(r['difference_pp']<0 for r in rows) and any(r['difference_pp']>0 for r in rows)
assert any(r['difference_votes']>0 and r['difference_pp']<0 for r in rows)
with (ROOT/'data/processed/capital-comparison.csv').open(encoding='utf-8-sig') as f:assert len(list(csv.DictReader(f)))==49
js=(ROOT/'map/comparison.js').read_text(encoding='utf8')
color=js[js.index('function comparisonColor'):js.index('const individualNote')]
checks="""
const assert=require('node:assert/strict');
assert.equal(comparisonColor(null,5),'#c9cecb');
assert.equal(comparisonColor(0,5),'rgb(245,245,245)');
assert.equal(comparisonColor(0,0),'rgb(245,245,245)');
assert.equal(comparisonColor(-5,5),'rgb(211,112,30)');
assert.equal(comparisonColor(5,5),'rgb(34,105,170)');
"""
subprocess.run(['node','-e',color+checks],check=True)
html=(ROOT/'index.html').read_text(encoding='utf8')
assert html==(ROOT/'map/index.html').read_text(encoding='utf8')
assert '__COMPARISON_SCRIPT__' not in html
subprocess.run(['node','--check'],input=html.split('<script>',1)[1].split('</script>',1)[0],text=True,encoding='utf8',check=True)
print('PASS: totals, distributions, sign differences, CSV, neutral/missing/extreme colors, syntax, Pages parity')
