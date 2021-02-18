import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from graphene_sqlalchemy_filter import FilterSet

from models import User
from utils import login_required
from app import geolocation_subject, JWT_SECRET

import jwt

'''Schema'''
class UserObject(SQLAlchemyObjectType):
    class Meta:
        model = User

class UserFilter(FilterSet):
    class Meta:
        model = User
        fields = {
            'name': ['contains']
        }

class GeolocationType(graphene.ObjectType):
    uuid =  graphene.ID()
    latitude = graphene.String()
    longitude = graphene.String()

'''Queries'''
class Query(graphene.ObjectType):
    node = relay.Node.Field()
    all_users_filter = graphene.List(UserObject, filters=UserFilter())
    all_users = graphene.List(UserObject)

    def resolve_all_users(self, info, **kwargs):
        return User.query.all()
    
    def resolve_all_users_filter(self, info, filters=None):
        query = User.query
        if filters is not None:
            query = UserFilter.filter(info, query, filters)
        return query.all()

'''Muation Classes'''
class Login(graphene.Mutation):
    class Arguments:
        password = graphene.String()
        email = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.String()

    def mutate(root, info, email, password):
        user = User.query.filter_by(email=email).first()
        if user is None:
            return {'success':False, 'token':'', 'message':'User does not exist'}
        if not user.check_password(password):
            return {'success':False, 'token':'', 'message':'Password is wrong'}
        token = jwt.encode({'user': user.id}, JWT_SECRET, algorithm='HS256')
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

class UpdateLocation(graphene.Mutation):
    class Arguments:
        longitude = graphene.String()
        latitude = graphene.String()

    success = graphene.Boolean()

    @login_required
    def mutate(root, info, latitude, longitude):
        user = info.context.get('user')
        geolocation = GeolocationType(latitude=latitude, longitude=longitude, uuid=user.id)
        geolocation_subject.on_next(geolocation)
        return {'success':True}

class DeleteUser(graphene.Mutation):
    class Arguments:
        id = graphene.String()
    
    success = graphene.Boolean()
    user = graphene.Field(UserObject)
    message = graphene.String()

    def mutate(root, info, id):
        user = User.query.get(id)
        if user is None:
            return {'success':False, 'user':None, 'message':'User does not exist!'}
        user.delete()
        return {'success':True, 'user':user, 'message':'Successfully deleted user'}

class Mutation(graphene.ObjectType):
    login = Login.Field()
    sign_up = SignUp.Field()
    update_location = UpdateLocation.Field()
    delete_user = DeleteUser.Field()

'''Subscriptions'''
class Subscription(graphene.ObjectType):
    get_location = graphene.Field(GeolocationType, uuid=graphene.String())

    @login_required
    def resolve_get_location(root, info, uuid):
        return geolocation_subject.filter(lambda x: x.uuid == uuid)

schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)
