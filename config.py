# -*- coding: utf-8-*- 
#
# Show FPS and use utf8 encoding
# noaudio...
#
from pandac.PandaModules import loadPrcFileData 
loadPrcFileData("", """
text-encoding utf8
show-frame-rate-meter 1
audio-library-name null
win-size 600 400
sync-video 1
window-title Astrini
""") 

#multiplier to avoid working with very high numbers
m = 1 / 1000000.

#realistic values
#cf Wikipedia
UA = 149597887 * m
EARTHRADIUS = 6371 * 2 * m
SUNRADIUS = 1392000 * m
MOONRADIUS = 1737 * 2 * m
MOONAX = 384399 * m
SECONDSINDAY = 86400 
SUNROT = 27.28 #in days
MOONROT = 27.321582
MOONREVO = MOONROT
EARTHREVO = 365.25696
EARTHTILT = 23.44
MOONTILT = 6.68
MOONINCL = 5.14


#fantasist values
UA = 30
EARTHRADIUS = 1
SUNRADIUS = 1.5
MOONRADIUS = 0.2
MOONAX = 8
#~ MOONINCL = 0
#~ EARTHTILT = 0