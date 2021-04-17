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
    def __init__(self, lobbyId, lobbyPLayer1, lobbyPLayer2=None, answPl1=None, answPl2=None):  # коструктор
        self.lobbyId = lobbyId
        self.lobbyPLayer1 = lobbyPLayer1  # игрок 1 тот кто создает лобби
        self.lobbyPLayer2 = lobbyPLayer2  # игрок 2 тот кто подключается
        self.answPl1 = answPl1
        self.answPl2 = answPl2

    def hasName(self, name):
        if self.lobbyPLayer1 == name:
            return self
        return None

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
    has = None
    for lob in lobbyList:
        has = lob.hasName(name)
        if has is not None:
            return has
    return has


def didFirstPLayerWon(ans1, ans2):  # 1-камень, 2-ножницы, 3-бумага.
    if ans1 == 1 and ans2 == 1:
        return "even"
    if ans1 == 2 and ans2 == 2:
        return "even"
    if ans1 == 3 and ans2 == 3:
        return "even"
    if ans1 == 1 and ans2 == 2:
        return "won"
    if ans1 == 2 and ans2 == 3:
        return "won"
    if ans1 == 3 and ans2 == 1:
        return "won"
    if ans1 == 1 and ans2 == 3:
        return "lost"
    if ans1 == 2 and ans2 == 1:
        return "lost"
    if ans1 == 3 and ans2 == 2:
        return "lost"


def figureDecode(fig):
    if fig == 1:
        return "rock"
    if fig == 2:
        return "scissors"
    if fig == 3:
        return "paper"


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
    gameLobby = searchByName(content['userId'])  # создаем пустышку для поиска
    if gameLobby is not None:
        # gameLobby = Lobby(content['gameID'], content['userId'])
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
        return json_response(status_=404, type=content['type'], status="no such lobby")
    gameLobby = lobbyList[id]
    gameLobby.lobbyPLayer2 = content['userId']
    lobbyList[id] = gameLobby
    return json_response(status_=200, type="connectToLobby", status="ok", gameID=gameLobby.lobbyId,
                         opponent=gameLobby.lobbyPLayer1)


def updateThing(user, result):
    if result == "won":
        user.wins = user.wins + 1
        db.session.commit()
    if result == "lost":
        user.losses = user.losses + 1
        db.session.commit()


@app.route('/selectAnswer', methods=['POST'])
def selectAnswer():
    content = request.get_json()
    checker = User.query.filter_by(username=content['userId']).first()
    if checker is None:  # проверка существует ли указанный логин
        return json_response(status_=401, type=content['type'], status="invalid login")
    try:  # проверка существует ли лобби
        id = lobbyList.index(Lobby(content['gameID'], content['userId']))
    except ValueError as ve:
        return json_response(status_=404, type=content['type'], status="no such lobby")
    gameLobby = lobbyList[id]

    if gameLobby.lobbyPLayer1 == content['userId']:
        gameLobby.answPl1 = content['answerId']
        lobbyList[id] = gameLobby
        if gameLobby.lobbyPLayer2 is None:
            return json_response(status_=404, type="selectAnswer", status="opponent left lobby")
        if gameLobby.answPl2 is None:
            return json_response(status_=202, type="selectAnswer", status="waiting for opponent response")
        else:
            result = didFirstPLayerWon(gameLobby.answPl1, gameLobby.answPl2)
            updateThing(checker, result)
            return json_response(status_=200, type="selectAnswer", status=result,
                                 opponentAnswer=figureDecode(gameLobby.answPl2))

    elif gameLobby.lobbyPLayer2 == content['userId']:
        gameLobby.answPl2 = content['answerId']
        lobbyList[id] = gameLobby
        if gameLobby.lobbyPLayer1 is None:
            return json_response(status_=404, type="selectAnswer", status="opponent left lobby")
        if gameLobby.answPl1 is None:
            return json_response(status_=202, type="selectAnswer", status="waiting for opponent response")
        else:
            result = didFirstPLayerWon(gameLobby.answPl2, gameLobby.answPl1)
            updateThing(checker, result)
            return json_response(status_=200, type="selectAnswer", status=result,
                                 opponentAnswer=figureDecode(gameLobby.answPl1))
    else:
        return json_response(status_=401, type="selectAnswer", status="no such player in lobby")


@app.route('/exit', methods=['POST'])
def exit():
    content = request.get_json()
    checker = User.query.filter_by(username=content['userId']).first()
    if checker is None:  # проверка существует ли указанный логин
        return json_response(status_=401, type=content['type'], status="invalid login")
    try:  # проверка существует ли лобби
        id = lobbyList.index(Lobby(content['gameID'], content['userId']))
    except ValueError as ve:
        return json_response(status_=404, type=content['type'], status="no such lobby")
    gameLobby = lobbyList[id]
    if gameLobby.lobbyPLayer1 == content['userId']:
        gameLobby.lobbyPLayer1 = None
        lobbyList[id] = gameLobby
        if gameLobby.lobbyPLayer2 is None:
            lobbyList.remove(gameLobby)
        return json_response(status_=200, type=content['type'], status="successfully left lobby")
    if gameLobby.lobbyPLayer2 == content['userId']:
        gameLobby.lobbyPLayer2 = None
        lobbyList[id] = gameLobby
        if gameLobby.lobbyPLayer1 is None:
            lobbyList.remove(gameLobby)
        return json_response(status_=200, type=content['type'], status="successfully left lobby")
    return json_response(status_=200, type=content['type'], status="you are not in this lobby")


@app.route('/stats', methods=['POST'])
def stats():
    content = request.get_json()
    checker = User.query.filter_by(username=content['userId']).first()
    if checker is None:  # проверка существует ли указанный логин
        return json_response(status_=401, type=content['type'], status="invalid login")
    return json_response(status_=200, type=content['type'], wins=checker.wins, losses=checker.losses)


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
