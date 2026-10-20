"""Inspect municipality/zone files directly inside user-provided TSE ZIPs."""
import collections
import csv
import io
import json
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
report = {}
for stem in ('detalhe_votacao_munzona_2026', 'votacao_candidato_munzona_2026', 'votacao_partido_munzona_2026'):
    groups = {}
    with zipfile.ZipFile(ROOT / (stem + '.zip')) as archive:
        for member in (stem + '_RJ.csv', stem + '_BR.csv'):
            with archive.open(member) as raw:
                for row in csv.DictReader(io.TextIOWrapper(raw, encoding='latin1'), delimiter=';'):
                    if row['SG_UF'] != 'RJ':
                        continue
                    key = '|'.join(row[k] for k in ('ANO_ELEICAO', 'NR_TURNO', 'CD_ELEICAO', 'CD_CARGO', 'DS_CARGO'))
                    g = groups.setdefault(key, {'rows': 0, 'municipalities': set(), 'zones': set(), 'generated': set(), 'transit': set(), 'totals': collections.Counter()})
                    g['rows'] += 1
                    g['municipalities'].add(row['CD_MUNICIPIO'])
                    g['zones'].add(row['NR_ZONA'])
                    g['generated'].add(row['DT_GERACAO'])
                    g['transit'].add(row.get('ST_VOTO_EM_TRANSITO'))
                    for field in ('QT_VOTOS_NOMINAIS_VALIDOS', 'QT_TOTAL_VOTOS_VALIDOS', 'QT_TOTAL_VOTOS_LEG_VALIDOS', 'QT_VOTOS_NOMINAIS', 'QT_COMPARECIMENTO', 'QT_APTOS'):
                        if field in row:
                            g['totals'][field] += int(row[field])
    for g in groups.values():
        for field in ('municipalities', 'zones'):
            g[field] = len(g[field])
        for field in ('generated', 'transit'):
            g[field] = sorted(g[field], key=str)
    report[stem] = groups
destination = ROOT / 'data/validation/tse-rj-inventory.json'
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=True, indent=2))
