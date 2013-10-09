__author__ = 'yiqingj'

from math import pi,cos,sin,log,exp,atan

import sys, os, json
import mapnik
from map import vector_pb2, common_pb2

DEG_TO_RAD = pi/180
RAD_TO_DEG = 180/pi

# Default number of rendering threads to spawn, should be roughly equal to number of CPU cores available
NUM_THREADS = 4

def minmax (a,b,c):
    a = max(a,b)
    a = min(a,c)
    return a

class GoogleProjection:
    def __init__(self,levels=18):
        self.Bc = [] #degree
        self.Cc = [] #Perimeter
        self.zc = [] #global pixel size
        self.Ac = [] #tile size n*n
        c = 256
        for d in range(0,levels):
            e = c/2;
            self.Bc.append(c/360.0)
            self.Cc.append(c/(2 * pi))
            self.zc.append((e,e))
            self.Ac.append(c)
            c *= 2

    def fromLLtoPixel(self,ll,zoom):
         d = self.zc[zoom]
         e = round(d[0] + ll[0] * self.Bc[zoom])
         f = minmax(sin(DEG_TO_RAD * ll[1]),-0.9999,0.9999)
         g = round(d[1] + 0.5*log((1+f)/(1-f))*-self.Cc[zoom])
         return (e,g)

    def fromPixelToLL(self,px,zoom):
         e = self.zc[zoom]
         f = (px[0] - e[0])/self.Bc[zoom]
         g = (px[1] - e[1])/-self.Cc[zoom]
         h = RAD_TO_DEG * ( 2 * atan(exp(g)) - 0.5 * pi)
         return (f,h)
    def fromLLtoTileId(self,ll,zoom):
        px,py = self.fromLLtoPixel(ll,zoom)
        x = int(px/256)
        y = int(py/256)
        z = zoom
        return (x,y,z)


class TileProvider:

    def __init__(self, map):
        self.map = map;
        self.tileProj = GoogleProjection()
        self.mapProj = mapnik.Projection(map.srs)
    def bbox(self,x,y,z):
    # Calculate pixel positions of bottom-left & top-right
        p0 = (x * 256, (y + 1) * 256)
        p1 = ((x + 1) * 256, y * 256)

        # Convert to LatLong (EPSG:4326)
        l0 = self.tileProj.fromPixelToLL(p0, z);
        l1 = self.tileProj.fromPixelToLL(p1, z);

        # Convert to map projection (e.g. mercator co-ords EPSG:900913)
        c0 = self.mapProj.forward(mapnik.Coord(l0[0],l0[1]))
        c1 = self.mapProj.forward(mapnik.Coord(l1[0],l1[1]))

        # Bounding box for the tile
        bbox = mapnik.Box2d(c0.x,c0.y, c1.x,c1.y)
        return bbox;
    def coordToPBPolyline(self,coordinates,polyline):
        lastLat=0
        lastLon=0
        for i in range(len(coordinates)):
            ll = coordinates[i]
            if i == 0:
                lat = lastLat = ll[0]
                lon = lastLon = ll[1]
            else:
                lat = ll[0]-lastLat
                lon = ll[1]- lastLon
            polyline.latlon.append(int(lat*100000))
            polyline.latlon.append(int(lon*100000))
        return

    def highwayToPBRoadType(self,highway):
        if highway == 'highway':
            return common_pb2.RT_HIGHWAY
        elif highway == 'residential':
            return common_pb2.RT_LOCAL
        elif highway == 'pedestrian':
            return common_pb2.RT_PEDESTRIAN
        elif highway == 'service':
            return common_pb2.RT_TERMINAL
        elif highway == 'footway':
            return common_pb2.RT_PEDESTRIAN
        elif highway == 'tertiary':
            return common_pb2.RT_LOCAL
        elif highway == 'path':
            return common_pb2.RT_NON_NAVIGABLE
        else:
            print 'unknown highway: ', highway
            return common_pb2.RT_UNKNOWN

    def handleFeature(self, pfTile, feature):
        geoPath = json.loads(feature.geometries().to_geojson())
        type = geoPath['type']
        name = feature.__getitem__('name')
        highway = feature.__getitem__('highway')
        if highway is not None and type == 'LineString':  # Road feature?
            rf = pfTile.rf.add()
            self.coordToPBPolyline(geoPath['coordinates'], rf.lines.add())
            if name is not None:
                fn = rf.roadNames.add()
                fn.name = name
            if highway is not None:
                rf.roadType = self.highwayToPBRoadType(highway)
        elif type == 'LineString':  # Line feature?
            pass
        elif type == 'Polygon':  # Area feature?
            pass
        elif type == 'Point':  # Point feature?
            pass
        else:
            print 'unknown type: ', type

    def getTile(self, x, y, zoom):
        bbox = self.bbox(x, y, zoom)
        query = mapnik.Query(bbox)
        query.add_property_name('name')
        query.add_property_name('highway')
        fs = self.map.layers[0].datasource.features(query)
        pfTile = vector_pb2.VectorMapTile()
        for feature in fs.features:
            self.handleFeature(pfTile,feature)
        return pfTile
    def getTileByLatLon(self, ll, zoom):
        tile = self.tileProj.fromLLtoTileId(ll, zoom)
        print tile
        return self.getTile(tile[0], tile[1], tile[2])

if __name__ == '__main__':

    """
    test code
    """

    m = mapnik.Map(256,256)
    mapnik.load_map(m, 'osm-sunnyvale.xml')
    provider = TileProvider(m)
    ll = (-122.004025,37.386410)
    zoom = 16
    pfTile = provider.getTileByLatLon(ll, zoom)
    f = open('tile.pb','wb');
    f.write(pfTile.SerializeToString())
    print pfTile

