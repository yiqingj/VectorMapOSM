__author__ = 'yiqingj'

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
import vectormap
import mapnik

map = mapnik.Map(256,256)
mapnik.load_map(map, 'osm-sunnyvale.xml')

@view_config(route_name='get_tile')
def getTile(request):
    provider = vectormap.TileProvider(map)
    zoom = int(request.matchdict['zoom'])
    x = int(request.matchdict['x'])
    y = int(request.matchdict['y'])
    pbTile = provider.getTile(x,y,zoom)
    print 'GetTile: ', x, y , zoom
    return Response(
        content_type="application/x-protobuf",
        body=pbTile.SerializeToString()
    )
