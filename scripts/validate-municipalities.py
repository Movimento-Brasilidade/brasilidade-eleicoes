"""Reconcile local TSE snapshots and build an auditable IBGE name crosswalk."""
import collections
import csv
import io
import json
from pathlib import Path
import struct
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/validation'

def normalize(name):
    return ''.join(c for c in unicodedata.normalize('NFKD', name.upper()) if c.isalnum())

def ibge_records():
    with zipfile.ZipFile(ROOT / 'RJ_Municipios_2025.zip') as z:
        data = z.read('RJ_Municipios_2025.dbf')
        encoding = z.read('RJ_Municipios_2025.cpg').decode().strip()
    count, header, length = struct.unpack_from('<IHH', data, 4)
    fields = []
    for offset in range(32, header - 1, 32):
        if data[offset] == 13:
            break
        fields.append((data[offset:offset+11].split(b'\0')[0].decode(), data[offset+16]))
    for index in range(count):
        record = data[header+index*length:header+(index+1)*length]
        if record[0] == 42:
            continue
        offset, values = 1, {}
        for name, width in fields:
            values[name] = record[offset:offset+width].decode(encoding).strip()
            offset += width
        yield values

sources = {
    'detail': 'detalhe_votacao_munzona_2026',
    'candidates': 'votacao_candidato_munzona_2026',
    'parties': 'votacao_partido_munzona_2026',
}
totals, municipality_names, provenance = {}, collections.defaultdict(set), []
fields = ('QT_VOTOS_NOMINAIS_VALIDOS', 'QT_TOTAL_VOTOS_LEG_VALIDOS', 'QT_TOTAL_VOTOS_VALIDOS')
for source, stem in sources.items():
    groups = collections.defaultdict(collections.Counter)
    with zipfile.ZipFile(ROOT / (stem + '.zip')) as archive:
        for suffix in ('RJ', 'BR'):
            member = stem + '_' + suffix + '.csv'
            info = archive.getinfo(member)
            provenance.append({'source': source, 'zip': stem+'.zip', 'member': member, 'crc32': f'{info.CRC:08x}', 'size': info.file_size})
            with archive.open(member) as raw:
                for row in csv.DictReader(io.TextIOWrapper(raw, encoding='latin1'), delimiter=';'):
                    if row['SG_UF'] != 'RJ' or row['ANO_ELEICAO'] != '2026' or row['NR_TURNO'] != '1':
                        continue
                    code = row['CD_MUNICIPIO'].zfill(5)
                    municipality_names[code].add(row['NM_MUNICIPIO'])
                    key = (row['CD_ELEICAO'], row['CD_CARGO'], code)
                    for field in fields:
                        if field in row:
                            groups[key][field] += int(row[field])
    totals[source] = groups
    print(source, len(groups), 'municipality/office groups', flush=True)

ibge = list(ibge_records())
by_name = collections.defaultdict(list)
for row in ibge:
    by_name[normalize(row['NM_MUN'])].append(row)
crosswalk, mapping_issues = [], []
for code, names in sorted(municipality_names.items()):
    matches = {r['CD_MUN']: r for name in names for r in by_name[normalize(name)]}
    if len(matches) != 1:
        mapping_issues.append({'tse': code, 'names': sorted(names), 'matches': list(matches)})
        continue
    match = next(iter(matches.values()))
    crosswalk.append({'code_tse': code, 'code_ibge': match['CD_MUN'], 'name_tse': '|'.join(sorted(names)), 'name_ibge': match['NM_MUN'], 'method': 'unique_normalized_name_within_RJ'})
mapped = [r['code_ibge'] for r in crosswalk]
unmatched_ibge = sorted(set(r['CD_MUN'] for r in ibge) - set(mapped))
duplicate_ibge = [k for k,v in collections.Counter(mapped).items() if v > 1]

checks = []
for key in sorted(set().union(*(set(v) for v in totals.values()))):
    available = all(key in totals[s] for s in sources)
    d, c, p = (totals[s].get(key, {}) for s in sources)
    nominal_match = available and d.get(fields[0]) == c.get(fields[0]) == p.get(fields[0])
    legend_match = available and d.get(fields[1]) == p.get(fields[1])
    valid_match = available and d.get(fields[2]) == c.get(fields[0], 0) + p.get(fields[1], 0)
    checks.append({'election':key[0], 'office':key[1], 'code_tse':key[2], 'nominal_detail':d.get(fields[0]), 'nominal_candidates':c.get(fields[0]), 'nominal_parties':p.get(fields[0]), 'legend_detail':d.get(fields[1]), 'legend_parties':p.get(fields[1]), 'valid_detail':d.get(fields[2]), 'passed':nominal_match and legend_match and valid_match})

for filename, rows in [('municipality-crosswalk.csv', crosswalk), ('municipality-vote-checks.csv', checks)]:
    if rows:
        with (OUT / filename).open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
summary = {'scope':'RJ, 2026, round 1', 'ibge_municipalities':len(ibge), 'tse_municipalities':len(municipality_names), 'matched':len(crosswalk), 'mapping_issues':mapping_issues, 'unmatched_ibge':unmatched_ibge, 'duplicate_ibge':duplicate_ibge, 'groups_checked':len(checks), 'groups_passed':sum(r['passed'] for r in checks), 'failures':[r for r in checks if not r['passed']], 'sources':provenance, 'limits':['Name-based crosswalk inferred from supplied files; not an official TSE/IBGE correspondence table.', 'Municipality aggregate reconciliation only; no section-level or candidate-level independent validation.', 'IBGE geometry vintage 2025; boundary history not audited.']}
(OUT / 'municipality-validation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k != 'sources'}, ensure_ascii=True, indent=2))
if summary['failures'] or mapping_issues or unmatched_ibge or duplicate_ibge:
    raise SystemExit(1)
