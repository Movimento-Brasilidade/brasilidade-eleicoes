"""Aggregate and reconcile the selected candidate by electoral zone."""
import csv, io, json, sys, zipfile, hashlib
from pathlib import Path
from collections import defaultdict, Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.local-python'))
import shapefile
from shapely.geometry import shape, mapping
from shapely import make_valid, union_all

groups={}; names=defaultdict(dict); candidate=Counter(); capital=set()
sources={'detail':'detalhe_votacao_munzona_2026','candidates':'votacao_candidato_munzona_2026','parties':'votacao_partido_munzona_2026'}
for source,stem in sources.items():
    totals=defaultdict(Counter)
    with zipfile.ZipFile(ROOT/(stem+'.zip')) as z:
        with z.open(stem+'_RJ.csv') as f:
            for r in csv.DictReader(io.TextIOWrapper(f,encoding='latin1'),delimiter=';'):
                if (r['ANO_ELEICAO'],r['NR_TURNO'],r['CD_ELEICAO'],r['CD_CARGO'],r['SG_UF'])!=('2026','1','6259','7','RJ'): continue
                zone=str(int(r['NR_ZONA'])); names[zone][r['CD_MUNICIPIO']]=r['NM_MUNICIPIO']
                if r['CD_MUNICIPIO']=='60011': capital.add(zone)
                for field in ('QT_VOTOS_NOMINAIS_VALIDOS','QT_TOTAL_VOTOS_LEG_VALIDOS','QT_TOTAL_VOTOS_VALIDOS'):
                    if field in r: totals[zone][field]+=int(r[field])
                if source=='candidates' and r['SQ_CANDIDATO']=='190002541800': candidate[zone]+=int(r['QT_VOTOS_NOMINAIS_VALIDOS'])
    groups[source]=totals
    print(source,len(totals),flush=True)
checks=[]
for zone in sorted(names,key=int):
    d,c,p=(groups[s].get(zone,{}) for s in sources)
    nominal='QT_VOTOS_NOMINAIS_VALIDOS'; legend='QT_TOTAL_VOTOS_LEG_VALIDOS'; valid='QT_TOTAL_VOTOS_VALIDOS'
    checks.append({'zone':zone,'nominal_detail':d.get(nominal),'nominal_candidates':c.get(nominal),'nominal_parties':p.get(nominal),'legend_detail':d.get(legend),'legend_parties':p.get(legend),'valid_detail':d.get(valid),'passed':d.get(nominal)==c.get(nominal)==p.get(nominal) and d.get(legend)==p.get(legend) and d.get(valid)==c.get(nominal,0)+p.get(legend,0)})
assert len(names)==165 and len(capital)==49 and all(c['passed'] for c in checks)
assert sum(candidate.values())==23105 and sum(candidate[z] for z in capital)==13195

pieces=defaultdict(list); origins=defaultdict(set); source_metadata=[]; repaired=[]
for region in ('capital','interior'):
    path=ROOT/f'data/raw/tre-rj/rezoneamento_{region}_zonas_unidas.zip'
    with zipfile.ZipFile(path) as z:
        shp=next(n for n in z.namelist() if n.endswith('.shp')); stem=shp[:-4]
        prj=z.read(stem+'.prj').decode()
        assert 'GEOGCS' in prj and ('SIRGAS' in prj or 'WGS' in prj)
        reader=shapefile.Reader(shp=io.BytesIO(z.read(shp)),shx=io.BytesIO(z.read(stem+'.shx')),dbf=io.BytesIO(z.read(stem+'.dbf')),encoding='latin1')
        source_metadata.append({'region':region,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'crs_wkt':prj,'records':len(reader),'archive_dates':sorted(set(str(i.date_time[:3]) for i in z.infolist())),'effective_2026':'unconfirmed'})
        for record in reader.iterShapeRecords():
            props=record.record.as_dict(); zone=str(int(props['Name'] if region=='capital' else props['rotulo']))
            g=shape(record.shape.__geo_interface__)
            if not g.is_valid: repaired.append(zone); g=make_valid(g)
            if g.geom_type=='GeometryCollection': g=union_all([p for p in g.geoms if p.geom_type in ('Polygon','MultiPolygon')])
            assert g.geom_type in ('Polygon','MultiPolygon') and not g.is_empty
            pieces[zone].append(g); origins[zone].add(region)
ambiguous=sorted([z for z,o in origins.items() if len(o)>1 or (z in capital and 'capital' not in o) or (z in names and z not in capital and 'capital' in o)],key=int)
geometries={z:union_all(gs) for z,gs in pieces.items() if z not in ambiguous}
rows=[]; features=[]
for zone in sorted(names,key=int):
    denominator=groups['detail'][zone]['QT_TOTAL_VOTOS_VALIDOS']
    row={'id':'RJ-'+zone,'zone':zone,'state':'RJ','capital':zone in capital,'municipalities':list(names[zone].values()),'municipality_codes':list(names[zone]),'candidate_valid_votes':candidate[zone],'office_valid_votes':denominator,'vote_share_percent':100*candidate[zone]/denominator if denominator else None,'geometry_status':'available' if zone in geometries else 'ambiguous' if zone in ambiguous else 'missing'}
    rows.append(row)
    if zone in geometries: features.append({'type':'Feature','properties':{'id':row['id']},'geometry':mapping(geometries[zone].simplify(.00015,preserve_topology=True))})
report={'zones':len(rows),'capital_zones':len(capital),'state_votes':sum(candidate.values()),'capital_votes':sum(candidate[z] for z in capital),'checks':checks,'missing':sorted(set(names)-set(geometries),key=int),'extra':sorted(set(pieces)-set(names),key=int),'ambiguous':ambiguous,'geometry_repairs':sorted(set(repaired),key=int),'matched':len(features),'sources':source_metadata,'warning':'Malha oficial TRE-RJ; vigência em 2026 não confirmada. Cruzamento exploratório por UF e número da zona.'}
out=ROOT/'data/processed'; out.mkdir(exist_ok=True)
(out/'leo-lupi-2026-rj-zones.json').write_text(json.dumps({'zones':rows,'coverage':report},ensure_ascii=False,indent=2),encoding='utf8')
(out/'rj-zones.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False),encoding='utf8')
with (out/'leo-lupi-2026-rj-zones.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows({k:' | '.join(v) if isinstance(v,list) else v for k,v in r.items()} for r in rows)
(ROOT/'data/validation/zone-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ('checks','sources')},ensure_ascii=True,indent=2))
