#!/usr/bin/env python3

from flask import Flask, render_template, redirect, request
import requests
from typing import List
from datetime import datetime
import os
import json

END_URL = os.getenv('END_URL')
COEFFICIENTS_AND_MOD = json.loads(os.getenv('COEFFICIENTS_AND_MOD')) # For example, [3, 5, 23] represents the function f(x)=3x+5 mod 23
DOMAIN = os.getenv('DOMAIN')
DAYS_TO_ALLOW = os.getenv('DAYS_TO_ALLOW') # How many days to GET endpoint until death code functions
if DAYS_TO_ALLOW:
    DAYS_TO_ALLOW = int(DAYS_TO_ALLOW)
# DAYS_TO_ALLOW = 7
ALIVE_PATH = os.getenv('ALIVE_PATH') # Path to deny allowing attempts immediately and start the countdown (optional)
# ALIVE_PATH = "i-am-alive"
DEAD_PATH = os.getenv('DEAD_PATH') # Path to start allowing attemps immediately (optional)
# DEAD_PATH = "i-am-dead"

LAST_ENDPOINT_GET: datetime = None

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    global POLYNOMIAL, LAST_ENDPOINT_GET, DAYS_TO_ALLOW
    if request.method == "POST":
        if ALIVE_PATH and DAYS_TO_ALLOW and LAST_ENDPOINT_GET and (datetime.today() - LAST_ENDPOINT_GET).days < DAYS_TO_ALLOW:
            return render_template("message.html", message="Andrew is still alive. Try again another time")
        captcha_id = request.form.get('captcha-id')
        captcha_solution = request.form.get('captcha-solution')
        v = captcha_validate(captcha_id, captcha_solution)
        if not v[0]:
            return render_template('message.html', message = "Failed captcha", attempts_left = v[1])
        try:
            coords = []
            for key in request.form:
                if 'x' == key[0]:
                    coords.append(Coordinate(int(request.form[key]), int(request.form['y' + key[1]])))
            if POLYNOMIAL.valid_combination(coords):
                return render_template("congrats.html", polynomial=POLYNOMIAL, domain=DOMAIN)
            return render_template("message.html", message="Those points weren't valid", attempts_left = v[1])
        except Exception as e:
            print(e)
            return render_template("message.html", message="Invalid data")
    captcha = captcha_get(ttl = 300)
    return render_template("index.html", polynomial = POLYNOMIAL, domain=DOMAIN, captcha_id = captcha[0], captcha_png = captcha[1])

@app.route("/<attempt_num>", methods=["GET", "POST"])
def attempt(attempt_num):
    global POLYNOMIAL, LAST_ENDPOINT_GET, DAYS_TO_ALLOW
    try:
        attempt_num = int(attempt_num)
        if request.method == "POST":
            captcha_id = request.form.get('captcha-id')
            captcha_solution = request.form.get('captcha-solution')
            v = captcha_validate(captcha_id, captcha_solution)
            if v[0]:
                if ALIVE_PATH and  LAST_ENDPOINT_GET and (datetime.today() - LAST_ENDPOINT_GET).days < DAYS_TO_ALLOW:
                    return render_template("message.html", message="Andrew is still alive. Try again another time")
                num = int(attempt_num)
                if num == POLYNOMIAL.x_zero_point:
                    return redirect(END_URL, code=302)
                return render_template('message.html', message="Incorrect guess for f(0)", attempts_left = v[1])
            return render_template('message.html', message="Failed captcha", attempts_left = v[1])
        captcha = captcha_get(ttl = 30, difficulty="hard")
        return render_template('attempt.html', captcha_id = captcha[0], captcha_png = captcha[1])
    except ValueError as e:
        print(e)
        return render_template('message.html', message="URL path must be an integer")
    except Exception as e:
        print(e)
        return render_template('message.html', message="Error ocurred")

if ALIVE_PATH and DAYS_TO_ALLOW:
    @app.route("/" + ALIVE_PATH, methods=["GET"])
    def am_alive():
        global LAST_ENDPOINT_GET
        LAST_ENDPOINT_GET = datetime.today()
        return "OK"

    if DEAD_PATH:
        @app.route("/" + DEAD_PATH, methods=["GET"])
        def am_dead():
            global LAST_ENDPOINT_GET
            LAST_ENDPOINT_GET = None
            return "OK"

def captcha_validate(captcha_id: str, captcha_solution: str) -> List:
    """ Validates a captcha and returns [success, trials_left] """
    response = requests.post(f"http://rust-captcha:8000/solution/{captcha_id}/{captcha_solution}", headers={'X-Client-ID': 'Death Code'}).json()
    if response["error_code"] != 0:
        print(f"http://rust-captcha:8000/solution/{captcha_id}/{captcha_solution}")
        raise Exception(response)
    if response["result"]["solution"] == "accepted":
        return [True, 0]
    return [False, response["result"]["trials_left"]]

def captcha_get(max_tries: int = 3, ttl: int = 120, difficulty: str = "medium") -> List[str]:
    """ Creates a captcha and returns [id, base64 encoded png] """
    response = requests.post(f"http://rust-captcha:8000/new/{difficulty}/{max_tries}/{ttl}", headers={'X-Client-ID': 'Death Code'}).json()
    if response["error_code"] != 0:
        raise Exception(response)
    return [response["result"]["id"], response["result"]["png"]]

class Coordinate:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
    
    def __repr__(self) -> str:
        return "({}, {})".format(self.x, self.y)

    def equals(self, coord):
        """ Returns whether this coordinate is equal to the other """
        return self.x == coord.x and self.y == coord.y

class Polynomial:
    def __init__(self, coefficients: List, modulo: int):
        while (coefficients[0] == 0):
            coefficients = coefficients[1:]

        self.degree = len(coefficients) - 1
        self.coefficients = coefficients
        self.modulo = modulo
        self.x_zero_point = coefficients[-1] % modulo

    def __repr__(self):
        i = 0
        s = "y="
        exponent = self.degree
        while exponent > 1:
            if s != "y=":
                s += "+"
            s += str(self.coefficients[i]) + "x^" + str(exponent)
            exponent -= 1
            i += 1
        if i != len(self.coefficients):
            if s != "y=":
                s += "+"
            s += str(self.coefficients[i]) + "x"
            i += 1
        if i != len(self.coefficients):
            if s != "y=":
                s += "+"
            s += str(self.coefficients[-1])
        return s + " mod " + str(self.modulo)

    def valid_combination(self, coordinates: List[Coordinate]) -> bool:
        """ Returns whether there are enough valid coordinates in `coordinates` to extract this polyomial """
        count = 0
        seen_coords = []
        for coord in coordinates:
            if self.valid_coord(coord) and all([not coord.equals(coordinate) for coordinate in seen_coords]):
                count += 1
                seen_coords.append(coord)
        return count >= self.degree + 1
    
    def valid_coord(self, coord: Coordinate) -> bool:
        """ Returns whether `coord` is a valid coordinate for this polynomial """
        exponent = self.degree
        coefficients = self.coefficients
        value = 0
        i = 0
        while exponent >= 0:
            value += coefficients[i] * pow(coord.x, exponent)
            exponent -= 1
            i += 1
        return value % self.modulo == coord.y

POLYNOMIAL = Polynomial(COEFFICIENTS_AND_MOD[:-1], COEFFICIENTS_AND_MOD[-1])

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8888)
