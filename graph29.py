#!/usr/bin/python
import matplotlib
matplotlib.use("Agg")

from matplotlib.dates import strpdate2num
import numpy as np
import pylab as pl
from cmath import rect, phase
import os, time, libheadstails, commands

os.nice(10)

def graphs():
  print "Loading sensor-data"
  C=np.loadtxt('/tmp/sql29.csv',delimiter=';',converters={0:strpdate2num("%Y-%m-%d %H:%M:%S")})

  # 2=13= windspeed (Gilze-Rijen)
  # 3=14= winddirection (Gilze-Rijen)
  # !=15= WindChill

  Wspd = np.array(C[:,2])
  Wdir = np.array(C[:,3])

  D = matplotlib.dates.num2date(C[:,0])

  # First modify the wind data to get a nicer graph
  d2r = (1/360.) * np.pi * 2.
  ms2kmh = 3.6
  # convert degrees to radians and m/s to km/hr
  Wdir[:] = [x*d2r for x in Wdir]
  Wspd[:] = [x*ms2kmh for x in Wspd]
  startWdir=0
  if (len(Wdir) > (12*24*2)):
    startWdir = len(Wdir) - (12*24*2)
  hrsmpls=6
  l=len(Wdir)
  last14 = Wdir[l-1]
  last13 = Wspd[l-1]
  # create intermediate arrays
  B13=Wspd
  B14=Wdir
  # make the array-lengths a multiple of <hrsmpls>
  for x in range(hrsmpls - l % hrsmpls):
    B13 = np.append(B13,last13)
    B14 = np.append(B14,last14)

  # Determine average speed and direction per 1-hour-period.
  radii=theta=width=np.array([])
  for x in range(0, l-1, hrsmpls):
    radii = np.append(radii, np.mean(B13[x:x+5]))

    # Averaging of the bearings as per:
    # http://rosettacode.org/wiki/Averages/Mean_angle
    avg_theta = phase(sum(rect(1, d) for d in B14[x:x+hrsmpls-1])/hrsmpls)
    if (avg_theta < 0):
      avg_theta = avg_theta + (2 * np.pi)
    theta = np.append(theta, avg_theta)
    w = (np.pi - abs(np.max(B14[x:x+hrsmpls-1]) - np.min(B14[x:x+hrsmpls-1]) - np.pi))
    width = np.append(width, w)

  ahpla = 0.3

  print "Windroos"
  # bar plot on a polar axis.
  # number of datapoints to show
  N = len(radii)
  ax = pl.subplot(111, polar=True)
  # 0deg position at the top
  ax.set_theta_zero_location("N")
  # 90deg position to the right; show compass bearings
  ax.set_theta_direction(-1)
  bars = ax.bar(theta, radii, width=width, bottom=0.0)
  # Use custom colors and opacity
  for r, bar in zip(range(N), bars):
    bar.set_facecolor(pl.cm.hot((r / float(N))))
    bar.set_alpha(ahpla)
  # highlight the last bar (most recent value) by giving it a different color
  bar.set_facecolor(pl.cm.cool(1.))
  bar.set_alpha(1.)
  print theta[r], radii[r], width[r]
  pl.title('Windroos')
  pl.savefig('/tmp/ubundiagd/again29dir.png')


if __name__ == "__main__":
  graphs()
