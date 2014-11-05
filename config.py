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
""")

# PANDA DEBUGTOOLS
#~ loadPrcFileData("", "want-directtools #t")
#~ loadPrcFileData("", "want-tk #t")

#use slow realistic ephemeris for positionning planetoids
USEEPHEM = False
EPHEMSIMPLESET = 18.7399468035 #correction to align equinox in simple model

#Interface settings
PRINTTIMING = False #show Task manager statistics
INTERFACEDELAY = 0.5
BUTTONSIZE = 48, 16

#duration in sec of soft transitions
FREEZELEN = 0.2
TRAVELLEN = 1.0
SCALELEN = 2.0
MAXSPEED = 70000000

#Marker and orbitlines settings
ORBITRESOLUTION = 256
MARKERSCALE = 0.02

#multiplier to avoid working with very high numbers
multiplier = 1 / 10000.

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
UA_F = 30.
EARTHRADIUS_F = 1.
SUNRADIUS_F = 1.5
MOONRADIUS_F = 0.2
MOONAX_F = 8.
MOONINCL_F = 15. #an exagerated inclination to avoid moon eclipses in fantasist scale

ABOUTTEXT = [
        '',
        '',
        'Astrini',
        '',
        'An Open source project for educational astronomy',
        'Version 0.1',
        '',
        'Design : Roberto Casati and Glen Lomax.',
        'Based on ideas from Roberto Casati,',
        'Dov\'è il Sole di notte, Milano : Raffaello Cortina 2013,',
        'partly developed during Glen Lomax CogMaster internship,',
        'École des Hautes Études en Sciences Sociales, 2011-2012.',
        '',
        'Code : Glen Lomax',
        'Engine : Panda3D (https://www.panda3d.org)',
        'Licence : GPL v3',
        'Contact : glenlomax@gmail.com',
        'The source code is available at : https://github.com/webplate/astrini']
