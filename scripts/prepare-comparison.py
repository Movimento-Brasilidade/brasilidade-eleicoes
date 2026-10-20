"""Prepare the capital-only comparison from official candidate/zone results."""
import csv, io, json, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
votes=Counter(); present=set(); identities=set(); metadata=None
source=ROOT/'data/raw/tse-2024/votacao_candidato_munzona_2024.zip'
with zipfile.ZipFile(source) as z:
    name=next(n for n in z.namelist() if n.endswith('_RJ.csv'))
    for r in csv.DictReader(io.TextIOWrapper(z.open(name),encoding='latin1'),delimiter=';'):
        if (r['CD_ELEICAO'],r['NR_TURNO'],r['CD_CARGO'],r['CD_MUNICIPIO'],r['NR_CANDIDATO'],r['SG_PARTIDO'])!=('619','1','13','60011','12345','PDT'): continue
        identities.add(r['SQ_CANDIDATO']); present.add(r['NR_ZONA'])
        votes[r['NR_ZONA']]+=int(r['QT_VOTOS_NOMINAIS_VALIDOS'])
        metadata={k:r[k] for k in ('SQ_CANDIDATO','NM_URNA_CANDIDATO','CD_ELEICAO','DT_GERACAO')}
assert identities=={'190002169885'}
leo=json.loads((ROOT/'data/processed/leo-lupi-2026-rj-zones.json').read_text(encoding='utf8'))
capital=[r for r in leo['zones'] if r['capital']]
a_total=sum(r['candidate_valid_votes'] for r in capital);b_total=sum(votes.values())
assert a_total==13195 and sum(r['candidate_valid_votes'] for r in leo['zones'])==23105
assert b_total==4220 # Independently checked against TSE municipal totalization report.
rows=[]
for zone in sorted({r['zone'] for r in capital}|present,key=int):
    a=next((r['candidate_valid_votes'] for r in capital if r['zone']==zone),None)
    b=votes[zone] if zone in present else None
    ap=100*a/a_total if a is not None and a_total else None
    bp=100*b/b_total if b is not None and b_total else None
    rows.append(dict(id='RJ-'+zone,zone=zone,leo_votes=a,pedro_votes=b,leo_distribution=ap,pedro_distribution=bp,difference_votes=a-b if a is not None and b is not None else None,difference_pp=ap-bp if ap is not None and bp is not None else None,leo_candidate_id='6259:190002541800',pedro_candidate_id='619:190002169885',territory='Rio de Janeiro/RJ',territorial_continuity='not_confirmed',status='exploratory' if a is not None and b is not None else 'missing_data'))
payload=dict(candidates=[dict(id='6259:190002541800',name='Léo Lupi',year=2026,office='Deputado estadual',number='12345',party='PDT',total=a_total),dict(id='619:190002169885',name='Pedro Porto',year=2024,office='Vereador',number='12345',party='PDT',total=b_total)],rows=rows,metadata=dict(obtained_at=datetime.now(timezone.utc).isoformat(),source='https://dadosabertos.tse.jus.br/dataset/resultados-2024',candidate=metadata,capital_zone_count=len(capital),pedro_zone_count=len(present),only_2024=sorted(present-{r['zone'] for r in capital}),only_2026=sorted({r['zone'] for r in capital}-present),territorial_status='Exploratório: correspondência administrativa por UF, município e zona; continuidade dos limites entre 2024 e 2026 não confirmada. Malha de 2018.',history_source='https://www.tre-rj.jus.br/institucional/memoria/evolucao-das-zonas-eleitorais-resumo'))
(ROOT/'data/processed/capital-comparison.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
with (ROOT/'data/processed/capital-comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(json.dumps(dict(leo=a_total,pedro=b_total,zones=len(rows),only_2024=payload['metadata']['only_2024'],only_2026=payload['metadata']['only_2026'])))
