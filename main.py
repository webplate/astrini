#!/usr/bin/env python
# -*- coding: utf-8-*- 
##  
#~ Astrini. An Open source project for educational astronomy
#~ Version 1.0
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
from direct.gui.DirectGui import *
from panda3d.core import *
# Task declaration import 
from direct.task import Task
#Sequence and parallel for intervals
from direct.interval.IntervalGlobal import *
#interpolate function parameter
from direct.interval.LerpInterval import LerpFunc
# Default classes used to handle input and camera behaviour
# Useful for fast prototyping
from Camera import Camera
from InputHandler import InputHandler
#Drawing functions
import graphics
#a pypi package to get precise planetoids positions
import astronomia.calendar as calendar
import astronomia.lunar as lunar
import astronomia.planets as planets
#Misc imports
from math import radians, degrees, tan
from datetime import datetime, timedelta


class World(ShowBase):  
    def __init__(self):
        #Set application properties
        wp = WindowProperties.getDefault()
        wp.setTitle(APPNAME)
        wp.setSize(APPX, APPY)
        WindowProperties.setDefault(wp)
        
        ShowBase.__init__(self)

        #starting all base methods
        self.Camera = Camera(self)
        self.InputHandler = InputHandler(self)
        
        #default config when just opened
        self.Camera.mm.showMouse()
        self.Camera.setUtilsActive()
        self.mainScene = render.attachNewNode("mainScene")
        
        #load fonts
        self.condensed_font = loader.loadFont('fonts/Ubuntu-C.ttf')
        self.mono_font = loader.loadFont('fonts/UbuntuMono-R.ttf')

        #Scene initialization
        self.initEmpty()
        self.initCamera()
        self.initScene()
        #Interface
        self.loadInterface()
        
        #Prepare locks (following procedures etc...)
        self.travelling = False
        self.paused = False
        self.reverse = False
        self.looking = None
        self.following = None
        self.tilted = False
        self.inclined = False
        self.inclinedHard = False
        self.realist = False
        # Add Tasks procedures to the task manager.
        #low priority to prevent jitter of camera
        self.taskMgr.add(self.lockTask, "lockTask", priority=25)
        self.taskMgr.add(self.timeTask, "timeTask")
        #do not update interface every frame (no use slowdown)
        self.taskMgr.doMethodLater(INTERFACEDELAY, self.interfaceTask, "interfaceTask")
        self.taskMgr.add(self.positionTask, "positionTask")
        
        #InitialSettings
        self.look('sun')
        self.follow('home')
        self.simulTime = datetime(2014, 3, 20)

    def initEmpty(self) :
        #Create the dummy nodes
        self.homeSpot = render.attachNewNode('homeSpot')
        self.focusSpot = render.attachNewNode('focusSpot')
        #Compute camera-sun distance from fov
        fov = self.Camera.getFov()[0]
        margin = UA / 3
        c_s_dist = (UA + margin) / tan(radians(fov/2))
        self.homeSpot.setPos(0, -c_s_dist,UA/3)
        #init focus is on the sun
        self.focusSpot.setPos(0, 0, 0)

    def initScene(self) :
        self.simulSpeed = 1
        self.time_is_now
        
        #computations of planetoids positions
        self.moon_coord = lunar.Lunar()
        self.system_coord = planets.VSOP87d()
        
        #variables to control the relative speeds of spinning and orbits in the
        #simulation
        #Number of days a full rotation of Earth around the sun should take
        self.yearscale = EARTHREVO

        self.orbitscale =  UA              #Orbit scale
        self.sizescale = EARTHRADIUS              #Planet size scale
        self.sunradius = SUNRADIUS
        self.earthTilt = EARTHTILT
        self.moonTilt = MOONTILT
        self.moonIncli = MOONINCL
        self.moonIncliHard = MOONINCLHARD
        
        base.setBackgroundColor(0, 0, 0)    #Set the background to black
        self.loadPlanets()                #Load and position the models
        self.loadMarkers()
        self.drawOrbits()
        self.initLight()                # light the scene


    def initLight(self):
        #invisible spotlight to activate shadow casting (bypass bug)
        self.unspot = render.attachNewNode(Spotlight("Invisible spot"))
        self.unspot.setPos(0,0,self.orbitscale)
        self.unspot.setHpr(0,90,0)
        #~ self.unspot.node().setScene(render)
        #~ self.unspot.node().setShadowCaster(True, 2048, 2048)
        #~ self.unspot.node().showFrustum()
        # a mask to define objects unaffected by light
        #~ self.unspot.node().setCameraMask(BitMask32.bit(1)) 
        #~ self.light.node().setExponent(0.1)#illuminate most of fov
        #~ self.unspot.node().getLens().setFov(1)
        #~ self.light.node().getLens().setFilmSize(200)
        #~ self.light.node().getLens().setNearFar(self.sunradius,self.orbitscale * 2)
        self.unspot.node().getLens().setNearFar(0,0)
        render.setLight(self.unspot)
        
        #the light on the earth system
        self.light = render.attachNewNode(DirectionalLight("SunLight"))
        self.light.setPos(0,0,0)
        self.light.node().setScene(render)
        self.light.node().setShadowCaster(True, 2048, 2048)
        #~ self.light.node().showFrustum()
        # a mask to define objects unaffected by light
        self.light.node().setCameraMask(BitMask32.bit(0)) 
        #~ self.light.node().setExponent(0.1)#illuminate most of fov
        #~ self.light.node().getLens().setFov(5)
        self.light.node().getLens().setFilmSize((2*MOONAX,MOONAX/2))
        self.light.node().getLens().setNearFar(self.orbitscale - MOONAX, self.orbitscale + MOONAX)
        render.setLight(self.light)

        self.alight = render.attachNewNode(AmbientLight("Ambient"))
        p = 0.15
        self.alight.node().setColor(Vec4(p, p, p, 1))
        render.setLight(self.alight)

        # Create a special ambient light specially for the sun
        # so that it appears bright
        self.ambientLava = self.sun.attachNewNode(AmbientLight("AmbientForLava"))
        # Since we do call
        # setLightOff(), we are turning off all the other lights on this
        # object first, and then turning on only the lava light.
        self.sun.setLightOff()
        self.sun.setLight(self.ambientLava)
        self.sky.setLight(self.ambientLava)

        # Important! Enable the shader generator.
        render.setShaderAuto()

    def initCamera(self):
        #Camera initialization
        camera.setPos(self.homeSpot.getPos())
        camera.lookAt(self.focusSpot)
    
    def time_is_now(self) :
        self.simulTime = datetime.utcnow()
    
    def changeSpeed(self, factor):
        speed = self.simulSpeed * factor
        if abs(speed) <= MAXSPEED :
            self.simulSpeed = speed

    def setSpeed(self, speed) :
        if speed <= MAXSPEED :
            self.simulSpeed = speed

    def toggleSpeed(self):
        if not self.paused :
            self.previousSpeed = self.simulSpeed
            self.simulSpeed = MINSPEED
            self.paused = True
        else:
            self.simulSpeed = self.previousSpeed
            self.paused = False

    def get_current_rel_pos(self) :
        return self.new.getPos(self.mainScene)
    
    def generate_speed_fade(self) :
        #generate intervals to fade in and out from previous speed
        prev_speed = self.simulSpeed
        slow = LerpFunc(self.setSpeed, FREEZELEN,
        prev_speed, MINSPEED)
        fast = LerpFunc(self.setSpeed, FREEZELEN,
        MINSPEED, prev_speed)
        return slow, fast

    def stop_follow(self) :
        self.following = None

    def start_follow(self, new) :
        self.travelling = False
        self.following = new

    def follow(self, identity):
        if identity == "earth" :
            new = self.earth
        elif identity == "moon" :
            new = self.moon
        elif identity == "sun" :
            new = self.sun
        elif identity == "home" :
            new = self.homeSpot
        #if new destination and not already trying to reach another
        if self.following != new and not self.travelling :
            self.travelling = True
            #buttons should reflect what you're looking at and what you're following
            self.update_buttons('follow', identity)
            #stop flow of time while traveling
            slow, fast = self.generate_speed_fade()
            #to be able to capture its position during sequence
            self.new = new
            travel = self.camera.posInterval(TRAVELLEN,
            self.get_current_rel_pos,
            blendType='easeInOut')
            #slow sim, release, travel, lock and resume speed
            sequence = Sequence(slow, Func(self.stop_follow),
            travel, Func(self.start_follow, new), fast)
            sequence.start()
            

    def stop_look(self) :
        self.looking = None
        
    def start_look(self, new) :
        self.looking = new

    def lock_focus(self) :
        self.focusSpot.reparentTo(self.looking)
        self.focusSpot.setPos(0, 0, 0)

    def unlock_focus(self) :
        self.focusSpot.wrtReparentTo(self.mainScene)
        
    def look(self, identity):
        if identity == "earth" :
            new = self.earth
        elif identity == "moon" :
            new = self.moon
        elif identity == "sun" :
            new = self.sun
        #if new target
        if self.looking != new :
            self.update_buttons('look', identity)
            #stop flow of tim while changing focus
            slow, fast = self.generate_speed_fade()
            #store new to get actual position
            self.new = new
            travel = self.focusSpot.posInterval(FREEZELEN,
            self.get_current_rel_pos,
            blendType='easeInOut')
            sequence = Sequence(slow, Func(self.unlock_focus),
                travel, Func(self.lock_focus), fast)
            sequence.start()
            self.looking = new

    def toggleTilt(self):
        """earth tilt"""
        if self.tilted:
            inter = self.dummy_earth.hprInterval(TRAVELLEN,
            (0, 0, 0),
            blendType='easeIn')
            inter.start()
            self.tilted = False
        else:
            inter = self.dummy_earth.hprInterval(TRAVELLEN,
            (0, self.earthTilt, 0),
            blendType='easeIn')
            inter.start()
            self.tilted = True

    def toggleIncl(self):
        """moon realist inclination"""
        if self.inclinedHard or self.inclined :
            inter = self.dummy_root_moon.hprInterval(TRAVELLEN,
            (0, 0, 0),
            blendType='easeIn')
            inter.start()
            self.inclined = False
            self.inclinedHard = False
        else:
            inter = self.dummy_root_moon.hprInterval(TRAVELLEN,
            (0, self.moonIncli, 0),
            blendType='easeIn')
            inter.start()
            self.inclined = True
            
    def toggleInclHard(self):
        """moon exagerated inclination"""
        if self.inclinedHard or self.inclined :
            inter = self.dummy_root_moon.hprInterval(TRAVELLEN,
            (0, 0, 0),
            blendType='easeIn')
            inter.start()
            self.inclined = False
            self.inclinedHard = False
        else:
            inter = self.dummy_root_moon.hprInterval(TRAVELLEN,
            (0, self.moonIncliHard, 0),
            blendType='easeIn')
            inter.start()
            self.inclinedHard = True

    def drawOrbits(self):
        #Draw orbits
        self.earth_orbitline = graphics.makeArc(360, 128)
        self.earth_orbitline.reparentTo(self.root_earth)
        self.earth_orbitline.setHpr( 0, 90,0)
        self.earth_orbitline.setScale(UA)
        # orbits are not affected by sunlight
        self.earth_orbitline.hide(BitMask32.bit(0))
        
        self.moon_orbitline = graphics.makeArc(360, 128)
        self.moon_orbitline.reparentTo(self.root_moon)
        self.moon_orbitline.setHpr( 0, 90,0)
        self.moon_orbitline.setScale(MOONAX)
        # orbits are not affected by sunlight
        self.moon_orbitline.hide(BitMask32.bit(0))
        
    def loadPlanets(self):
        #Create the dummy nodes
        self.dummy_root_earth = render.attachNewNode('dummy_root_earth')
        self.root_earth = self.dummy_root_earth.attachNewNode('root_earth')
        
        self.earth_system = self.root_earth.attachNewNode('earth_system')
        self.earth_system.setPos(self.orbitscale,0,0)
        
        self.dummy_earth = self.earth_system.attachNewNode('dummy_earth')
        self.dummy_earth.setEffect(CompassEffect.make(render))
        
        #The moon orbits Earth, not the sun
        self.dummy_root_moon = self.earth_system.attachNewNode('dummy_root_moon')
        self.dummy_root_moon.setEffect(CompassEffect.make(render))
        
        self.root_moon = self.dummy_root_moon.attachNewNode('root_moon')
        
        self.moon_system = self.root_moon.attachNewNode('moon_system')
        self.moon_system.setPos(MOONAX, 0, 0)
        
        self.dummy_moon = self.moon_system.attachNewNode('dummy_moon')
        self.dummy_moon.setHpr(0, self.moonTilt, 0)
        self.dummy_moon.setEffect(CompassEffect.make(render))
        
        #Load the sky
        self.sky = loader.loadModel("models/solar_sky_sphere")
        self.sky_tex = loader.loadTexture("models/stars_1k_tex.jpg")
        self.sky.setTexture(self.sky_tex, 1)
        self.sky.reparentTo(render)
        self.sky.setScale(10 *self.orbitscale)
        self.sky.hide(BitMask32.bit(0))

        #Load the Sun
        self.sun = loader.loadModel("models/planet_sphere")
        self.sun_tex = loader.loadTexture("models/sun_1k_tex.jpg")
        self.sun.setTexture(self.sun_tex, 1)
        self.sun.reparentTo(render)
        self.sun.setScale(self.sunradius)
        self.sun.hide(BitMask32.bit(0))

        #Load Earth
        self.earth = loader.loadModel("models/planet_sphere")
        self.earth_tex = loader.loadTexture("models/earth_1k_tex.jpg")
        self.earth.setTexture(self.earth_tex, 1)
        self.earth.reparentTo(self.dummy_earth)
        self.earth.setScale(self.sizescale)
        
        #Load the moon
        self.moon = loader.loadModel("models/planet_sphere")
        self.moon_tex = loader.loadTexture("models/moon_1k_tex.jpg")
        self.moon.setTexture(self.moon_tex, 1)
        self.moon.reparentTo(self.dummy_moon)
        self.moon.setScale(MOONRADIUS)
    
    def placePlanets(self) :
        '''positions planetoids according to time of simulation'''
        #time in days
        now = self.simulTime
        julian_time = calendar.cal_to_jde(now.year, now.month, now.day,
        now.hour, now.minute, now.second, gregorian=True)
        
        self.sun.setHpr((360 / SUNROT) * julian_time % 360, 0, 0)

        if USEEPHEM :
            #REALIST MODE (BUT SLOW!!)
            longi = self.system_coord.dimension(julian_time, 'Earth', 'L')
            lati = self.system_coord.dimension(julian_time, 'Earth', 'B')
            self.dummy_root_earth.setHpr(0, degrees(lati), 0)
            self.root_earth.setHpr(degrees(longi), 0, 0)
            self.earth.setHpr(360 * julian_time % 360, 0, 0)
            
            longi = self.moon_coord.dimension(julian_time, 'L')
            lati = self.moon_coord.dimension(julian_time, 'B')
            self.dummy_root_moon.setHpr(0, degrees(lati), 0)
            self.root_moon.setHpr(degrees(longi), 0, 0)
            self.moon.setHpr((360 / MOONROT) * julian_time % 360 + 110, 0, 0)
        else :
            #SIMPLISTIC MODEL
            self.root_earth.setHpr(
            ((360 / self.yearscale) * julian_time % 360) -EPHEMSIMPLESET,
            0, 0)
            self.earth.setHpr(360 * julian_time % 360, 0, 0)
            
            self.root_moon.setHpr((360 / MOONREVO) * julian_time % 360, 0, 0)
            #correction of 25 degrees to align correct moon face
            self.moon.setHpr((360 / MOONROT) * julian_time % 360 - 25, 0, 0)

    def loadMarkers(self):
        #Sun
        #Create always visible marker
        self.sunMarker = graphics.makeArc()
        self.sunMarker.reparentTo(render)
        self.sunMarker.setScale(self.sunradius + 0.1)
        # markers are not affected by sunlight or unspot
        self.sunMarker.hide(BitMask32.bit(0))
        #~ self.sunMarker.setLight(self.ambientLava)
        self.sunMarker.setBillboardPointWorld()

        #Earth
        #Create always visible marker
        self.earthMarker = graphics.makeArc()
        self.earthMarker.reparentTo(self.earth_system)
        self.earthMarker.setScale(self.sizescale + 0.1)
        self.earthMarker.hide(BitMask32.bit(0))# markers are not affected by sunlight
        self.earthMarker.setBillboardPointWorld()
        #Show orientation
        self.earthAxMarker = graphics.makeCross(4*self.sizescale)
        self.earthAxMarker.reparentTo(self.earth)
        self.earthAxMarker.hide(BitMask32.bit(0))# markers are not affected by sunlight
        #the moon
        #Create always visible marker
        self.moonMarker = graphics.makeArc()
        self.moonMarker.reparentTo(self.root_moon)
        self.moonMarker.setScale(MOONRADIUS + 0.1)
        self.moonMarker.setPos(MOONAX, 0, 0)
        self.moonMarker.hide(BitMask32.bit(0))# markers are not affected by sunlight
        self.moonMarker.setBillboardPointWorld()
        #Show orientation
        self.moonAxMarker = graphics.makeCross(4*self.sizescale)
        self.moonAxMarker.reparentTo(self.moon)
        self.moonAxMarker.hide(BitMask32.bit(0))# markers are not affected by sunlight

    def loadInterface(self) :
        paths = ('images/button_ready.png',
             'images/button_click.png',
             'images/button_rollover.png',
             'images/button_disabled.png')
        self.b_map = [graphics.makeGeom(name) for name in paths]
        #an alternate map to show activated buttons
        paths = ('images/button_activated.png',
             'images/button_click.png',
             'images/button_activated.png',
             'images/button_disabled.png')
        self.b_map_acti = [graphics.makeGeom(name) for name in paths]
        #Container
        w, h = base.win.getXSize(), base.win.getYSize()
        bw, bh = BUTTONSIZE
        b_cont = DirectFrame(frameSize=(-(bw+bw/2), bw+bw/2, -h/2, h/2),
            frameColor=(1,1,1,0.3),
            pos=(bw+bw/2, -1, -h/2))
        b_cont.reparentTo(pixel2d)

        def add_button(name, i, j, command, args, parent) :
            """add button as on a button grid on parent"""
            left, right, bottom, top = parent.bounds
            w, h = right - left, top - bottom
            pos = (-w/2+bw*i,0,h/2-bh-bh*j)
            b = DirectButton(text = name,
                text_font=self.condensed_font,
                text_scale = (bw/3, bh/1.3),
                text_pos=(bw/2, bh/3),
                pos=pos,
                command=command, extraArgs=args,
                geom=self.b_map,
                relief=None,
                pressEffect=False,
                parent=parent)
            return b

        def add_label(name, i, j, parent) :
            """add text label as on a button grid on parent"""
            left, right, bottom, top = parent.bounds
            w, h = right - left, top - bottom
            b = DirectLabel(text = name,
                text_font=self.condensed_font,
                text_scale=(bw/3, bh/1.3),
                text_pos=(bw/2, bh/3),
                text_fg=(1,1,1,1),
                text_shadow=(0,0,0,0.9),
                pos = (-w/2+bw*i,0,h/2-bh-bh*j),
                relief=None,
                parent=parent)
            return b
        
        #Buttons to follow
        j = 0
        add_label('Go to : ', 1, j, b_cont)
        self.earth_b = add_button('Earth', 0, j+1, self.follow, ['earth'], b_cont)
        self.moon_b = add_button('Moon', 1, j+1, self.follow, ['moon'], b_cont)
        self.sun_b = add_button('Sun', 2, j+1, self.follow, ['sun'], b_cont)
        self.ext_b = add_button('Ext', 2, j+2, self.follow, ['home'], b_cont)
        #and to look at
        j = 4
        add_label('Look at : ', 1, j, b_cont)
        self.earth_lb = add_button('Earth', 0, j+1, self.look, ['earth'], b_cont)
        self.moon_lb = add_button('Moon', 1, j+1, self.look, ['moon'], b_cont)
        self.sun_lb = add_button('Sun', 2, j+1, self.look, ['sun'], b_cont)
        #and to change speed
        j = 7
        add_label('Speed : ', 0, j, b_cont)
        self.speedlabel = add_label('Speed', 1, j, b_cont)
        add_button('-', 0, j+1, self.changeSpeed, [1./2], b_cont)
        add_button('+', 1, j+1, self.changeSpeed, [2], b_cont)
        add_button('++', 2, j+1, self.changeSpeed, [100], b_cont)
        add_button('-1', 0, j+2, self.changeSpeed, [-1], b_cont)
        self.pause_b = add_button('Pause', 1, j+2, self.toggleSpeed, [], b_cont)
        add_button('Now', 2, j+2, self.time_is_now, [], b_cont)

        #date time display
        j = 11
        self.datelabel = add_label('UTC Time', 1, j, b_cont)
        self.datelabel['text_font'] = self.mono_font
        self.timelabel = add_label('UTC Time', 1, j+1, b_cont)
        self.timelabel['text_font'] = self.mono_font
        
        #factual changes
        j = 15
        add_label('Factual changes : ', 1, j, b_cont)
        add_button('Moon', 0, j+1, self.toggleIncl, [], b_cont)
        add_button('Moon+', 1, j+1, self.toggleInclHard, [], b_cont)
        add_button('Earth', 2, j+1, self.toggleTilt, [], b_cont)

    
    def update_buttons(self, action, identity='earth') :
        """set buttons states and appearances according to user input
        buttons should reflect what you're looking at and what you're following"""
        if action == 'follow' :
            if identity == 'earth' :
                #disable buttons to prevent looking at own position
                self.earth_lb['state'] = DGG.DISABLED
                self.moon_lb['state'] = DGG.NORMAL
                self.sun_lb['state'] = DGG.NORMAL
                #show activated button for followed object
                self.earth_b['geom'] = self.b_map_acti
                self.moon_b['geom'] = self.b_map
                self.sun_b['geom'] = self.b_map
                self.ext_b['geom'] = self.b_map
            elif identity == 'moon' :
                self.earth_lb['state'] = DGG.NORMAL
                self.moon_lb['state'] = DGG.DISABLED
                self.sun_lb['state'] = DGG.NORMAL
                self.earth_b['geom'] = self.b_map
                self.moon_b['geom'] = self.b_map_acti
                self.sun_b['geom'] = self.b_map
                self.ext_b['geom'] = self.b_map
            elif identity == 'sun' :
                self.earth_lb['state'] = DGG.NORMAL
                self.moon_lb['state'] = DGG.NORMAL
                self.sun_lb['state'] = DGG.DISABLED
                self.earth_b['geom'] = self.b_map
                self.moon_b['geom'] = self.b_map
                self.sun_b['geom'] = self.b_map_acti
                self.ext_b['geom'] = self.b_map
            elif identity == 'home' :
                self.earth_lb['state'] = DGG.NORMAL
                self.moon_lb['state'] = DGG.NORMAL
                self.sun_lb['state'] = DGG.NORMAL
                self.earth_b['geom'] = self.b_map
                self.moon_b['geom'] = self.b_map
                self.sun_b['geom'] = self.b_map
                self.ext_b['geom'] = self.b_map_acti
        elif action == 'look' :
            if identity == 'earth' :
                #disable buttons to prevent going at looked object
                self.earth_b['state'] = DGG.DISABLED
                self.moon_b['state'] = DGG.NORMAL
                self.sun_b['state'] = DGG.NORMAL
                #show activated button for looked object
                self.earth_lb['geom'] = self.b_map_acti
                self.moon_lb['geom'] = self.b_map
                self.sun_lb['geom'] = self.b_map
            elif identity == 'moon' :
                self.earth_b['state'] = DGG.NORMAL
                self.moon_b['state'] = DGG.DISABLED
                self.sun_b['state'] = DGG.NORMAL
                self.earth_lb['geom'] = self.b_map
                self.moon_lb['geom'] = self.b_map_acti
                self.sun_lb['geom'] = self.b_map
            elif identity == 'sun' :
                self.earth_b['state'] = DGG.NORMAL
                self.moon_b['state'] = DGG.NORMAL
                self.sun_b['state'] = DGG.DISABLED
                self.earth_lb['geom'] = self.b_map
                self.moon_lb['geom'] = self.b_map
                self.sun_lb['geom'] = self.b_map_acti

    #
    #
    ## TASKS :
    #
    def lockTask(self, task) :
        """alignment contraints""" 
        #lighting follows earth
        self.light.lookAt(self.earth)
        #align if necessary
        if self.following != None :
                camera.setPos(self.following.getPos(self.render))
        if self.looking != None :
                camera.lookAt(self.focusSpot)
        return Task.cont
        
    def timeTask(self, task) :
        #keep simulation time updated each frame
        dt = globalClock.getDt() * self.simulSpeed
        #datetime object is limited between year 1 and year 9999
        try :
            self.simulTime +=  timedelta(seconds=dt)
        except OverflowError :
            if self.simulSpeed < 0 :
                self.simulTime =  datetime.min
            else :
                self.simulTime = datetime.max
            self.simulSpeed = MINSPEED
        return Task.cont

    def interfaceTask(self, task) :
        #update simulton speed indicator 
        #(in scientific notation with limied significant digits)
        self.speedlabel['text'] = '%.1e' % self.simulSpeed, 2
        #update clock display
        new_time = self.simulTime.isoformat().split("T")
        self.datelabel['text'] = new_time[0]
        self.timelabel['text'] = new_time[1].split(".")[0]
        #show task timing for debug
        if PRINTTIMING :
            print self.taskMgr
        return Task.again

    def positionTask(self, task) :    
        #update planetoids positions
        self.placePlanets()
        return Task.cont

#a virtual argument to bypass packing bug
def main(arg=None):
    w = World()
    w.run()

if __name__ == '__main__':
    main()
