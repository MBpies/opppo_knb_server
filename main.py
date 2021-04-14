import uuid

import werkzeug
from flask import Flask, request
from flask_json import FlaskJSON, json_response
from flask_sqlalchemy import SQLAlchemy

# глобальные переменные
app = Flask(__name__)
json = FlaskJSON(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Python_proj\\knb_server\\test.db'  # !!исправьте под себя!!
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = "False"

availableLobbyList = []
lobbyList = []
availablePlayers = []


class Lobby():
    def __init__(self, lobbyId, lobbyPLayer1, lobbyPLayer2=None):  # коструктор
        self.lobbyId = lobbyId
        self.lobbyPLayer1 = lobbyPLayer1  # игрок 1 тот кто создает лобби
        self.lobbyPLayer2 = lobbyPLayer2  # игрок 2 тот кто подключается

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


# uuid.uuid4()
@app.route('/lobby', methods=['POST'])
def lobby():
    content = request.get_json()
    checker = User.query.filter_by(username=content['userId']).first()
    if checker is None:  # проверка существует ли указанный логин
        return json_response(status_=401, type=content['type'], status="invalid login")

    if content['type'] == "createLobby":
        gameLobby = Lobby(str(uuid.uuid4()), content['userId'])
        if not availablePlayers:  # нет доступных игроков
            availableLobbyList.append(gameLobby)
            return json_response(status_=202, type="createLobby", status="waiting for players",
                                 gameID=gameLobby.lobbyId)
        gameLobby.lobbyPLayer2 = availablePlayers[0]
        availablePlayers.remove(gameLobby.lobbyPLayer2)
        lobbyList.append(gameLobby)
        return json_response(status_=200, type="createLobby", status="ok", gameID=gameLobby.lobbyId)

    if content['type'] == "connectToLobby":
        if not availableLobbyList:  # нет доступных лобби
            availablePlayers.append(content['userId'])
            return json_response(status_=202, type="connectToLobby", status="waiting for lobby")
        gameLobby = availableLobbyList[0]
        availableLobbyList.remove(gameLobby)
        gameLobby.lobbyPLayer2 = content['userId']
        lobbyList.append(gameLobby)
        return json_response(status_=200, type="connectToLobby", status="ok", gameID=gameLobby.lobbyId)


@app.route('/waiting_lobby', methods=['POST'])
def waiting_lobby():
    content = request.get_json()
    checker = User.query.filter_by(username=content['userId']).first()
    if checker is None:  # проверка существует ли указанный логин
        return json_response(status_=401, type=content['type'], status="invalid login")
    if content['type'] == "createLobby":
        gameLobby = Lobby(content['gameID'], content['userId'])
        if gameLobby in availableLobbyList:  # если лобби висит в списке доступных, значит игрок все еще не найден
            return json_response(status_=202, type="createLobby", status="waiting for players",
                                 gameID=content['gameID'])
        gameLobby = lobbyList[lobbyList.index(gameLobby)]  # вытягиваем обновленное лобби с игроком
        return json_response(status_=200, type="connectToLobby", status="ok", gameID=gameLobby.lobbyId,
                             opponent=gameLobby.lobbyPLayer2)

    if content['type'] == "connectToLobby":
        if not availableLobbyList:  # нет доступных лобби
            availablePlayers.append(content['userId'])
            return json_response(status_=202, type="connectToLobby", status="waiting for lobby")
        gameLobby = availableLobbyList[0]
        availableLobbyList.remove(gameLobby)
        gameLobby.lobbyPLayer2 = content['userId']
        lobbyList.append(gameLobby)
        availablePlayers.remove(content['userId'])
        return json_response(status_=200, type="connectToLobby", status="ok", gameID=gameLobby.lobbyId,
                             opponent=gameLobby.lobbyPLayer1)


# боже незабудь пожалуйста добавить обработку выхода из очереди

@app.route('/dev', methods=['POST'])
def dev():
    print(lobbyList)
    print(availableLobbyList)
    print(availablePlayers)
    return 'huh'


# Обработка ошибок
@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400


# запуск всего этого самого
if __name__ == '__main__':
    app.run(debug=True)
