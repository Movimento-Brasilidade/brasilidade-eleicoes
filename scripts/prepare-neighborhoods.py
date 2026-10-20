"""Spatial many-to-many crosswalk. Area percentages are never vote estimates."""
import csv, io, json, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.local-python'))
import shapefile
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform
from shapely import make_valid, union_all

to_utm=Transformer.from_crs(4674,31983,always_xy=True).transform
neighborhood_utm=Transformer.from_crs(4326,31983,always_xy=True).transform
to_geo=Transformer.from_crs(31983,4326,always_xy=True).transform
repairs=[]
def polygon(g, key):
    if not g.is_valid: repairs.append(key);g=make_valid(g)
    if g.geom_type=='GeometryCollection': g=union_all([x for x in g.geoms if x.geom_type in ('Polygon','MultiPolygon')])
    assert g.geom_type in ('Polygon','MultiPolygon') and not g.is_empty and g.is_valid
    return g
zones={}
with zipfile.ZipFile(ROOT/'data/raw/tre-rj/rezoneamento_capital_zonas_unidas.zip') as z:
    stem=next(n[:-4] for n in z.namelist() if n.endswith('.shp'))
    reader=shapefile.Reader(shp=io.BytesIO(z.read(stem+'.shp')),shx=io.BytesIO(z.read(stem+'.shx')),dbf=io.BytesIO(z.read(stem+'.dbf')),encoding='latin1')
    for r in reader.iterShapeRecords():
        key='RJ-'+str(int(r.record.as_dict()['Name']))
        g=polygon(transform(to_utm,shape(r.shape.__geo_interface__)),key)
        zones[key]=union_all([zones[key],g]) if key in zones else g
expected=json.loads((ROOT/'data/processed/leo-lupi-2026-rj-zones.json').read_text(encoding='utf8'))['zones']
assert set(zones)=={r['id'] for r in expected if r['capital']} and len(zones)==49
source=json.loads((ROOT/'data/raw/prefeitura/source.json').read_text(encoding='utf8'))
raw=json.loads((ROOT/'data/raw/prefeitura/capital-neighborhoods.geojson').read_text(encoding='utf8'))
neighborhoods=[];relations=[];display=[]
for f in raw['features']:
    code=str(f['properties']['codbairro']).zfill(3); name=f['properties']['nome']
    g=polygon(transform(neighborhood_utm,shape(f['geometry'])),code)
    assert g.area>0
    hits=[];areas=[]
    for zone,z in zones.items():
        if not g.intersects(z):continue
        intersection=g.intersection(z)
        if intersection.area<=0:continue
        percent=100*intersection.area/g.area
        relation={'neighborhood_code':code,'neighborhood':name,'zone_id':zone,'zone':zone.split('-')[1],'intersection_area_m2':intersection.area,'neighborhood_area_m2':g.area,'neighborhood_area_percent':percent,'classification':'integral' if percent>=99.9 else 'parcial','residual':percent<.1}
        relations.append(relation);hits.append(relation);areas.append(intersection)
    covered=union_all(areas).area if areas else 0
    neighborhoods.append({'code':code,'name':name,'area_m2':g.area,'covered_percent':100*covered/g.area,'uncovered_area_m2':max(0,g.area-covered),'overlap_area_m2':max(0,sum(a.area for a in areas)-covered),'zone_count':len(hits),'area_percent_sum':sum(r['neighborhood_area_percent'] for r in hits)})
    display.append({'type':'Feature','properties':{'code':code},'geometry':mapping(transform(to_geo,g.simplify(8,preserve_topology=True)))})
assert len({r['code'] for r in neighborhoods})==len(neighborhoods)==source['count']
assert all(0<r['neighborhood_area_percent']<=100.000001 for r in relations)
assert sum(r['candidate_valid_votes'] for r in expected)==23105
assert sum(r['candidate_valid_votes'] for r in expected if r['capital'])==13195
report={'source':{k:source[k] for k in ('url','retrieved_at','count','sha256')},'area_crs':'EPSG:31983','integral_threshold_percent':99.9,'residual_threshold_percent':.1,'zone_count':49,'neighborhood_count':len(neighborhoods),'relation_count':len(relations),'integral_relations':sum(r['classification']=='integral' for r in relations),'residual_relations':sum(r['residual'] for r in relations),'uncovered_neighborhoods':[r for r in neighborhoods if r['zone_count']==0],'coverage':neighborhoods,'geometry_repairs':repairs,'warning':'Cruzamento territorial exploratório. Malha eleitoral com datas internas de 2018 e vigência em 2026 não confirmada. Percentuais representam área, não votos. Nenhuma interseção de área positiva foi excluída.'}
out=ROOT/'data/processed'
(out/'capital-neighborhood-crosswalk.json').write_text(json.dumps({'neighborhoods':neighborhoods,'relations':relations,'metadata':{k:v for k,v in report.items() if k!='coverage'}},ensure_ascii=False,indent=2),encoding='utf8')
(out/'capital-neighborhoods-display.geojson').write_text(json.dumps({'type':'FeatureCollection','features':display},ensure_ascii=False),encoding='utf8')
with (out/'capital-neighborhood-crosswalk.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(relations[0]));w.writeheader();w.writerows(relations)
(ROOT/'data/validation/neighborhood-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ('source','coverage','warning')},ensure_ascii=True,indent=2))
