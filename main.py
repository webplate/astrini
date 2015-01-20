#!/usr/bin/env python
# -*- coding: utf-8-*- 
##  
#~ Astrini. An Open source project for educational astronomy
#~ Version ...
#~ Design: Roberto Casati and Glen Lomax.
#~ Based on ideas from Roberto Casati, Dov'è il Sole di notte, Milano: Raffaello Cortina 2013, partly developed during Glen Lomax CogMaster internship, École des Hautes Études en Sciences Sociales, 2011-2012.
#~ 
#~ 
#~ Code: Glen Lomax
#~ Engine: Panda3D (https://www.panda3d.org)
#~ Licence: GPL v3
#~ Contact: glenlomax ---at--- gmail.com
#~ 
#~ 
#~ The source code is available at: https://github.com/webplate/astrini
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 3 as published by
#  the Free Software Foundation.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

#My Global config variables
#import before Showbase to set panda application
from config import *
# Import stuff in order to have a derived ShowBase extension running
# Remember to use every extension as a DirectObject inheriting class
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
# Standard library
from datetime import datetime
# Default classes
from Camera import Camera
from InputHandler import InputHandler
from Scene import Scene
from Interface import Interface

class World(ShowBase):  
    def __init__(self):
        
        if DEBUG:
            from pandac.PandaModules import ConfigPageManager
            print ConfigPageManager.getGlobalPtr()

        #Set application properties
        wp = WindowProperties.getDefault()
        wp.setTitle(APPNAME)
        wp.setSize(APPX, APPY)
        WindowProperties.setDefault(wp)

        ShowBase.__init__(self)
        
        self.initScene()
        #InitialSettings
        #~ self.scene.simul_time = datetime(2024,12,31, 8, 44)#sun rise
        #~ self.scene.simul_time = datetime(9999,12,31, 8, 44)
        self.Camera.hm.look(self.sun)
        self.Camera.hm.follow(self.home)

    def initScene(self) :
        #Scene initialization
        self.scene = Scene(self)
        
        self.earth = self.scene.sys.earth.mod
        self.moon = self.scene.sys.moon.mod
        self.sun = self.scene.sys.sun.mod
        self.home = self.scene.home
        self.focus = self.scene.focus
        
        #camera manip and mode
        self.Camera = Camera(self)
        #mouse and keyboard inputs
        self.InputHandler = InputHandler(self)
        #Interface
        self.Interface = Interface(self)


#a virtual argument to bypass packing bug
def main(arg=None):
    w = World()
    w.run()

if __name__ == '__main__':
    main()
