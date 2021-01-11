from flask import Flask
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import User

@app.route('/', methods=['POST', 'GET'])
def hello_world():
    print(User.query.all())
    if request.method == 'POST':
        user = User(name = request.form['name'])
        user.save()
    return render_template('form.html')