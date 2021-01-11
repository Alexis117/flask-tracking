from app import db
import uuid

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column('id', db.Text(length=36), default=lambda: str(uuid.uuid4()), primary_key=True)
    name = db.Column(db.String(80))

    def __repr__(self):
        return f'<User {self.id}>'

    def save(self):
        '''Simplifying orm savings'''
        if not self.id:
            db.session.add(self)
        db.session.commit()