#!flask/bin/python

# Written by Andrew Pun 2020

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

import subprocess
from flask import Flask, jsonify
from flask import abort
from flask import request
from flask import make_response
from datetime import datetime
import os
import mysql.connector

# credentials
mysql_user = '[user]' # user
mysql_password = '[password]' # password
mysql_host = '[IP of sql server]' # 127.0.0.1
mysql_database = '[database name]' # my_db

api_ip = '[IP of API]' # example.com:5000

users_route = '[route of users api]' # /api/users
temp_route = '[route of temps api]' # /api/temp

app = Flask(__name__)

temps = [
    {
        'id': 1,
        'temperature': -999.9999,
        'comment': 'default api value',
        'serial': '28-00000notreal',
        'logdate': '1991-01-01'
    }
]

users = [
    {
        'id': 1,
        'name': 'userdef',
        'comment': 'default api value',
        'serial': '28-00000notreal'
    }
]


@auth.get_password
def get_password(username):

    cnx = mysql.connector.connect(user=mysql_user, password=mysql_password,
                                  host=mysql_host,
                                  database=mysql_database)

    mycursor = cnx.cursor()

    username = username.strip()

    sql1 = "SELECT name, password FROM users WHERE name =%s"
    val = (username,)
    mycursor.execute(sql1, val)
    result_set = mycursor.fetchall()

    print(sql1)

    if len(result_set) > 0:
        return result_set[0][1]
    else:
        print(username + " tried to access with invalid password")
    return None


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


@app.route(temp_route, methods=['GET'])
@auth.login_required
def get_temps():
    return jsonify({'temps': temps})


@app.route(temp_route + '<int:temp_id>', methods=['GET'])
@auth.login_required
def get_temp(temp_id):
    temp = [temp for temp in temps if temp['id'] == temp_id]
    if len(temp) == 0:
        abort(404)
    return jsonify({'temp': temp[0]})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)


@app.route(users_route, methods=['POST'])
@auth.login_required
def create_probe():
    if not request.json or not 'name' in request.json:
        abort(400)

    cnx = mysql.connector.connect(user=mysql_user, password=mysql_password,
                                  host=mysql_host,
                                  database=mysql_database)
    mycursor = cnx.cursor()

    user = {

        'id': users[-1]['id'] + 1,
        'name': request.json.get('name', ""),
        'comment':request.json.get('comment', ""),
        'serial': request.json.get('serial', "")

    }
    users.append(user)

    name = user['name']
    serial = user['serial']
    comment = user['comment']

    sql1 = ("SELECT user_id FROM users WHERE name =%s")
    val = (name,)
    mycursor.execute(sql1, val)
    result_set = mycursor.fetchall()

    if len(result_set) > 0:
        user_id = result_set[0][0]
        print(user_id)

        sql2 = ("SELECT serial FROM probes WHERE serial =%s")
        val = (serial,)
        mycursor.execute(sql2, val)
        result_set = mycursor.fetchall()

        if len(result_set) == 0:
            sql2 = "INSERT INTO probes (user_id, serial, comment) VALUES (%s, %s, %s)"
            val = (user_id, serial, comment)
            mycursor.execute(sql2, val)

            print("Created probe " + serial + " for user " + str(user_id) + " successfully.")

        else:
            print("Probe: " + serial + " already exists!")
    else:
        print("User: " + name + " does not exist!")

    cnx.commit()
    cnx.close()
    return jsonify({'user': user}), 201


@app.route(temp_route, methods=['POST'])
@auth.login_required
def create_temp():

    # temporary run graphnew in python

    if not request.json or not 'temperature' in request.json:
        abort(400)

    cnx = mysql.connector.connect(user=mysql_user, password=mysql_password,
                                  host=mysql_host,
                                  database=mysql_database)
    mycursor = cnx.cursor()

    temp = {

        'id': temps[-1]['id'] + 1,
        'temperature': request.json['temperature'],
        'comment': request.json.get('comment', ""),
        'serial': request.json.get('serial', ""),
        'logdate': datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    }
    temps.append(temp)



    # get values from temp entry
    temperature = temp['temperature']
    comment = temp['comment']
    serial = temp['serial']
    logdate = temp['logdate']

    print(comment)

    # get probe id from serial number
    sql1 = ("SELECT probe_id, user_id, tokens FROM probes WHERE serial =%s")
    val = (serial,)
    mycursor.execute(sql1, val)
    result_set = mycursor.fetchall()

    probe_id = result_set[0][0]
    user_id = result_set[0][1]
    tokens = result_set[0][2]

    if tokens > 0:

        # insert value
        sql2 = "INSERT INTO temperatures (probe_id, temperature, log_date, comment) VALUES (%s, %s, %s, %s)"
        val = (probe_id, temperature, logdate, comment)
        mycursor.execute(sql2, val)

        cnx.commit()

        print(sql2, val)

        # get min and max temperatures
        sql1 = ("SELECT min_temp, max_temp, days FROM probes WHERE probe_id =%s")
        val = (str(probe_id),)
        mycursor.execute(sql1, val)
        result_set = mycursor.fetchall()

        tempMin = -999999
        tempMax = 999999
        probe_days = 2

        if len(result_set[0]) > 1:
            tempMin = result_set[0][0]
            tempMax = result_set[0][1]
            probe_days = result_set[0][2]

        sql1 = ("UPDATE probes SET tokens = tokens - 1, total_requests = total_requests + 1 WHERE probe_id =%s")
        val = (str(probe_id),)

        mycursor.execute(sql1, val)
        cnx.commit()

        print("Probe: " + serial + " has logged its temperature successfully. It has " + str(tokens - 1) + " tokens left.")


        # get email
        sql1 = ("SELECT email FROM users WHERE user_id =%s")
        val = (str(user_id),)
        mycursor.execute(sql1, val)
        result_set = mycursor.fetchall()

        print(result_set)

        if tempMin <= float(temperature) and float(temperature) <= tempMax:

            print("Temperature is in range.")
            print("Temperature is " + temperature)

        else:

            print("WARNING: Temperature is out of range!")
            print("Temperature is " + temperature)
            print("Minimum temperature is " + str(tempMin) + ".")
            print("Maximum temperature is " + str(tempMax) + ".")

            if result_set[0][0]:
                email = result_set[0][0]
                probe_warn(tempMin, tempMax, serial, temperature, email)

        subprocess.Popen(["python", "[path to graph.py]", str(probe_id), str(user_id), str(probe_days)])

    else:

        print("Probe " + serial + "has run out of tokens! It has " + str(tokens) + " tokens left.")

    cnx.commit()
    cnx.close()

    return jsonify({'temp': temp}), 201


def probe_warn(tempMin, tempMax, serial, temperature, email):

    emailMsg = "Min: " + str(tempMin) + " Max: " + str(tempMax) + " Serial: " + str(serial) + " Temperature: " + str(temperature) + " Email: " + email
    print(emailMsg)


if __name__ == '__main__':
    app.run(host=api_ip, debug=True)
