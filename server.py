__author__ = 'yiqingj'

from wsgiref.simple_server import make_server
from pyramid.config import Configurator

if __name__ == '__main__':
    config = Configurator()
    config.add_route('get_tile', '/{zoom}/{x}/{y}')
    config.scan('views')
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8080, app)
    print 'starting server on 8080'
    server.serve_forever()
    print 'server is up.'