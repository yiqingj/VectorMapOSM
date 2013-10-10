__author__ = 'yiqingj'

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config
import vectormap
import mapnik
import httplib
from map import vector_pb2

map = mapnik.Map(256,256)
mapnik.load_map(map, 'osm-sunnyvale.xml')

def getTile(request):
    provider = vectormap.TileProvider(map)
    zoom = int(request.matchdict['zoom'])
    x = int(request.matchdict['x'])
    y = int(request.matchdict['y'])
    try:
        format = request.params['format']
    except KeyError:
        format = 'pb'
    print 'GetTile: ', x, y , zoom
    pbTile = provider.getTile(x,y,zoom)
    if format == "pb":
        return Response(
            content_type="tapplication/x-protobuf",
            body=pbTile.SerializeToString()
        )
    elif format == 'str':
        return Response(
            content_type="text/plain",
            body='Response: ' + pbTile.__str__()
        )
    else:
        return Response(
            "UnRecognized format."
        )

def tileFinder(request):
    provider = vectormap.TileProvider(map)
    zoom = int(request.matchdict['zoom'])
    latlon = int(request.matchdict['latlon'])
    pbTile = provider.getTileByLatLon(latlon,zoom)
    return Response(
        content_type="application/x-protobuf",
        body=pbTile.SerializeToString()
    )

def refVectorTile(request):
    """
    get reference vector tile data from existing product
    this is just providing a easy way to compare the difference.
    """
    zoom = int(request.matchdict['zoom'])
    x = int(request.matchdict['x'])
    y = int(request.matchdict['y'])
    conn = httplib.HTTPConnection("hqd-vectortilefscdn.telenav.com")
    path = "/maps/v3/VectorTile/TomTom/NA/13M3c/%(zoom)s/%(y)s/%(x)s" % request.matchdict
    conn.request("GET", path)
    response = conn.getresponse()
    data =  response.read()
    pfTile = vector_pb2.VectorMapTile()
    pfTile.ParseFromString(data)
    return Response(
        content_type="text/plain",
        body=pfTile.__str__()
    )


if __name__ == '__main__':
    config = Configurator()
    config.add_route('vector_tile', '/maps/v3/VectorTile/{dataSet}/NA/{dataVersion}/{zoom}/{y}/{x}')
    config.add_route('ref_vector_tile', '/maps/v3/VectorTileRef/{dataSet}/NA/{dataVersion}/{zoom}/{y}/{x}')
    config.add_route('tile_finder', '/{zoom}/{latlon}')
    config.add_view(getTile, route_name='vector_tile')
    config.add_view(refVectorTile, route_name='ref_vector_tile')
    config.add_view(tileFinder, route_name='tile_finder')
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    print 'starting server on 8080'
    server.serve_forever()
    print 'server is up.'