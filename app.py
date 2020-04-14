from flask import Flask, Response, redirect
import carData
import flask
import json

import userData
import garageData
import reportData

from google.oauth2 import id_token
from google.auth.transport import requests

from user import User
from car import Car
from garage import Garage
from report import Report

# BE SURE TO CHANGE NAME BACK TO MAIN !!!!!

SIGN_IN_CLIENT_ID = '552110144556-qef3jf1sukp03o4khvjtcsu8kvs108tr.apps.googleusercontent.com'

app = flask.Flask(__name__)
app.secret_key = b'@U\xb0\xadf\x92f\xe8\x10\xee\xdf\x81O\x92\xb7\xe5\xca\x10rE&=\xd0\x7f'
# secret key is needed for flask sessions

def log(msg):
    """Log a simple message."""
    # Look at: https://console.cloud.google.com/logs to see your logs.
    # Make sure you have "stdout" selected.
    print('main: %s' % msg)



@app.route('/')
def root():
    return flask.redirect("/static/index.html", code=302)

@app.route('/add-garage', methods=['POST'])
def addGarage():
    log('Called addGarage') 
    garageName = flask.request.form['name']
    log(garageName)
    floorCount = flask.request.form['floorCount']
    log(floorCount)
    spaces = flask.request.form['spaces']            #Should be a string array w/ Number and then letters: 1AA 3BC etc. Let's see what happens as is
    log(spaces)
    address = flask.request.form['address']
    log(address)
    phone = flask.request.form['phone']
    log(phone)
    ownerDL = flask.request.form['ownerDL']
    log(ownerDL)
    longitude = flask.request.form['longitude']
    latitude = flask.request.form['latitude']
    log('About to create JSON')
    json_result = {}
    log('About to try')

    try:
        log('In try')
        garageData.createGarage(Garage(garageName, floorCount, spaces, address, phone, ownerDL, longitude, latitude))
        log('finished create garage')
        json_result['ok'] = True
        log('after json result')
    except Exception as exc:
        log('EXCEPTION')
        log(str(exc))
        json_result['error'] = str(exc)
    return flask.Response(json.dumps(json_result), mimetype='application/json')

@app.route('/load-garage', methods=['POST'])
def load_garage():
    name = flask.request.form['name']
    garageObj = garageData.load_garage(name)
    g = garageObj.toDict()
    log(g)
    return flask.Response(json.dumps(g), mimetype='application/json')
    

@app.route('/load-all-garages', methods=['POST'])
def load_all_garages():
    nameToQuery = flask.request.form['dl_number']
    garageArray = garageData.load_all_garages_dl(nameToQuery)
    data = []
    
    log('About to enter load-all Garages for')
    for X in garageArray:
        newDict = X.toDict().copy()
        data.append(newDict)
        log('new dict added...')
        log(json.dumps(newDict))

   
    return flask.Response(json.dumps(data), mimetype='application/json')

@app.route('/add-user', methods=['POST'])
def add_user():
    username = flask.request.form['username']
    phone = flask.request.form['phone']
    dl_no = flask.request.form['dl_no']
    json_result = {}
    try:
        log('Creating new user and adding to database')
        user_id = flask.session['user_id']
        userData.create_user(User(uid=user_id, username=username, phone=phone, dl_no=dl_no))
        json_result['ok'] = True
    except Exception as exc:
        log(str(exc))
        json_result['error'] = str(exc)
    return flask.Response(json.dumps(json_result), mimetype='application/json')

@app.route('/get-user', methods=['POST', 'GET'])
def get_user():
    user_id = flask.session['user_id']
    if user_id:
        log('Getting User ID')
        user = userData.get_user(user_id)
        u = user.to_dict()
        log(json.dumps(u))
    return flask.Response(json.dumps(u), mimetype='application/json')

@app.route('/login', methods=['POST'])
def login():
    jd = JsonData()
    user_token = flask.request.form['id_token']
    email = flask.request.form['email']
    user_id = None
    validate_user(user_token, jd)
    if len(jd.errors) != 0:
        log('there were errors logging the user in')
        return show_json(jd)
    else:
        user_id = jd.data['user_id']
        flask.session['user_id'] = user_id # store the user_id in the session to use later
        if userData.get_user(user_id):
            jd.set_data({
                    'user_in_db' : "true",
                    'user_id' : user_id,
                })
            return show_json(jd)
        else:
            jd.set_data({
                    'user_in_db' : "false",
                    'user_id' : user_id,
                })
            return show_json(jd)


# takes the token_id given by google and returns the user id for that token
# if the token is valid
def validate_user(user_token, jsonData):
    log('validating user')
    try:
        idinfo = id_token.verify_oauth2_token(user_token, requests.Request(), SIGN_IN_CLIENT_ID)

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            jsonData.errors.append('Unable to authenticate the user token')
            jsonData.errors.append('Please try logging in again')

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        user_id = idinfo['sub']
        jsonData.set_data({
                'user_id' : user_id
            })
    except ValueError:
        # Invalid token
        jsonData.errors.append('There was an error validating the user')


class PageData(object):
    def __init__(self, title):
        self.title = title
        self.errors = []
        self.p = {}

    def add_error(self, error):
        self.errors.append(error)

    def set_param(self, key, value):
        self.p[key] = value

class JsonData(object):
    def __init__(self):
        self.errors = []
        self.status = []

    def add_error(self, error):
        self.errors.append(error)

    def add_status(self, status):
        self.status.append(status)

    def set_data(self, data):
        self.data = data

def show_json(json_data):
    response_dict = {
        'errors': json_data.errors,
        'status': json_data.status,
        'data': json_data.data,
    }
    responseJson = json.dumps(response_dict)
    log('responseJson: ' + responseJson)
    return flask.Response(responseJson, mimetype='application/json')

@app.route('/add-car', methods=['POST'])
def addCar():
    make = flask.Flask.request.form['make']
    model = flask.Flask.request.form['model']
    plate_num = flask.Flask.request.form['plate_num']
    json_result = {}
    try:
        log('Creating a new Car and adding it to db')
        carData.createCar(Car(None, make, model, plate_num))
        json_result['ok'] = True
    except Exception as exc:
        log(str(exc))
        json_result['error'] = str(exc)
    return flask.Response(json.dumps(json_result), mimetype='application/json')

# this is for testing if it works, probably don't need
@app.route('/load-car')
def loadCarTest(plate_num):
        log('loading Car.')
        carObj = carData.load_car(plate_num)
        car = carObj.toDict()
        json_list = []
        for key in car:
            json_list.append(car[key])

        responseJson = json.dumps(json_list)
        return flask.Response(responseJson, mimetype='application/json')

@app.route('/add-space', methods=['POST'])
def addSpace():
    space_id = flask.request.form['space_id']
    floor = flask.request.form['floor']
    taken = flask.request.form['taken']
    json_result = {}
    try:
        log('Creating new space and adding to database')
        spaceData.createSpace(Space(None, id, floor, taken))
        json_result['ok'] = True
    except Exception as exc:
        log(str(exc))
        json_result['error'] = str(exc)
    return flask.Response(json.dumps(json_result), mimetype='application/json')

@app.route('/add-report', methods=['POST'])
def addReport():
    log('Called add-report') 
    user = flask.request.form['userBy']
    log(user)
    plate = flask.request.form['plate']
    log(plate)
    space = flask.request.form['space']
    log(space)
    dateOccured = flask.request.form['dateOccured']
    log(dateOccured)
    description = flask.request.form['description']
    log(description)
    dateReported = flask.request.form['dateSubmitted']
    log(description)
    garage = flask.request.form['garage']
    log(garage)
    log(garage)
    log('adding report for ' + dateOccured)
    json_result = {}
    try:
       
        reportData.createReport(Report(user, description, plate, garage, space, dateReported, dateOccured ))
        json_result['ok'] = True
        
    except Exception as exc:
        log('EXCEPTION')
        log(str(exc))
        json_result['error'] = str(exc)
    return flask.Response(json.dumps(json_result), mimetype='application/json')


#Loads all reports for a specfic garage
@app.route('/load-all-reports', methods=['POST'])
def loadReports():
    garageToQuery = flask.request.form['garage']
    reportArray = reportData.loadAllReports(garageToQuery)
    data = []
    
    log('About to enter load-all reports for')
    for X in reportArray:
        newDict = X.toDict().copy()
        data.append(newDict)
        log('new dict added...')
        log(json.dumps(newDict))

   
    return flask.Response(json.dumps(data), mimetype='application/json')



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)