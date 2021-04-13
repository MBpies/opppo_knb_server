import werkzeug
from flask import Flask, request
from datetime import datetime
from flask_json import FlaskJSON, JsonError, json_response, as_json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

# глобальные переменные
app = Flask(__name__)
json = FlaskJSON(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Python_proj\\knb_server\\test.db'  # !!исправьте под себя!!
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = "False"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(20), unique=False, nullable=False)


# обработка по адресам
@app.route('/auth', methods=['POST'])
def auth():
    content = request.get_json()
    username = content["login"]
    password = content["password"]
    if (content['type'] == "registration"):
        checker = User.query.filter_by(username=username).first()
        if (checker is not None):  # проверка если логин уже есть
            return "already exist"
        db.session.add(User(username=username, password=password))  # закинуть в бд
        db.session.commit()  # зачекинить изменения
        return "All good"

    if (content['type'] == "authorization"):
        checker = User.query.filter_by(username=username).first()
        if (checker is None):  # проверка существует ли логин
            return "dosent exist"
        if (checker.password == password):
            return "All good"
        else:
            return "password error"


# Обработка ошибок
@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400


# запуск всего этого самого
if __name__ == '__main__':
    app.run(debug=True)
