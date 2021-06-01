# Import relevant modules
import mysql.connector
import json
import urllib.request
from flask import Flask, render_template, request, redirect

fileName = "missionIDs.txt"
file = open(fileName,'r')
IDs = []
for line in file:
    line = line.rstrip('\n')
    IDs.append(line)


# URL with Stratostar JSON data
url = "https://tracking.stratostar.net/missions/" + IDs[0] + "/payloaddump"

def entireScript(currentURL): 
    try:
        global packetLabels
        global plotPacketLabels
        global allPackets
        global allPacketsLength
        global allPlotPackets

        response = urllib.request.urlopen(url)
        data = json.loads(response.read()) # Save Stratostar JSON data as list var

        allPackets = []
        allPlotPackets = []
        allPacketsLength = 0

        packetLabels = ["Packet Time", "Latitude", "Longitude",
                        "Alt (ft)", "Temp (F)", "Pressure (PSI)", "Comms ID", "Payload 1 ID",
                        "Payload 1 Status Bits ", "Payload 1 Sensor 1", "Payload 1 Sensor 2",
                        "Payload 1 Sensor 3", "Payload 1 Sensor 4", "Payload 2 Status Bits", 
                        "Payload 2 Sensor 1", "Payload 2 Sensor 2", "Payload 2 Sensor 3", "Payload 2 Sensor 4"]

        plotPacketLabels = ["Year", "Month", "Day", "Hour", "Minute", "Second", "Latitude", "Longitude",
                            "Altitude (ft)", "Temperature (F)", "Pressure (PSI)", "Payload 1 Status Bits ",
                            "Payload 1 Sensor 1", "Payload 1 Sensor 2", "Payload 1 Sensor 3",
                            "Payload 1 Sensor 4", "Payload 2 Status Bits", "Payload 2 Sensor 1",
                            "Payload 2 Sensor 2", "Payload 2 Sensor 3", "Payload 2 Sensor 4"]

        for i in data: # Loop through each packet listed on API
            currentPayloadData = i['payload'] # Save current UMN data packet as var

            if(len(currentPayloadData)>=43):
                temp = i['temperature']
                pres = i['pressure']
                lat = round(i['latitude'],2) # Round values given by API to two data 
                lon = round(i['longitude'],2)
                alt = round(i['altitude'],2)

                rawTime = i['time']

                year = int(rawTime[:rawTime.index('-')])
                month = int(rawTime[rawTime.index('-')+1:rawTime.index('-', rawTime.index('-')+1)])
                day = int(rawTime[rawTime.index('-', rawTime.index('-')+1)+1:rawTime.index('T')])
                hour = int(rawTime[rawTime.index('T')+1:rawTime.index(':')])
                min = int(rawTime[rawTime.index(':')+1:rawTime.index(':',rawTime.index(':')+1)])
                sec = int(rawTime[rawTime.index(':',rawTime.index(':')+1)+1:rawTime.index('.')])
                usefulTime = str(month) + "/" + str(day) + "/" + str(year) + " " + str(hour) + ":" + str(min) + ":" + str(sec) + (" CST") 

                letter = bytes.fromhex(currentPayloadData[0:2]).decode('utf-8') # First two HEX values indicate team (A for UMN)
                payloadID1 = currentPayloadData[2:4] # two HEX values following UMN ID indicate first subteam 
                status1 = bin(int(currentPayloadData[4:6], 16))[2:].zfill(8) # 8 bits indicating first subteam payload health
                data1 = []
                data2 = []
                for k in range(4):
                    data1.append(int(currentPayloadData[(6+4*k):(10+4*k)], 16)) # Pulling each subteam's 4 integer values
                    data2.append(int(currentPayloadData[(26+4*k):(30+4*k)], 16))
                payloadID2 = currentPayloadData[22:24] # two HEX values following UMN ID indicate first subteam
                status2 = bin(int(currentPayloadData[24:26], 16))[2:].zfill(8) # 8 bits indicating second subteam payload health 

                packet = [usefulTime, lat, lon, alt, temp, pres, letter,
                        payloadID1, int(status1), data1[0], data1[1], data1[2], data1[3],
                        payloadID2, int(status2), data2[0], data2[1], data2[2], data2[3]]

                plotPacket = [year, month, day, hour, min, sec, lat, lon, alt, temp, pres,
                            int(status1), data1[0], data1[1], data1[2], data1[3], int(status2),
                            data2[0], data2[1], data2[2], data2[3]]
                
                allPackets.append(packet)
                allPlotPackets.append(plotPacket)
                allPacketsLength += 1
    except:
        pass # If the new inputted Mission ID is invalid, just use the previous ID.

def readDB():
    global allPlotPackets2
    global plotPacketLabels2
    global allPackets2
    global allPacketsLength2
    global packetLabels2

    packetLabels2 = ["ID", "Year", "Month", "Day", "Hour", "Minute", "Second", "Latitude", "Longitude", "Altitude (ft)", "Alt Est (ft)", "Int Temp (F)", "Ext Temp (F)", "altimeter Temp (F)", "Pressure (PSI)", "Sensor1", "Sensor2", "Sensor3"]
    plotPacketLabels2 = ["Year", "Month", "Day", "Hour", "Minute", "Second",  "Latitude", "Longitude", "Altitude (ft)", "Alt Est (ft)", "Int Temp (F)", "Ext Temp (F)", "Altimeter Temp (F)", "Pressure (PSI)", "Sensor1", "Sensor2", "Sensor3"]
    allPlotPackets2 = []
    allPackets2 = []

    fileName = "sensitiveInfo.txt" # name of file containing usernames, passwords, etc.

    file = open(fileName, 'r') # open file for reading

    for line in file: # read file line by line

        line = line.rstrip('\n')
        if line.startswith('user:'):
            user = line[line.index(':')+1:] # read in all characters beyond semicolon
            user= user.replace(" ", "") # Remove spaces before and after word, if there are any

        if line.startswith('password:'):
            password = line[line.index(':')+1:]
            password = password.replace(" ", "")

        if line.startswith('host:'):
            host = line[line.index(':')+1:] # read in all characters beyond semicolon
            host= host.replace(" ", "") # Remove spaces before and after word, if there are any

        if line.startswith('database:'):
            database = line[line.index(':')+1:]
            database = database.replace(" ", "")
    
    connection = mysql.connector.connect(host= host, database= database, user=user, password=password)

    sql_select_Query = "select * from sensorDataOne ORDER BY id DESC"
    cursor = connection.cursor()
    cursor.execute(sql_select_Query)
    records = cursor.fetchall()
    allPacketsLength2 = len(records)

    for line in records:
        try:
            plotPacket = [float(line[2]), float(line[3]), float(line[4]), float(line[5]), float(line[6]),
                        float(line[7]), float(line[8]), float(line[9]), float(line[10]), float(line[11]),
                        float(line[12]), float(line[13]), float(line[14]), float(line[15]), float(line[16]), float(line[17]), float(line[18])]
            
            if(int(line[3])<=12 and int(line[3])>=1):
                allPlotPackets2.append(plotPacket)
                allPackets2.append(line[1:])
            else:
                allPacketsLength2 = allPacketsLength2 - 1
        except:
            allPacketsLength2 = allPacketsLength2 - 1

entireScript(url)

application = Flask(__name__) #Create flask instance

@application.route("/") # Indicates path of the html file
def home():
    # Render front-end page and pass in the following variables to the index.html file
    return render_template("index.html", currentURL = url, IDs = IDs, allPackets = allPackets,
        packetLabels = packetLabels, allPacketsLength = allPacketsLength,
        allPlotPackets = allPlotPackets, plotPacketLabels = plotPacketLabels)

@application.route('/newMissionID', methods = ['POST'])
def signup():
    global url
    url = "https://tracking.stratostar.net/missions/" + request.form['missionID'] + "/payloaddump"
    entireScript(url)
    return redirect('/')

@application.route('/radio')
def radioz():
    readDB()
    return render_template("index2.html", allPackets2 = allPackets2,
        packetLabels2 = packetLabels2, allPacketsLength2 = allPacketsLength2,
        allPlotPackets2 = allPlotPackets2, plotPacketLabels2 = plotPacketLabels2)

@application.route('/radio<num>')
def radiozz(num):
    readDB()
    allPacketsLength2 = int(num)
    return render_template("index2.html", allPackets2 = allPackets2,
        packetLabels2 = packetLabels2, allPacketsLength2 = allPacketsLength2,
        allPlotPackets2 = allPlotPackets2, plotPacketLabels2 = plotPacketLabels2)

@application.route('/refreshStuff', methods = ['POST'])
def refreshStuff():
    readDB()
    return redirect('/')

if __name__ == "__main__": # Run flask application if this is the main program being run by an interpreter
    application.run(ssl_context='adhoc')