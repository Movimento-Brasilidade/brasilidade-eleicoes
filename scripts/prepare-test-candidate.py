"""Prepare the selected candidate's municipal vote dataset from local TSE files."""
import csv
import io
import json
from collections import Counter
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed'
OUT.mkdir(parents=True, exist_ok=True)
CANDIDATE = '190002541800'

def rows(stem):
    with zipfile.ZipFile(ROOT / (stem + '.zip')) as z:
        with z.open(stem + '_RJ.csv') as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding='latin1'), delimiter=';'):
                if row['ANO_ELEICAO'] == '2026' and row['NR_TURNO'] == '1' and row['CD_ELEICAO'] == '6259' and row['CD_CARGO'] == '7' and row['SG_UF'] == 'RJ':
                    yield row

votes, raw_votes, denominators = Counter(), Counter(), Counter()
metadata, present = None, set()
for r in rows('votacao_candidato_munzona_2026'):
    if r['SQ_CANDIDATO'] != CANDIDATE:
        continue
    assert r['NR_CANDIDATO'] == '12345' and r['SG_PARTIDO'] == 'PDT'
    code = r['CD_MUNICIPIO'].zfill(5)
    present.add(code)
    votes[code] += int(r['QT_VOTOS_NOMINAIS_VALIDOS'])
    raw_votes[code] += int(r['QT_VOTOS_NOMINAIS'])
    metadata = {k:r[k] for k in ('SQ_CANDIDATO','NR_CANDIDATO','NM_CANDIDATO','NM_URNA_CANDIDATO','SG_PARTIDO','DS_CARGO','CD_CARGO','CD_ELEICAO','ANO_ELEICAO','NR_TURNO','DT_GERACAO')}
for r in rows('detalhe_votacao_munzona_2026'):
    denominators[r['CD_MUNICIPIO'].zfill(5)] += int(r['QT_TOTAL_VOTOS_VALIDOS'])
with (ROOT / 'data/validation/municipality-crosswalk.csv').open(encoding='utf-8-sig', newline='') as f:
    crosswalk = list(csv.DictReader(f))
assert metadata and len(present) == 92 and present == set(denominators) == {r['code_tse'] for r in crosswalk}
data = []
for r in crosswalk:
    code = r['code_tse']
    denominator = denominators[code]
    assert denominator > 0 and 0 <= votes[code] <= denominator
    data.append({'code_tse':code, 'code_ibge':r['code_ibge'], 'municipality':r['name_ibge'], 'candidate_valid_votes':votes[code], 'candidate_raw_votes':raw_votes[code], 'office_valid_votes':denominator, 'vote_share_percent':100*votes[code]/denominator})
total = sum(votes.values())
payload = {'candidate':metadata, 'denominator':'Total valid votes for state deputy in each municipality, including party-list votes; excludes blank, null and invalid votes.', 'state_valid_candidate_votes':total, 'state_office_valid_votes':sum(denominators.values()), 'state_vote_share_percent':100*total/sum(denominators.values()), 'municipalities':data, 'limitations':['TSE/IBGE crosswalk inferred by unique normalized municipality names.', 'IBGE boundary vintage 2025.', 'No independent section-level validation.']}
(OUT / 'leo-lupi-2026-rj.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
with (OUT / 'leo-lupi-2026-rj.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(data[0]))
    writer.writeheader()
    writer.writerows(data)
print(json.dumps({'votes':total, 'municipalities':len(data), 'state_percent':payload['state_vote_share_percent'], 'top_by_votes':sorted(data,key=lambda r:r['candidate_valid_votes'],reverse=True)[:5]}, ensure_ascii=True, indent=2))
