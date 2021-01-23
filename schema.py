import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from models import User
import jwt 
from rx import Observable
from app import geolocation_subject
from utils import login_required

class UserObject(SQLAlchemyObjectType):
    class Meta:
        model = User

class GeolocationType(graphene.ObjectType):
    uuid =  graphene.ID()
    latitude = graphene.String()
    longitude = graphene.String()

class Query(graphene.ObjectType):
    node = relay.Node.Field()
    #all_users = SQLAlchemyConnectionField(UserObject) Makes an automated node connection
    all_users = graphene.List(UserObject)

    def resolve_all_users(self, info, **kwargs):
        print(info.context)
        return User.query.all()

class Login(graphene.Mutation):
    class Arguments:
        password = graphene.String()
        email = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.String()

    @login_required
    def mutate(root, info, email, password):
        user = User.query.filter_by(email=email).first()
        if user is None:
            return {'success':False, 'token':'', 'message':'User does not exist'}
        if not user.check_password(password):
            return {'success':False, 'token':'', 'message':'Password is wrong'}
        token = jwt.encode({'user': user.id}, 'alexis', algorithm='HS256')
        return {'success':True, 'token':token, 'message':'Logged In!'}

class SignUp(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        name = graphene.String()
        last_name = graphene.String()
        password = graphene.String()

    success = graphene.Boolean()
    token = graphene.String()

    def mutate(root, info, name, password, last_name, email):
        user = User.query.filter_by(email=email).first()
        if user is not None:
            raise Exception('Email already used!')
        user = User(name = name, email = email, last_name = last_name)
        user.set_password(password)
        token = jwt.encode({'user': user.id}, 'alexis', algorithm='HS256')
        user.save()
        return {'success':True, 'token':token}

class Mutation(graphene.ObjectType):
    login = Login.Field()
    sign_up = SignUp.Field()

class Subscription(graphene.ObjectType):
    get_location = graphene.Field(GeolocationType, uuid=graphene.ID())

    def resolve_get_location(root, info, uuid):
        return geolocation_subject.filter(lambda x: x.uuid == uuid)

schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)
