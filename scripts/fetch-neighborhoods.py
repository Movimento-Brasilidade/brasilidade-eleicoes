"""Download a complete official neighborhood snapshot, without generalization."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
from datetime import datetime, timezone
import json, hashlib
ROOT=Path(__file__).resolve().parents[1]
BASE='https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Cartografia/Limites_administrativos/FeatureServer/4'
def get(params, endpoint='/query'):
    with urlopen(BASE+endpoint+'?'+urlencode(params),timeout=90) as r:
        data=json.load(r)
    if 'error' in data: raise RuntimeError(data['error'])
    return data
metadata=get({'f':'json'},'')
ids=get({'where':'1=1','returnIdsOnly':'true','f':'json'})['objectIds']
features=[]
for start in range(0,len(ids),100):
    page=get({'objectIds':','.join(map(str,ids[start:start+100])),'outFields':'objectid,codbairro,nome','returnGeometry':'true','outSR':4326,'f':'geojson'})
    assert not page.get('exceededTransferLimit')
    features.extend(page['features'])
assert len(features)==len(ids)
codes=[f['properties']['codbairro'] for f in features]
assert all(codes) and len(set(codes))==len(codes)
out=ROOT/'data/raw/prefeitura';out.mkdir(parents=True,exist_ok=True)
blob=json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False).encode('utf8')
(out/'capital-neighborhoods.geojson').write_bytes(blob)
(out/'source.json').write_text(json.dumps({'url':BASE,'retrieved_at':datetime.now(timezone.utc).isoformat(),'count':len(features),'sha256':hashlib.sha256(blob).hexdigest(),'metadata':metadata},ensure_ascii=False,indent=2),encoding='utf8')
print(f'Downloaded {len(features)} neighborhoods; {len(blob)} bytes')
