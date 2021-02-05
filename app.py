from flask import Flask
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_graphql import GraphQLView
from graphql_ws.gevent import GeventSubscriptionServer
from graphql import graphql
from flask_sockets import Sockets
from rx.subjects import Subject
from rx import Observable
import jwt 
import json
from decouple import config


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['FLASK_ENV'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
JWT_SECRET = config('JWT_SECRET')

geolocation_subject = Subject() #Subject to subscribe geolocation events


from models import User
from schema import schema, GeolocationType
from graphene import Context

@app.route('/', methods=['POST', 'GET'])
def geolocation_form():
    '''Simple form for dummie geolocation data'''
    if request.method == 'POST':
        uuid = request.form['uuid']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        geolocation = GeolocationType(uuid=uuid, latitude=latitude, longitude=longitude)
        geolocation_subject.on_next(geolocation)
    return render_template('geolocation_form.html')

class AuthorizationMiddleware(object):
    def resolve(self, next, root, info, **args):
        '''Middleware Authorization logic before execute every mutation/query'''
        info.context = {'request':request}
        if request.headers.get('Authorization'):
            decoded_user = jwt.decode(request.headers.get('Authorization'), JWT_SECRET, algorithms=['HS256'], options={'require_exp':False})
            user = User.query.get(decoded_user['user'])
            info.context['user'] = user
        return next(root, info, **args)

'''GraphQL Endpoint'''
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True,
        middleware=[AuthorizationMiddleware()], #Apply middleware for global authorization
    )
)

class CustomSubscriptionServer(GeventSubscriptionServer):
    '''Overriding the gevent subscription server class for custom context and middleware setting'''

    def on_start(self, connection_context, op_id, params):
        '''Handling errors returned by the execution result before we reach the returned observable'''
        try:
            execution_result = self.execute(connection_context.request_context, params)
        except Exception as e:
            self.send_error(connection_context, op_id, str(e))
        if not isinstance(execution_result, Observable):
            self.send_error(connection_context, op_id, str(execution_result.errors[0]))            
        return super().on_start(connection_context, op_id, params)

    def execute(self, request_context, params):
        '''Sending context to the graphql subscriptions execution'''
        params['context_value'] = request_context
        return graphql(
            self.schema, **dict(params, allow_subscriptions=True))
    
    def on_connection_init(self, connection_context, op_id, payload):
        '''Get AuthToken from the first message from client'''
        #It would be better add a new attribute to connection_context object for avoid to use request_context
        connection_context.request_context = {}
        if payload.get('authToken'):
            decoded_user = jwt.decode(payload.get('authToken'), JWT_SECRET, algorithms=['HS256'], options={'require_exp':False})
            user = User.query.get(decoded_user['user'])
            connection_context.request_context['user'] = user
        return super().on_connection_init(connection_context, op_id, payload)

sockets = Sockets(app)
subscription_server = CustomSubscriptionServer(schema)
app.app_protocol = lambda environ_path_info: 'graphql-ws'

@sockets.route('/graphql')
def echo_socket(ws):
    subscription_server.handle(ws, request)
    return []