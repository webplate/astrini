# -*- coding: utf-8-*- 
#

APPNAME = 'Astrini'
APPX, APPY = 1024, 768

# Show FPS and use utf8 encoding
# noaudio...
#
from pandac.PandaModules import loadPrcFileData 
loadPrcFileData("", """
text-encoding utf8
show-frame-rate-meter 1
audio-library-name null
sync-video 1
task-timer-verbose #t
fake-view-frustum-cull 1
""")

# PANDA DEBUGTOOLS
#~ loadPrcFileData("", "want-directtools #t")
#~ loadPrcFileData("", "want-tk #t")

#use slow realistic ephemeris for positionning planetoids
USEEPHEM = False
EPHEMSIMPLESET = -18.7399468035 #correction to align equinox in simple model
MOONEPHEMSET = -44 #correction to align moon phases
MOONROTSET = -55
EARTHROTSET = -160

#Interface settings
PRINTTIMING = False #show Task manager statistics
SHOWFRUSTRUM = False
CAMERAFAR = 10.**4
INTERFACEDELAY = 0.1
BUTTONSIZE = 48, 16

#duration in sec of soft transitions
FREEZELEN = 0.2
TRAVELLEN = 1.0
SCALELEN = 2.0
MAXSPEED = 70000000.

#Marker and orbitlines settings
ORBITRESOLUTION = 256
MARKERSCALE = 0.02
AXSCALE = 0.6
SKYRADIUS = 1000.

#multiplier to avoid working with very high numbers
multiplier = 1 / 1000000.

#realistic values
#cf Wikipedia
#space
UA = 149597887 * multiplier
EARTHRADIUS = 6371 * multiplier
SUNRADIUS = 1392000 * multiplier
MOONRADIUS = 1737 * multiplier
MOONAX = 384399 * multiplier
EARTHTILT = 23.44
MOONTILT = 6.68
MOONINCL = 5.145
#time
SECONDSINDAY = 86400. 
SUNROT = 27.28 #in days
MOONROT = 27.321582
MOONREVO = MOONROT
EARTHREVO = 365.25696

#fantasist values
UA_F = UA
EARTHRADIUS_F = 5.
SUNRADIUS_F = 10.
MOONRADIUS_F = 1.
MOONAX_F = 40.
MOONINCL_F = 15. #an exagerated inclination to avoid moon eclipses in fantasist scale
