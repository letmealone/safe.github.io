"""Prepare local, offline map paths. Lower district/neighborhood shapes are illustrative."""
from pathlib import Path
import json
from shapely.geometry import shape,box
from shapely.ops import transform
root=Path(__file__).resolve().parent
names={'KR-42':'강원','KR-41':'경기','KR-44':'충남','KR-28':'인천','KR-45':'전북','KR-46':'전남','KR-48':'경남','KR-26':'부산','KR-31':'울산','KR-47':'경북','KR-49':'제주','KR-11':'서울','KR-30':'대전','KR-50':'세종','KR-43':'충북','KR-29':'광주','KR-27':'대구'}
regions={}
def record(key,name,parent,g,level,source):
 g=g.simplify(.003 if level>0 else .009,preserve_topology=True)
 projected=transform(lambda x,y:(x*80,-y*100),g)
 polys=[projected] if projected.geom_type=='Polygon' else list(projected.geoms)
 path=' '.join('M'+' L'.join(f'{x:.3f},{y:.3f}' for x,y in p.exterior.coords)+' Z' for p in polys if p.area>.00003)
 pt=projected.representative_point();regions[key]={'id':key,'name':name,'parent':parent,'level':level,'path':path,'bounds':list(projected.bounds),'label':[pt.x,pt.y],'source':source}
for f in json.loads((root/'ADM1.geojson').read_text())['features']:
 key=f['properties']['shapeISO'];record(key,names[key], 'kr',shape(f['geometry']),0,'시·도 경계 2021')
g=next(shape(f['geometry']) for f in json.loads((root/'ADM2.geojson').read_text())['features'] if f['properties']['shapeName']=='Goyang-si')
record('goyang','고양시','KR-41',g,1,'고양시 경계 2020')
x0,y0,x1,y1=g.bounds;xm=x0+(x1-x0)*.58;ym=y0+(y1-y0)*.57
samples=[('ilsanwest','일산서구',g.intersection(box(x0,ym,xm,y1))),('ilsaneast','일산동구',g.intersection(box(x0,y0,xm,ym))),('deogyang','덕양구',g.intersection(box(xm,y0,x1,y1)))]
for key,name,geom in samples:record(key,name,'goyang',geom,2,'구·동 경계는 조작 설명용 구획')
east=samples[1][2];a,b,c,d=east.bounds;m=a+(c-a)*.48;n=b+(d-b)*.5
for key,name,geom in [('janghang1','장항1동',east.intersection(box(a,b,m,d))),('janghang2','장항2동',east.intersection(box(m,b,c,n))),('madu1','마두1동',east.intersection(box(m,n,c,d)))]:record(key,name,'ilsaneast',geom,3,'구·동 경계는 조작 설명용 구획')
regions['kr']={'id':'kr','name':'전국','parent':None,'level':-1,'bounds':[9940,-3865,10565,-3290],'label':[10250,-3600],'source':'시·도 경계 2021 / 하위 구획 일부 예시'}
(root.parent.parent/'map_geometry.js').write_text('/* geoBoundaries / Natural Earth; attribution in reference/map/README.md */\nconst MAP_REGIONS='+json.dumps(regions,ensure_ascii=False,separators=(',',':'))+';\n')
(root/'README.md').write_text('''# 시안 지도 경계 출처

- 시·도: geoBoundaries gbOpen KOR ADM1, 경계 기준 2021, 원출처 Natural Earth, Public Domain.
- 고양시: geoBoundaries gbOpen KOR ADM2, 경계 기준 2020, 원출처 geoBoundaries 및 citypopulation.de, CC BY 3.0.
- https://www.geoboundaries.org/api/current/gbOpen/KOR/ADM1/
- https://www.geoboundaries.org/api/current/gbOpen/KOR/ADM2/
- 고정 원본: wmgeolab/geoBoundaries commit 9469f09, releaseData/gbOpen/KOR.
- https://creativecommons.org/licenses/by/3.0/

도형을 단순화하고 좌표를 변환했다. 고양시 아래 구·동 도형은 실제 행정경계가 아닌 클릭 탐색 설명용으로 분할한 가상 구획이다. 건축물 위치·주소·점검 기록·sBIM·근거 그림도 가상이며 실제 안전정보가 아니다. 경계 자료는 최신 행정업무용으로 사용할 수 없다. 모든 지도 자산은 로컬 파일이며 시안 실행 중 외부 지도 서버에 요청하지 않는다.
''')
print({'regions':len(regions),'bytes':(root.parent.parent/'map_geometry.js').stat().st_size})
