"""Build a self-contained local map from supplied IBGE geometry and TSE votes."""
import io
import json
import math
from pathlib import Path
import sys
import shutil
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.local-python'))
import shapefile
from shapely.geometry import shape

dataset = json.loads((ROOT / 'data/processed/leo-lupi-2026-rj.json').read_text(encoding='utf-8'))
votes = {r['code_ibge']:r for r in dataset['municipalities']}
features = []
with zipfile.ZipFile(ROOT / 'RJ_Municipios_2025.zip') as z:
    reader = shapefile.Reader(shp=io.BytesIO(z.read('RJ_Municipios_2025.shp')), dbf=io.BytesIO(z.read('RJ_Municipios_2025.dbf')), shx=io.BytesIO(z.read('RJ_Municipios_2025.shx')), encoding='utf-8')
    for item in reader.iterShapeRecords():
        code = item.record.as_dict()['CD_MUN']
        geometry = shape(item.shape.__geo_interface__).simplify(0.0006, preserve_topology=True)
        polygons = [geometry] if geometry.geom_type == 'Polygon' else list(geometry.geoms)
        rings = []
        for polygon in polygons:
            for ring in [polygon.exterior, *polygon.interiors]:
                # Spherical Mercator; actual IBGE geographic coordinates, north up.
                rings.append([(math.radians(x), -math.log(math.tan(math.pi/4+math.radians(y)/2))) for x,y in ring.coords])
        features.append({**votes[code], 'rings':rings})
assert len(features) == 92 and len({r['code_ibge'] for r in features}) == 92
points = [p for f in features for r in f['rings'] for p in r]
x0,y0 = map(min, zip(*points)); x1,y1 = map(max, zip(*points))
scale = min(940/(x1-x0), 650/(y1-y0))
width,height = (x1-x0)*scale+40, (y1-y0)*scale+40
for f in features:
    f['path'] = ' '.join('M'+'L'.join(f'{(x-x0)*scale+20:.2f},{(y-y0)*scale+20:.2f}' for x,y in ring)+'Z' for ring in f.pop('rings'))
payload = {'width':width,'height':height,'features':features}
zone_dataset = json.loads((ROOT / 'data/processed/leo-lupi-2026-rj-zones.json').read_text(encoding='utf-8'))
zone_shapes = json.loads((ROOT / 'data/processed/rj-zones.geojson').read_text(encoding='utf-8'))
zone_paths = {}
for feature in zone_shapes['features']:
    geometry = feature['geometry']
    polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
    rings = [[((math.radians(x)-x0)*scale+20, (-math.log(math.tan(math.pi/4+math.radians(y)/2))-y0)*scale+20) for x,y in ring] for polygon in polygons for ring in polygon]
    pts = [p for r in rings for p in r]
    lowx,lowy=map(min,zip(*pts)); highx,highy=map(max,zip(*pts))
    zone_paths[feature['properties']['id']] = {'path':' '.join('M'+'L'.join(f'{x:.2f},{y:.2f}' for x,y in ring)+'Z' for ring in rings),'bounds':[lowx,lowy,highx,highy]}
payload['zones'] = [{**r,**zone_paths.get(r['id'],{})} for r in zone_dataset['zones']]
payload['coverage'] = {k:v for k,v in zone_dataset['coverage'].items() if k != 'checks'}
crosswalk=json.loads((ROOT/'data/processed/capital-neighborhood-crosswalk.json').read_text(encoding='utf8'))
neighborhood_shapes=json.loads((ROOT/'data/processed/capital-neighborhoods-display.geojson').read_text(encoding='utf8'))
neighborhood_paths={}
for feature in neighborhood_shapes['features']:
    geometry=feature['geometry']
    polygons=[geometry['coordinates']] if geometry['type']=='Polygon' else geometry['coordinates']
    rings=[[((math.radians(x)-x0)*scale+20,(-math.log(math.tan(math.pi/4+math.radians(y)/2))-y0)*scale+20) for x,y in ring] for polygon in polygons for ring in polygon]
    neighborhood_paths[feature['properties']['code']]=' '.join('M'+'L'.join(f'{x:.2f},{y:.2f}' for x,y in ring)+'Z' for ring in rings)
payload['neighborhoods']=[{**r,'path':neighborhood_paths[r['code']]} for r in crosswalk['neighborhoods']]
payload['neighborhoodRelations']=crosswalk['relations']
payload['neighborhoodMetadata']=crosswalk['metadata']
template = (ROOT / 'map/template.html').read_text(encoding='utf-8')
shutil.copyfile(ROOT / 'data/processed/leo-lupi-2026-rj.csv', ROOT / 'map/leo-lupi-2026-rj.csv')
shutil.copyfile(ROOT / 'data/processed/leo-lupi-2026-rj-zones.csv', ROOT / 'map/leo-lupi-2026-rj-zones.csv')
for extension in ('csv','json'):
    shutil.copyfile(ROOT/f'data/processed/capital-neighborhood-crosswalk.{extension}',ROOT/f'map/capital-neighborhood-crosswalk.{extension}')
(ROOT / 'map/index.html').write_text(template.replace('__MAP_DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':'))),encoding='utf-8')
# GitHub Pages publishes the repository root; keep its static bundle in sync.
for filename in ('index.html','leo-lupi-2026-rj.csv','leo-lupi-2026-rj-zones.csv','capital-neighborhood-crosswalk.csv','capital-neighborhood-crosswalk.json'):
    shutil.copyfile(ROOT/'map'/filename,ROOT/filename)
print(f'Map built: {len(features)} municipalities; {sum(f["candidate_valid_votes"] for f in features)} votes; {(ROOT / "map/index.html").stat().st_size} bytes')
