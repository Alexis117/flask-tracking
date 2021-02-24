from app import db
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()), primary_key=True)
    email = db.Column('email', db.String(80), unique=True)
    name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    password = db.Column(db.String(20))
    latitude = db.Column(db.String(20))
    longitude = db.Column(db.String(20))
    sharing_location = db.Column(db.Boolean(), default=False, nullable=False)

    def __repr__(self):
        return f'<User {self.id}>'

    def save(self):
        '''Simplifying orm savings'''
        if not self.id:
            db.session.add(self)
        db.session.commit()

    def delete(self):
        '''Simplifying orm removings'''
        db.session.delete(self)
        db.session.commit()

    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)