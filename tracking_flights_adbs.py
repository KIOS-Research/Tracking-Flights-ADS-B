# -*- coding: utf-8 -*-
"""
Tracking flights adbs antenna
Copyright: (C) 2017, KIOS Research Center of Excellence
"""
# pyModeS Source: https://github.com/python-mode/python-mode
import socket
import pyModeS as pms
from datetime import datetime
import dateutil.parser
import os
import sys
import yaml
import shutil

# Load configuration file
pathname = os.path.dirname(sys.argv[0])
fullpath = os.path.abspath(pathname)
confpath = fullpath + '\\configuration_adbs.yaml'  # forwarder/
try:
    f = open(confpath, 'r')
except:
    sys.exit()
conf = yaml.load(f.read())
f.close()
pathfile = conf['pathfile']
lat_ref = conf['lat']
lon_ref = conf['lon']
rtlpath = conf['rtlpath']
adbspath = conf['adbspath']
pathfileCurrent = conf['currentAircrafts']
thresholdTime = conf['thresholdTime']
dirProject = conf['dirProject']

TCP_IP = '127.0.0.1'
TCP_PORT = 31001
BUFFER_SIZE = 488

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try: s.connect((TCP_IP, TCP_PORT))
except: pass

char1 = '*'
char2 = ';'

if os.path.exists(pathfile)==True:
   f=open(pathfile,'r')
   lines = [line.rstrip('\n') for line in f]
   historyAircrafts = lines[:-2]
   historyAircrafts.append(',')
   f.close()
else:
    historyAircrafts = []
    historyAircrafts.append('''{ "type": "FeatureCollection", ''')
    historyAircrafts.append('''"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } }, ''')
    historyAircrafts.append('\n')
    historyAircrafts.append('"features": [')

aircraft_list = {}
icao_list = []
while True:
    try: s.connect((TCP_IP, TCP_PORT))
    except: pass
    try: data = s.recv(BUFFER_SIZE)
    except: continue

    data = data[data.find(char1)+1 : data.find(char2)]
    data_length = len(data)
    try:
        dl_format = pms.df(data)
    except: break

    #CHECK MESSAGE CORRUPTED
    try: MSG = pms.hex2bin(data)
    except: pass

    if data_length > 14:
        CRC = pms.crc(MSG, encode=False)

        if int(CRC,  2) == 0:
            #print "Received Data:", data
            #print 'MSG is CORRECT'
            message = data
            type_code = pms.adsb.typecode(message)
            velocity = ''
            icao = ''
            lon = ''
            lat = ''
            callsign = ''
            altitude = ''
            position = ''
            speed = ''
            heading = ''
            vertical_speed = ''
            comma = ''
            aircraft_type = ''
            icao = str(pms.adsb.icao(message))

            #aircraft_list callsign(0),lat(1),lon(2),altitude(3),speed(4),heading(5),vertical_speed(6), aircraft_type(7), aircraft_time(8), aircraft_date(9)

            try:
                tmp = icao_list.index(icao)
            except:
                aircraft_list[icao]=['']*10

                icao_list.append(icao)
                tmp = icao_list.index(icao)

            if  9 <= type_code <= 18:
                position = pms.adsb.position_with_ref(message, lat_ref, lon_ref)
                lat = str(position[0])
                lon = str(position[1])
                position = str(position)

                aircraft_list[icao_list[tmp]][1] = lat
                aircraft_list[icao_list[tmp]][2] = lon
                aircraft_list[icao_list[tmp]][8] = datetime.now().strftime("%H:%M:%S")
                aircraft_list[icao_list[tmp]][9] = datetime.now().strftime("%Y-%m-%d")
            if  1 <= type_code <= 4:
                callsign = str(pms.adsb.callsign(message))
                aircraft_list[icao_list[tmp]][0] = callsign
                emmiter_code = pms.adsb.category(message) #aircraft category type
                if emmiter_code == 0:
                    aircraft_type = "Not Available"
                elif emmiter_code == 1:
                    aircraft_type = "Light Aircraft"
                elif emmiter_code == 2:
                    aircraft_type = "Small Aircraft"
                elif emmiter_code == 3:
                    aircraft_type = "Medium Aircraft"
                elif emmiter_code == 4:
                    aircraft_type = "High Vortex Large Aircraft"
                elif emmiter_code == 5:
                    aircraft_type = "Heavy Aircraft"
                elif emmiter_code == 6:
                    aircraft_type = "Not Available"
                elif emmiter_code == 7:
                    aircraft_type = "Reserved (Emmiter code 7)"
                elif emmiter_code == 8:
                    aircraft_type = "Reserved (Emmiter code 8)"
                elif emmiter_code == 9:
                    aircraft_type = "Reserved (Emmiter code 9)"
                elif emmiter_code == 10:
                    aircraft_type = "Rotorcraft"
                elif emmiter_code == 11:
                    aircraft_type = "Glider / Sailplane"
                elif emmiter_code == 12:
                    aircraft_type = "Lighter-than-air"
                elif emmiter_code == 13:
                    aircraft_type = "Unmanned Aircraft Vehicle"
                elif emmiter_code == 14:
                    aircraft_type = "Space / Transatmospheric Vehicle"
                elif emmiter_code == 15:
                    aircraft_type = "Ultralight / Handglider / Paraglider"
                elif emmiter_code == 16:
                    aircraft_type = "Parachutist / Skydiver"
                elif 17 <= emmiter_code <= 19:
                    aircraft_type = "Reserved (Emmiter code 17 to 19)"
                elif emmiter_code == 20:
                    aircraft_type = "Surface Emergency Vehicle"
                elif emmiter_code == 21:
                    aircraft_type = "Surface Service Vehicle"
                elif emmiter_code == 22:
                    aircraft_type = "Fixed ground or Tethered obstruction"
                elif emmiter_code == 23:
                    aircraft_type = "Cluster Obstacle"
                elif emmiter_code == 24:
                    aircraft_type = "Line Obstacle"

                aircraft_list[icao_list[tmp]][7] = aircraft_type


            if  type_code == 19:
                velocity = pms.adsb.velocity(message)
                speed = str(velocity[0]*1.852)
                heading = str(velocity[1])
                vertical_speed = str(velocity[2])
                velocity = str(velocity)

                aircraft_list[icao_list[tmp]][4] = speed
                aircraft_list[icao_list[tmp]][5] = heading
                aircraft_list[icao_list[tmp]][6] = vertical_speed
            if 5 <= type_code <= 8:
                velocity = pms.adsb.velocity(message)
                speed = str(velocity[0]*1.852)
                heading = str(velocity[1])
                vertical_speed = str(velocity[2])
                velocity = str(velocity)

                aircraft_list[icao_list[tmp]][2] = speed
                aircraft_list[icao_list[tmp]][4] = heading
                aircraft_list[icao_list[tmp]][5] = vertical_speed
            if 5 <= type_code <= 18:
                altitude = str(pms.adsb.altitude(message))
                aircraft_list[icao_list[tmp]][3] = altitude

            def getLengthIcaoInfo(icaotmp):
                u = 0
                for x in aircraft_list[icaotmp]:
                    if x != '':
                        u = u + 1
                return u

            u = getLengthIcaoInfo(icao)

            if u > 5:
                callsign = aircraft_list[icao_list[tmp]][0]
                speed = aircraft_list[icao_list[tmp]][4]
                heading = aircraft_list[icao_list[tmp]][5]
                vertical_speed = aircraft_list[icao_list[tmp]][6]
                lat = aircraft_list[icao_list[tmp]][1]
                lon = aircraft_list[icao_list[tmp]][2]
                altitude = aircraft_list[icao_list[tmp]][3]
                aircraft_type = aircraft_list[icao_list[tmp]][7]
                aircraft_date = aircraft_list[icao_list[tmp]][9]
                aircraft_time = aircraft_list[icao_list[tmp]][8]

                try:
                    historyAircrafts.append('''{ "type": "Feature", "properties": {  "ICAO": ''' + '"' + str(icao) + '"' + ', "Date": ' + '"' + aircraft_date + '"' + ', "Time": ' + '"' + aircraft_time + '"' + ', "Callsign": ' + '"'+callsign+'"' + ', "Category": ' + '"'+aircraft_type+'"' + ', "Speed": ' + '"'+speed+'"' +
                                   ', "Heading": ' + '"'+heading+'"' + ', "Vertical Speed": ' + '"'+vertical_speed+'"' + ', "lat": '+ '"'+lat+'"' + ', "lon": ' + '"'+lon+'"' +
                                   ', "Altitude": ' + '"'+altitude+'"'+',}, "geometry": { "type": "Point",  "coordinates": '+ '['+lon+','+ lat+']')
                except: continue
                historyAircrafts.append('}\n }')
                f = open(pathfile, "w")
                for line in historyAircrafts:
                    f.write(line)
                f.write('\n]\n}\n')
                historyAircrafts.append(',\n')
                f.close()

                try:
                    shutil.copyfile(pathfile, dirProject + "\\Historic Aircrafts.geojson")
                except:
                    pass

            if historyAircrafts != []:
                currentAircrafts = []
                currentAircrafts.append('''{ "type": "FeatureCollection", ''')
                currentAircrafts.append(
                    '''"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } }, ''')
                currentAircrafts.append('\n')
                currentAircrafts.append('"features": [')
                currentNo = 0
                for ic in aircraft_list:
                    pp = getLengthIcaoInfo(ic)
                    if pp > 5:
                        currentNo = 1
                        callsign = aircraft_list[ic][0]
                        speed = aircraft_list[ic][4]
                        heading = aircraft_list[ic][5]
                        vertical_speed = aircraft_list[ic][6]
                        lat = aircraft_list[ic][1]
                        lon = aircraft_list[ic][2]
                        altitude = aircraft_list[ic][3]
                        aircraft_type = aircraft_list[ic][7]
                        aircraft_time = aircraft_list[ic][8]
                        aircraft_date = aircraft_list[ic][9]
                        date1 = datetime.now()
                        date2 = dateutil.parser.parse(aircraft_date + ' ' + aircraft_time, fuzzy=True)
                        try:
                            if (abs((date1 - date2).total_seconds()) < thresholdTime):
                                    currentAircrafts.append(
                                        '''{ "type": "Feature", "properties": {  "ICAO": ''' + '"' + str(
                                            ic) + '"' + ', "Date": ' + '"' + aircraft_date + '"' + ', "Time": ' + '"' + aircraft_time + '"' + ', "Callsign": ' + '"' + callsign + '"' + ', "Category": ' + '"' + aircraft_type + '"' + ', "Speed": ' + '"' + speed + '"' +
                                        ', "Heading": ' + '"' + heading + '"' + ', "Vertical Speed": ' + '"' + vertical_speed + '"' + ', "lat": ' + '"' + lat + '"' + ', "lon": ' + '"' + lon + '"' +
                                        ', "Altitude": ' + '"' + altitude + '"' + ',}, "geometry": { "type": "Point",  "coordinates": ' + '[' + lon + ',' + lat + ']')
                                    currentAircrafts.append('}\n }')
                                    currentAircrafts.append(',\n')
                        except: pass
                if currentNo == 0:
                    currentAircrafts.append('''{ "type": "FeatureCollection", ''')
                    currentAircrafts.append(
                        '''"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } }, ''')
                    currentAircrafts.append('\n')
                    currentAircrafts.append('"features": [')
                try:
                    fcur = open(pathfileCurrent, "w")
                    for liness in currentAircrafts:
                        fcur.write(liness)
                    fcur.write('\n]\n}\n')
                    currentAircrafts.append(',\n')
                    fcur.close()
                except:
                    pass
            else:
                break
s.close()