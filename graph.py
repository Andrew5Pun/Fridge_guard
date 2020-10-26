# Written by Andrew Pun 2020

import plotly.express as px
from datetime import datetime
import plotly.io as pio
import mysql.connector
import pandas as pd
import os
import sys

arguments = sys.argv # uncomment

# credentials
mysql_user = '[user]' # user
mysql_password = '[password]' # password
mysql_host = '[IP of sql server]' # 127.0.0.1
mysql_database = '[database name]' # my_db
mysql_port = '[port]' # 3306

# set probe id from arguments
probe_id = arguments[1]
user_id = arguments[2]
pastDays = arguments[3]

# get working directory
WDir = "[directory of where you want htmls to be]" # /var/www/example.com/

temperatureDir = "TemperatureReading" + probe_id + ".html"

# change directory
os.system("cd " + WDir)

filePath = os.path.join(WDir, user_id)

print(filePath)

# if user_id does not exist then create directory
if not os.path.exists(filePath):
    os.makedirs(filePath)
    print("created directory " + filePath + " successfully")

# path of file to write to
filePath = os.path.join(WDir, user_id, temperatureDir)

#print(filePath)

# connect to database
cnx = mysql.connector.connect(user=mysql_user, password=mysql_password,
                                  host=mysql_host,
                                  database=mysql_database, port=mysql_port)

# set cursor
mycursor = cnx.cursor()

# get temperature ranges and nicknames from probe_id number
sql1 = ("SELECT min_temp, max_temp, nickname FROM probes WHERE probe_id =%s")
val = (probe_id,)
mycursor.execute(sql1, val)
result_set = mycursor.fetchall()

# store values
tempMin = result_set[0][0]
tempMax = result_set[0][1]
nickname = result_set[0][2]

#print(result_set)

# get log_date and temperature from probe number
lt = ("SELECT MAX(log_date) AS 'Current log_date' FROM temperatures WHERE probe_id =%s")
val = (probe_id,)
mycursor.execute(lt, val)
result_set = mycursor.fetchall()

current_date = result_set[0][0]

#print(current_date)

# SELECT values from past few days
lt = ("SELECT log_date, temperature FROM temperatures WHERE probe_id =%s AND log_date <= %s AND log_date >= DATE_SUB(%s, INTERVAL %s DAY)")

val = (probe_id, current_date, current_date, pastDays)
mycursor.execute(lt, val)
result_set = mycursor.fetchall()

if len(result_set) > 0:

    #print(result_set[1][0])

    date = []
    temperature = []

    for log in result_set:
        date.append(log[0])
        temperature.append(log[1])

    fig = px.line(x=date, y=temperature)

    fig.update_traces(mode="markers+lines")  # make dots more visible

    # axes labels and title
    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Temperature (°C)')
    fig.update_layout(title_text=('Temperature graph for ' + nickname))

    # hover template layout
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=15,
        )
    )
    fig.update_traces(hovertemplate='<b>Date:</b> %{x}<br><b>Temperature:</b> %{y} °C')

    # add area
    fig.add_shape(
        type="rect",
        yref="y",
        xref="paper",
        y0=tempMax,
        x0=0,
        y1=tempMin,
        x1=1,
        fillcolor="rgb(124, 223, 124)",
        opacity=0.6,
        layer="below",
        line_width=0,
    )

    fig.show()

    pio.write_html(fig, file=filePath, auto_open=False)

else:

    Html_file = open (filePath, "w")
    Html_file.write("No data in that range.")
    Html_file.close()

cnx.commit()

cnx.close()
