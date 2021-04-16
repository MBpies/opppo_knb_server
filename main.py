import uuid

import werkzeug
from flask import Flask, request
from flask_json import FlaskJSON, json_response
from flask_sqlalchemy import SQLAlchemy
from random import randint

# глобальные переменные
app = Flask(__name__)
json = FlaskJSON(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Python_proj\\knb_server\\test.db'  # !!исправьте под себя!!
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = "False"

lobbyList = []



class Lobby():
    def __init__(self, lobbyId, lobbyPLayer1, lobbyPLayer2=None):  # коструктор
        self.lobbyId = lobbyId
        self.lobbyPLayer1 = lobbyPLayer1  # игрок 1 тот кто создает лобби
        self.lobbyPLayer2 = lobbyPLayer2  # игрок 2 тот кто подключается

    def hasName(self, name):
        return self.lobbyPLayer1 == name

    def __eq__(self, other):  # нужна для поиска в листе
        assert isinstance(other, Lobby)  # является ли экземпляром класса
        return self.lobbyId == other.lobbyId  # сравниваем по айдишникам

    def __repr__(self):
        return '[' + str(self.lobbyId) + ' ' + str(self.lobbyPLayer1) + ' ' + str(self.lobbyPLayer2) + ']'

    def __str__(self):
        return '[' + str(self.lobbyId) + ' ' + str(self.lobbyPLayer1) + ' ' + str(self.lobbyPLayer2) + ']'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # игнорируйте эти предупрежждения, они чинятся в рантайме
    username = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(20), unique=False, nullable=False)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)


def genRandId():
    range_start = 10 ** (6 - 1)
    range_end = (10 ** 6) - 1
    return randint(range_start, range_end)


def searchByName(name):
    has = False
    for lob in lobbyList:
        has = lob.hasName(name)
    return has


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


@app.route('/createLobby', methods=['POST'])
def createLobby():
    content = request.get_json()
    checker = User.query.filter_by(username=content['userId']).first()
    if checker is None:  # проверка существует ли указанный логин
        return json_response(status_=401, type=content['type'], status="invalid login")

    if searchByName(content['userId']):
        gameLobby = Lobby(content['gameID'], content['userId'])  # создаем пустышку для поиска
        id = lobbyList.index(gameLobby)
        gameLobby = lobbyList[id]  # находим оригинал
        if gameLobby.lobbyPLayer2 is None:
            return json_response(status_=202, type="createLobby", status="waiting for players",
                                 gameID=gameLobby.lobbyId)
        else:
            return json_response(status_=200, type="createLobby", status="ok", gameID=gameLobby.lobbyId,
                                 opponent=gameLobby.lobbyPLayer2)

    gameLobby = Lobby(str(genRandId()), content['userId'])
    lobbyList.append(gameLobby)
    return json_response(status_=202, type="createLobby", status="waiting for players", gameID=gameLobby.lobbyId)


@app.route('/connectToLobby', methods=['POST'])
def connectToLobby():
    content = request.get_json()
    checker = User.query.filter_by(username=content['userId']).first()
    if checker is None:  # проверка существует ли указанный логин
        return json_response(status_=401, type=content['type'], status="invalid login")
    try:
        id = lobbyList.index(Lobby(content['gameID'], content['userId']))
    except ValueError as ve:
        return json_response(status_=404, type=content['type'], status=ve)
    gameLobby = lobbyList[id]
    gameLobby.lobbyPLayer2 = content['userId']
    lobbyList[id] = gameLobby
    return json_response(status_=200, type="connectToLobby", status="ok", gameID=gameLobby.lobbyId,
                         opponent=gameLobby.lobbyPLayer1)



@app.route('/dev', methods=['POST'])
def dev():
    print(lobbyList)
    return 'huh'


# Обработка ошибок
@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400


# запуск всего этого самого
if __name__ == '__main__':
    app.run(debug=True)
