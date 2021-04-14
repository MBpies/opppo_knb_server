import werkzeug
from flask import Flask, request
from flask_json import FlaskJSON, JsonError, json_response, as_json
from flask_sqlalchemy import SQLAlchemy

# глобальные переменные
app = Flask(__name__)
json = FlaskJSON(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Python_proj\\knb_server\\test.db'  # !!исправьте под себя!!
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = "False"
lobbyList = []
availablePlayers = []


class Lobby():
    lobbyId = 0


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # игнорируйте эти предупрежждения, они чинятся в рантайме
    username = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(20), unique=False, nullable=False)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)


# обработка по адресам
@app.route('/auth', methods=['POST'])
def auth():
    content = request.get_json()
    username = content["login"]
    password = content["password"]
    if content['type'] == "registration":
        checker = User.query.filter_by(username=username).first()
        if checker is not None:  # проверка если логин уже есть
            return json_response(status_=409, type="registration", status="login exists")
        db.session.add(User(username=username, password=password))  # закинуть в бд
        db.session.commit()  # зачекинить изменения
        return json_response(status_=200, type="registration", status="ok")

    if content['type'] == "authorization":
        checker = User.query.filter_by(username=username).first()
        if checker is None:  # проверка существует ли логин
            return json_response(status_=404, type="authorization", status="login doesn't exists")
        if checker.password == password:
            return json_response(status_=200, type="authorization", status="ok")
        else:
            return json_response(status_=401, type="authorization", status="login error")


@app.route('/lobby', methods=['POST'])
def lobby():
    content = request.get_json()
    if content['type'] == "createLobby":
        return " error"
    if content['type'] == "connectToLobby":
        return " error"


# Обработка ошибок
@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400


# запуск всего этого самого
if __name__ == '__main__':
    app.run(debug=True)
