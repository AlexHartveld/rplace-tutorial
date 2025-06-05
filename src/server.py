import flask
from flask import request, redirect, send_file
from PIL import Image, ImageColor
from io import BytesIO
from canvas import Canvas
from database import Database
import random

address = "0.0.0.0"
port = 8888

app = flask.Flask(__name__)
canvas = Canvas(2, 2)
db = Database()

@app.route('/signin', methods=['GET'])
def signInPage():
    return flask.render_template(
        'auth/signin.html'
    )

@app.route('/signin', methods=['POST'])
def signIn():
    if not checkDDOS(request.remote_addr, 5000):
        return flask.render_template(
            'auth/signin.html',
            verdict="You will not ddos my server."
        )

    login = request.form.get('login')
    password = request.form.get('password')
    if (not login) or (not password):
        return flask.render_template(
            'auth/signin.html',
            verdict="Fields are incorrect."
        )

    db_response = db.getUser(login)

    if not db_response:
        return flask.render_template(
            'auth/signin.html',
            verdict="No user found."
        )

    db_response = db_response[0]
    
    if db_response[2] != password:
        return flask.render_template(
            'auth/signin.html',
            verdict="Wrong password."
        )

    response = flask.make_response(
        redirect('/index')
    )
    hash_ = db.getHash(login, password)
    response.set_cookie("token", hash_, max_age=3600)

    return response

@app.route('/signup', methods=['GET'])
def signUpPage():
    return flask.render_template(
        'auth/signup.html'
    )

@app.route('/signup', methods=['POST'])
def signUp():
    if not checkDDOS(request.remote_addr, 5000):
        return flask.render_template(
            'auth/signup.html',
            verdict="You will not ddos my server."
        )

    login = request.form.get('login')
    password = request.form.get('password')

    if not login or not password:
        return flask.render_template(
            'auth/signup.html',
            verdict="Fields are incorrect."
        )

    db_response = db.getUser(login)
    if db_response:
        return flask.render_template(
            'auth/signup.html',
            verdict="User with such login already exists."
        )

    db.addUser(login, password)

    response = flask.make_response(
        redirect('/index')
    )

    hash_ = db.getHash(login, password)
    response.set_cookie("token", hash_, max_age=3600)

    return response

@app.route('/index')
@app.route('/')
def index():
    return flask.render_template(
        'index.html'
    )

import time

def current_milli_time():
    return round(time.time() * 1000)

lastRequestTime = {}
def checkDDOS(address, timelimit):
    t = current_milli_time()
    if address in lastRequestTime:
        prev = lastRequestTime[address]
        if (t - prev < timelimit):
            lastRequestTime[address] = t
            return False

    lastRequestTime[address] = t
    return True

@app.route('/submit', methods=['POST'])
def paint():
    if not checkDDOS(request.remote_addr, 200):
        return "NO"

    data = request.json
    if not 'token' in data:
        print('wrong token')
        return "Wrong token"

    id = db.isKnownToken(data['token'])
    if id == None:
        print('unknown user')
        return "Unknown user"
    
    db.addPaintedCell(id)

    canvas.set_cell(data['x'], data['y'], ImageColor.getcolor(data['color'], "RGB"))
    return "OK"

@app.route('/pixel', methods=['GET'])
def getpixel():
    args_dict = request.args.to_dict()
    print(args_dict)
    color = canvas.get_cell(int(args_dict['x']), int(args_dict['y']))
    return str(color)

@app.route('/pixel', methods=['POST'])
def setpixel():
    data = request.json
    try:
        x = int(data['x'])
        y = int(data['y'])
        color_hex = data['color']
        color_rgb = ImageColor.getcolor(color_hex, "RGB")
    except:
        return "please provide coordinates and a color", 400
    
    
    canvas.set_cell(data['x'], data['y'], color_rgb)

    return f"{x}, {y}, {color_rgb}", 200


if __name__ == '__main__':
    app.run(address, port, debug=True)