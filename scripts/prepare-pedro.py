"""Prepare and reconcile Pedro's individual vote shares, including party-list votes."""
import csv,io,json,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def vote_share(votes, denominator):
 return 100*votes/denominator if votes is not None and denominator is not None and denominator>0 else None
def source(stem):
 with zipfile.ZipFile(ROOT/f'data/raw/tse-2024/{stem}_2024.zip') as z:
  name=next(n for n in z.namelist() if n.endswith('_RJ.csv'))
  for r in csv.DictReader(io.TextIOWrapper(z.open(name),encoding='latin1'),delimiter=';'):
   if (r['CD_ELEICAO'],r['NR_TURNO'],r['CD_CARGO'],r['CD_MUNICIPIO'])==('619','1','13','60011'):yield r
nominal=Counter();legend=Counter();denominators=Counter();party_nominal=Counter();party_legend=Counter()
for r in source('detalhe_votacao_munzona'):
 z=r['NR_ZONA'];denominators[z]+=int(r['QT_TOTAL_VOTOS_VALIDOS']);nominal[z]+=int(r['QT_VOTOS_NOMINAIS_VALIDOS']);legend[z]+=int(r['QT_TOTAL_VOTOS_LEG_VALIDOS'])
for r in source('votacao_partido_munzona'):
 z=r['NR_ZONA'];party_nominal[z]+=int(r['QT_VOTOS_NOMINAIS_VALIDOS']);party_legend[z]+=int(r['QT_TOTAL_VOTOS_LEG_VALIDOS'])
assert nominal==party_nominal and legend==party_legend
comparison=json.loads((ROOT/'data/processed/capital-comparison.json').read_text(encoding='utf8'))
rows=[]
for r in comparison['rows']:
 z=r['zone'];d=denominators.get(z);assert d==nominal[z]+legend[z]
 rows.append(dict(id=r['id'],zone=z,candidate_valid_votes=r['pedro_votes'],office_valid_votes=d,vote_share_percent=vote_share(r['pedro_votes'],d),office_nominal_votes=nominal[z],office_party_list_votes=legend[z],candidate_id='619:190002169885',year=2024,office='Vereador',municipality='Rio de Janeiro'))
assert len(rows)==49 and sum(r['candidate_valid_votes'] for r in rows)==4220
payload=dict(zones=rows,total_votes=4220,office_valid_votes=sum(denominators.values()),source='https://dadosabertos.tse.jus.br/dataset/resultados-2024',validation='Nominais e legenda conferidos por zona entre partidos e detalhamento; inclui legenda.')
(ROOT/'data/processed/pedro-porto-2024-capital.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
with (ROOT/'data/processed/pedro-porto-2024-capital.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('49 zones, 4220 votes;',payload['office_valid_votes'],'valid office votes; reconciled nominal and party-list votes')
