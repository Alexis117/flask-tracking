import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from models import User
import jwt 
from rx import Observable
from app import subject_test

class UserObject(SQLAlchemyObjectType):
    class Meta:
        model = User

class Query(graphene.ObjectType):
    node = relay.Node.Field()
    #all_users = SQLAlchemyConnectionField(UserObject) Makes an automated node connection
    all_users = graphene.List(UserObject)

    def resolve_all_users(self, info, **kwargs):
        return User.query.all()

class Login(graphene.Mutation):
    class Arguments:
        password = graphene.String()
        email = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.String()

    def mutate(root, info, email, password):
        user = User.query.filter_by(email=name).first()
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
        user.save()
        token = jwt.encode({'user': user.id}, 'alexis', algorithm='HS256')
        return {'success':True, 'token':token}

class Mutation(graphene.ObjectType):
    login = Login.Field()
    sign_up = SignUp.Field()

class Subscription(graphene.ObjectType):
    count_seconds = graphene.String()

    def resolve_count_seconds(root, info):
        return subject_test

schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)
