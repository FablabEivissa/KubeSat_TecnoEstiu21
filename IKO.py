import serial
import smbus
import math
import RPi.GPIO as GPIO
import struct
import sys
import smbus2
import bme280
import time
import sqlite3
from picamera import PiCamera
import tweepy

dbconector = sqlite3.connect('gii.db')
dbcursor = dbconector.cursor()

ceunta = 1

image = 'a'

puta = 0

port = 1
address = 0x76
bus = smbus2.SMBus(port)

camera = PiCamera()

enable_debug=0
enable_save_to_file=0




ser = serial.Serial('/dev/serial0',  9600, timeout = 0)
ser.flush()
calibration_params = bme280.load_calibration_params(bus, address)

def cleanstr(in_str):
    out_str = "".join([c for c in in_str if c in "0123456789.-" ])
    if len(out_str)==0:
        out_str = "-1"
    return out_str

def safefloat(in_str):
    try:
        out_str = float(in_str)
    except ValueError:
        onut_str = -1.0
    return out_str

class GPS:

    inp=[]

    GGA=[]



    def read(self):
        while True:
            GPS.inp=ser.readline()
            if GPS.inp[:6] =='$GPGGA':
                break
            time.sleep(0.1)
        try:
            ind=GPS.inp.index('$GPGGA',5,len(GPS.inp))
            GPS.inp=GPS.inp[ind:]
        except ValueError:
            print ("")
        GPS.GGA=GPS.inp.split(",")
        return [GPS.GGA]

    def vals(self):
        if enable_debug:
            print(GPS.GGA)

        time=GPS.GGA[1]

        if GPS.GGA[2]=='':
            lat =-1.0
        else:
            lat=safefloat(cleanstr(GPS.GGA[2]))

        if GPS.GGA[3]=='':
            lat_ns=""
        else:
            lat_ns=str(GPS.GGA[3])

        if  GPS.GGA[4]=='':
            long=-1.0
        else:
            long=safefloat(cleanstr(GPS.GGA[4]))

        if  GPS.GGA[5]=='':
            long_ew=""
        else:
            long_ew=str(GPS.GGA[5])

        fix=int(cleanstr(GPS.GGA[6]))
        sats=int(cleanstr(GPS.GGA[7]))

        if  GPS.GGA[9]=='':
            alt=-1.0
        else:

            alt=str(GPS.GGA[9])
        return [time,fix,sats,alt,lat,lat_ns,long,long_ew]


    def decimal_degrees(self, raw_degrees):
        try:
            degrees = float(raw_degrees) // 100
            d = float(raw_degrees) % 100 / 60
            return degrees + d
        except:
            return raw_degrees


if __name__ == "__main__":
    g=GPS()

    gttt=open("5sec.txt", "a")

    ind=0
    while True:
        print ('foto echa')
        time.sleep(0.5)
        camera.start_preview()
        time.sleep(1)
        tiempoSINespacios = time.time()
        camera.capture('imagenescubesat/foto{}.png'.format(str(tiempoSINespacios)[0:9]), 'png')
        imagenn = 'imagenescubesat/foto{}.png'.format(str(tiempoSINespacios)[0:9])

        time.sleep(0.01)
        image = 'imagenescubesat/foto.png'


        try:
            x=g.read()
            [t,fix,sats,alt,lat,lat_ns,longitude,long_ew]=g.vals()
            data = bme280.sample(bus, address, calibration_params)


            if lat !=-1.0:
                lat = g.decimal_degrees(safefloat(lat))
                if lat_ns == "S":
                    lat = -lat

            if longitude !=-1.0:
                longitude = g.decimal_degrees(safefloat(longitude))
                if long_ew == "W":
                    longitude = -longitude

            tweeterr = 'fecha: ' + str(data.timestamp) + '\n temperatura: ' + str(data.temperature) + '\n presion: ' + str(data.pressure) + '\n humedad: ' + str(data.humidity) + '\n altitud: ' + str(alt) + '\n longitud: ' + str(longitude) + '\n latitud: ' + str(lat)
            string1="INSERT INTO donggeon(id, fecha, temperaatura, presion, humedad, lat, long, altura, imagen) VALUES('{}','{}',{},{},{},{},{},{},'{}')".format(str(ceunta),str(data.timestamp) ,str(data.temperature),str(data.pressure),str(data.humidity),str(alt),str(longitude),str(lat), image)
            string2="{} ; {} ; {} ; {} ; {} ; {} ; {} ; {} ; {} ;\n".format(str(ceunta),str(data.timestamp) ,str(data.temperature),str(data.pressure),str(data.humidity),str(alt),str(longitude),str(lat), image)
            ceunta = ceunta+1

            try:

                print("\n")
                print(string2)

            except:
                print("\n")
                print(string2)



            twitter_auth_keys = {

                "consumer_key"        : "B8AMDCkUhsRNkSAbKQ1rYaNiW",

                "consumer_secret"     : "I9pRWF7AQlJhDAvGEJ4cDr9EH8ufln1sEktOdqzPt9Pvd4K8v3",

                "access_token"        : "1431168028943716353-m4s2HRWXaxsSsqYyQxOoBeWtSn05Fn",

                "access_token_secret" : "0HRW7k2A3CfX2F19fO4dEixaoZ0y2zHu56W13ARgk3ExA"

            }
            auth = tweepy.OAuthHandler(

                    twitter_auth_keys['consumer_key'],

                    twitter_auth_keys['consumer_secret']

                    )

            auth.set_access_token(

                    twitter_auth_keys['access_token'],

                    twitter_auth_keys['access_token_secret']

                    )

            api = tweepy.API(auth)

            print(imagenn)
            media = api.media_upload(imagenn)

            tweet = tweeterr

            status = api.update_status(status=tweet, media_ids=[media.media_id])


            gttt.write(string2)
            dbcursor.execute(string1)
            dbconector.commit()


        except IndexError:
            print ("Unable to read")
        except KeyboardInterrupt:

            gttt.close()
            dbconector.close()
            print ("Exiting")
            sys.exit(0)

        time.sleep(600)
