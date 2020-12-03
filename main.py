#!/usr/bin/python3
import os, sys
import serial
import syslog
import time
import datetime
import signal
import os, sys
import matplotlib.pyplot as plt
import matplotlib.animation
import numpy as np
import time
import fcntl
import PySimpleGUI as sg
from math import sin, cos, sqrt, atan2, radians


r, w = os.pipe() 

path="roura"

def signal_handler(sig, frame):
    global closefile
    closefile=True
    print("Signal")

OFLAGS = None

def set_nonblocking(file_handle):
    """Make a file_handle non-blocking."""
    global OFLAGS
    OFLAGS = fcntl.fcntl(file_handle, fcntl.F_GETFL)
    nflags = OFLAGS | os.O_NONBLOCK
    fcntl.fcntl(file_handle, fcntl.F_SETFL, nflags)
    



set_nonblocking(r)

set_nonblocking(w)

processid = os.fork()



sg.theme('BluePurple')
Ffont='Any 15'
layout = [
	  [sg.Text('Vyska:',font=Ffont), sg.Text(size=(5,1), key='-VYSKA-',font=Ffont),sg.Text('Vyska 0:',font=Ffont), sg.Text(size=(15,1), key='-VYSKA0-',font=Ffont),sg.Button('Reset',font=Ffont)],
	  [sg.Text('Rychlost:',font=Ffont), sg.Text(size=(3,1), key='-RYCHLOST-',font=Ffont),sg.Text('Vzdalenost:',font=Ffont), sg.Text(size=(5,1), key='-VZDALENOST-',font=Ffont)],
	  [sg.Text('Satelitu:',font=Ffont), sg.Text(size=(5,1), key='-SATELITY-',font=Ffont)],
          [sg.Text('Naposledy:',font=Ffont), sg.Text(size=(10,1), key='-DATA-',font=Ffont)]
          ]

window = sg.Window('Flight Info', layout)


def getDistance(lat1,lon1,lat2,lon2):
  R = 6373.0

  lat1 = radians(float(lat1))
  lon1 = radians(float(lon1))
  lat2 = radians(float(lat2))
  lon2 = radians(float(lon2))

  dlon = lon2 - lon1
  dlat = lat2 - lat1

  a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
  c = 2 * atan2(sqrt(a), sqrt(1 - a))

  distance = R * c
  return distance*1000


def animate(i):
   
    global startY,startX,sc,ax,ruh_m,BBox,fig,plt,x,y,window,alt,Reset,start,end,destX,destY
    event, values = window.read(timeout = 100)
    end = time.time()
    
    if event == 'Reset':
            Reset = True
            print("RESET")
            
    try:
               
        msg = os.read(r, 128)
        msg= msg.decode('utf-8')
        msgSplit=msg.split("|")
        xA=msgSplit[0]
        yA=msgSplit[1]
        altitude=msgSplit[2]
        altitude0=float(altitude)-float(alt)
        speed = msgSplit[3]
        satelites = msgSplit[4]
        y=[xA]
        x=[yA]
       
        if Reset is True:
            Reset = False
            alt=altitude
            destX=y[0]
            destY=x[0]
        
        dist = "{:.2f}".format(getDistance(y[0],x[0],destX,destY))
        altitude0="{:.1f}".format(altitude0)
        
        window['-VYSKA-'].update(altitude)
        window['-VYSKA0-'].update(altitude0)
        window['-RYCHLOST-'].update(speed)
        window['-SATELITY-'].update(satelites)
        window['-VZDALENOST-'].update(dist)
        start = time.time()
     
    except BlockingIOError:
        pass
    else:
        print(len(msg), msg)
    
    el = end-start
    el = el*-1 if el<0 else el
    round(el, 1)
    el = "{:.1f}".format(el)
    
    window['-DATA-'].update(el)
    sc.set_offsets(np.c_[x,y])
    
                
                
    

if processid:#parrent
   
    print("Rodic:")
    #os.close(w)
    
    
    BBox = ((17.90527,17.92742,49.92999,49.94423))
    ruh_m = plt.imread('map.png')

    startY =17.918900 
    startX=49.938873
    
    destX=0
    destY=0

    fig, ax = plt.subplots()
    x, y = [],[]
    alt = 0
    Reset = False
    ax.imshow(ruh_m, zorder=0, extent = BBox, aspect= 'equal')
    sc = ax.scatter(x,y)

    plt.xlim(BBox[0],BBox[1])
    plt.ylim(BBox[2],BBox[3])
    
    start = time.time()
    end=start
    
    ani = matplotlib.animation.FuncAnimation(fig, animate, frames=1, interval=1000, repeat=True) 
    
    plt.show()
    
    sys.exit(0)

else:#child

    port = '/dev/ttyUSB0'
    ard = serial.Serial(port,9600,timeout=1000)
    f = open("output.gpx", "a")
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<gpx version="1.1" creator="Garmin Connect"><trk>\n')
    f.write('<name>Logger</name>\n')
    f.write('<trkseg>\n')
    signal.signal(signal.SIGINT, signal_handler)
    closefile=False

  
       
    while(1):
        msg = ard.readline()
        try:
          msg= msg.decode('utf-8')
          print (msg)
        
        except:
          print("Decode error")
          continue
          
          
        
        
        if closefile==True:
            print("Breaking")
            break
    
        msgSplit = msg.split("|")
        if len(msgSplit)!=5:
            print("Split error")
            continue
        
        altitude=float(msgSplit[0])/10
        speed = float(msgSplit[1])/10
        satelites = int(msgSplit[2])
        X=msgSplit[3].rstrip()
        Y=msgSplit[4].rstrip()
        time=str(datetime.datetime.now())
    
    
        datum = time.split(" ")
        dat=datum[0]
        cas = datum[1][0:8]

        if(altitude<5):
            continue
    
        f.write('<trkpt lon="'+ Y+ '" lat="'+X+'">\n')
        f.write('<time>'+str(dat+"T"+cas+"Z")+'</time>\n')
        f.write('<ele>'+str(altitude)+'</ele>\n')
   
        f.write('</trkpt>\n')
        
        line = X+"|"+Y+"|"+str(altitude)+"|"+str(speed)+"|"+str(satelites)
        b = str.encode(line)
        os.write(w, b)
          
        
    

    f.write('</trkseg>')
    f.write('</trk>')
    f.write('</gpx>')
    f.flush()
    f.close()
    ard.close()
          
    sys.exit(0)
  
   

