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
#~ Contact: glenlomax@gmail.com
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
from panda3d.core import *
#Sequence and parallel for intervals
from direct.interval.IntervalGlobal import *
#interpolate function parameter
from direct.interval.LerpInterval import LerpFunc
# Default classes
from Camera import Camera
from InputHandler import InputHandler
from Scene import Scene
from Interface import Interface

class World(ShowBase):  
    def __init__(self):
        #Set application properties
        wp = WindowProperties.getDefault()
        wp.setTitle(APPNAME)
        wp.setSize(APPX, APPY)
        WindowProperties.setDefault(wp)

        ShowBase.__init__(self)

        #Scene initialization
        self.scene = Scene()
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
        
        #Prepare locks (following procedures etc...)
        self.travelling = False
        self.looking = None
        self.following = None
        self.tilted = False
        self.inclined = False
        self.inclinedHard = False
        self.show_shadows = False
        self.show_stars = False
        self.show_marks = False
        
        #InitialSettings
        self.look(self.sun)
        self.follow(self.home)
    

    def toggleShadows(self) :
        if self.show_shadows :
            self.shadow_b['geom'] = self.b_map
            self.earthShadow.detachNode()
            self.moonShadow.detachNode()
            self.show_shadows = False
        else :
            self.shadow_b['geom'] = self.b_map_acti
            self.earthShadow.reparentTo(self.earth)
            self.moonShadow.reparentTo(self.moon)
            self.show_shadows = True
        self.update_shadows()
    
    def toggleStars(self) :
        if self.show_stars :
            self.star_b['geom'] = self.b_map
            self.sky.detachNode()
            self.show_stars = False
        else :
            self.star_b['geom'] = self.b_map_acti
            self.sky.reparentTo(render)
            self.show_stars = True
    
    def toggleMarks(self) :
        if self.show_marks :
            self.mark_b['geom'] = self.b_map
            nodes = [ self.earthAxMarker,
            self.sunMarker,
            self.moonMarker,
            self.earthMarker, 
            self.earth_orbitline,
            self.moon_orbitline ]
        
            for n in nodes :
                n.detachNode()

            self.show_marks = False
        else :
            self.mark_b['geom'] = self.b_map_acti
            
            self.earthAxMarker.reparentTo(self.earth)
            self.sunMarker.reparentTo(aspect2d)
            self.moonMarker.reparentTo(aspect2d)
            self.earthMarker.reparentTo(aspect2d)
            self.earth_orbitline.reparentTo(self.root_earth)
            self.moon_orbitline.reparentTo(self.root_moon)
            
            self.show_marks = True
        
    def get_curr_look_rel_pos(self) :
        return self.to_look.getPos(render)
        
    def get_curr_follow_rel_pos(self) :
        return self.to_follow.getPos(render)

    def stop_follow(self) :
        self.following = None

    def start_follow(self, new) :
        self.travelling = False
        self.following = new

    def follow(self, identity):
        #if new destination and not already trying to reach another
        if self.following != identity and not self.travelling :
            self.travelling = True
            #to be able to capture its position during sequence
            #and make updates before we actually follow it
            self.to_follow = identity
            #hide tubular shadow of followed object
            self.update_shadows()
            #stop flow of time while traveling
            slow, fast = self.scene.generate_speed_fade()
            travel = self.camera.posInterval(TRAVELLEN,
            self.get_curr_follow_rel_pos,
            blendType='easeInOut')
            #slow sim, release, travel, lock and resume speed
            sequence = Sequence(slow, Func(self.stop_follow),
            travel, Func(self.start_follow, identity), fast)
            sequence.start()
            

    def stop_look(self) :
        self.looking = None
        
    def start_look(self, new) :
        self.looking = new

    def lock_focus(self) :
        self.looking = self.to_look
        self.focus.reparentTo(self.looking)
        self.focus.setPos(0, 0, 0)

    def unlock_focus(self) :
        self.focus.wrtReparentTo(render)
        
    def look(self, identity) :
        #if new target
        if self.looking != identity :
            #store new to get actual position and update interface
            self.to_look = identity
            #stop flow of time while changing focus
            slow, fast = self.scene.generate_speed_fade()
            
            travel = self.focus.posInterval(FREEZELEN,
            self.get_curr_look_rel_pos,
            blendType='easeInOut')
            sequence = Sequence(slow, Func(self.unlock_focus),
                travel, Func(self.lock_focus), fast)
            sequence.start()

    def toggleTilt(self) :
        """earth tilt"""
        if self.tilted:
            inter = self.dummy_earth.hprInterval(TRAVELLEN,
            (0, 0, 0),
            blendType='easeIn')
            inter.start()
            self.fact_earth_b['geom'] = self.b_map
            self.tilted = False
        else :
            inter = self.dummy_earth.hprInterval(TRAVELLEN,
            (0, self.earthTilt, 0),
            blendType='easeIn')
            inter.start()
            self.fact_earth_b['geom'] = self.b_map_acti
            self.tilted = True

    def toggleIncl(self) :
        """moon realist inclination"""
        if self.inclinedHard or self.inclined :
            inter = self.dummy_root_moon.hprInterval(TRAVELLEN,
            (0, 0, 0),
            blendType='easeIn')
            inter.start()
            self.fact_moon_b['geom'] = self.b_map
            self.fact_moon2_b['geom'] = self.b_map
            self.inclined = False
            self.inclinedHard = False
        else :
            inter = self.dummy_root_moon.hprInterval(TRAVELLEN,
            (0, self.moonIncli, 0),
            blendType='easeIn')
            inter.start()
            self.fact_moon_b['geom'] = self.b_map_acti
            self.inclined = True
            
    def toggleInclHard(self) :
        """moon exagerated inclination"""
        if self.inclinedHard or self.inclined :
            inter = self.dummy_root_moon.hprInterval(TRAVELLEN,
            (0, 0, 0),
            blendType='easeIn')
            inter.start()
            self.fact_moon_b['geom'] = self.b_map
            self.fact_moon2_b['geom'] = self.b_map
            self.inclined = False
            self.inclinedHard = False
        else :
            inter = self.dummy_root_moon.hprInterval(TRAVELLEN,
            (0, self.moonIncliHard, 0),
            blendType='easeIn')
            inter.start()
            self.fact_moon2_b['geom'] = self.b_map_acti
            self.inclinedHard = True

    def update_shadows(self) :
        '''hide/show tubular shadows'''
        #show them all
        if self.show_shadows :
            self.moonShadow.reparentTo(self.moon)
            self.earthShadow.reparentTo(self.earth)
        #we shouldn't hide the same shadow if we are going to follow or 
        #already following
        if self.travelling :
            name = self.to_follow.getName()
        #shouldn't bug if we aren't following any
        elif not self.travelling and self.following != None :
            name = self.following.getName()
        else :
            name = None
        #specific hide
        if name == 'earth' :
            self.earthShadow.detachNode()
        elif name == 'moon' :
            self.moonShadow.detachNode()

#a virtual argument to bypass packing bug
def main(arg=None):
    w = World()
    w.run()

if __name__ == '__main__':
    main()
