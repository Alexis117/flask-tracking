from flask import Flask
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_graphql import GraphQLView
from graphql_ws.gevent import GeventSubscriptionServer, GeventConnectionContext
from graphql.backend import GraphQLCoreBackend
from flask_sockets import Sockets
from rx.subjects import Subject

subject_test = Subject()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/flask.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['FLASK_ENV'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import User
from schema import schema

@app.route('/', methods=['POST', 'GET'])
def hello_world():
    '''Simple form for dummie user creations'''
    if request.method == 'POST':
        print('-----')
        print(subject_test)
        subject_test.on_next("A")
        user = User(name = request.form['name'])
        user.save()
    return render_template('form.html')

class AuthorizationMiddleware(object):
    def resolve(self, next, root, info, **args):
        '''Middleware logic before execute every mutation/query'''
        return next(root, info, **args)

'''GraphQL Endpoint'''
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True,
        #middleware=[AuthorizationMiddleware()], Apply middleware for global authorization
        #get_context=lambda: {'request': request} Modifyng context
    )
)

import json

class CustomSubscriptionServer(GeventSubscriptionServer):
    def handle(self, ws, request_context=None):
        connection_context = GeventConnectionContext(ws, request_context)
        #connection_context.send(json.dumps({"type": "websocket.accept", "subprotocol": "graphql-ws"}))
        return super().handle(ws, request_context)

    def on_message(self, connection_context, message):
        print(message)
        return super().on_message(connection_context, message)

sockets = Sockets(app)
subscription_server = CustomSubscriptionServer(schema)
app.app_protocol = lambda environ_path_info: 'graphql-ws'

@sockets.route('/graphql')
def echo_socket(ws):
    subscription_server.handle(ws)
    return []

if __name__ == '__main__':
    from gevent.pywsgi import WSGIServer
    from geventwebsocket.handler import WebSocketHandler

    http_server = WSGIServer(('',5000), app, handler_class=WebSocketHandler)
    http_server.serve_forever()