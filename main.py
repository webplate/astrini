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

def linInt(level, v1, v2) :
    '''linearly interpolate between v1 and v2
    according to 0<level<1 '''
    return v1 * level + v2 * (1 - level)

def nodeCoordIn2d(nodePath):
    '''converts coord of node in render to coord in aspect2d'''
    coord3d = nodePath.getPos(base.cam)
    #elude objects behind camera
    if coord3d[1] < 0 :
        return Point3()
    coord2d = Point2()
    base.camLens.project(coord3d, coord2d)
    coordInRender2d = Point3(coord2d[0], 0, coord2d[1])
    coordInAspect2d = aspect2d.getRelativePoint(render2d,
                        coordInRender2d)
    return coordInAspect2d

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
        self.initAstrofacts()
        self.initEmpty()
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
        self.show_shadows = False
        self.show_stars = False
        self.show_marks = False
        self.realist_scale = False
        # Add Tasks procedures to the task manager.
        #low priority to prevent jitter of camera
        self.taskMgr.add(self.lockTask, "lockTask", priority=25)
        self.taskMgr.add(self.timeTask, "timeTask")
        #do not update interface every frame (no use slowdown)
        self.taskMgr.doMethodLater(INTERFACEDELAY, self.interfaceTask, "interfaceTask")
        self.taskMgr.add(self.positionTask, "positionTask")
        
        #InitialSettings
        self.look(self.sun)
        self.follow(self.home)
        #~ self.simulTime = datetime(9998, 3, 20)

    def initAstrofacts(self) :
        '''variables to control the relative speeds of spinning and orbits in the
        simulation'''
        #Number of days a full rotation of Earth around the sun should take
        self.yearscale = EARTHREVO

        self.ua =  UA_F          #Orbit scale (fantasist)
        self.earthradius = EARTHRADIUS_F             #Planet size scale
        self.moonradius = MOONRADIUS_F
        self.sunradius = SUNRADIUS_F
        self.moonax = MOONAX_F
        self.earthTilt = EARTHTILT
        self.moonTilt = MOONTILT
        self.moonIncli = MOONINCL
        self.moonIncliHard = MOONINCL_F

    def initEmpty(self) :
        #Create the dummy nodes
        self.home = render.attachNewNode('home')
        self.home.setName('home')
        self.focus = render.attachNewNode('focus')
        self.focus.setName('focus')

    def initScene(self) :
        self.simulSpeed = 1
        self.time_is_now()
        
        #computations of planetoids positions
        self.moon_coord = lunar.Lunar()
        self.system_coord = planets.VSOP87d()
        
        base.setBackgroundColor(0.2, 0.2, 0.2)    #Set the background to grey
        self.loadPlanets()                #Load and position the models
        self.loadShadows()
        self.loadMarkers()
        self.loadOrbits()
        self.loadLight()                # light the scene
        #position and scale all loaded
        self.placeAll()

    def loadLight(self):
        #invisible spotlight to activate shadow casting (bypass bug)
        self.unspot = render.attachNewNode(Spotlight("Invisible spot"))
        self.unspot.setPos(0,0,self.ua)
        self.unspot.setHpr(0,90,0)
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
        render.setLight(self.light)

        self.alight = render.attachNewNode(AmbientLight("Ambient"))
        p = 0.15
        self.alight.node().setColor(Vec4(p, p, p, 1))
        render.setLight(self.alight)

        # Create a special ambient light specially for the sun
        # so that it appears bright
        self.ambientLava = self.render.attachNewNode(AmbientLight("AmbientForLava"))
        self.sun.setLight(self.ambientLava)
        self.sky.setLight(self.ambientLava)
        #Special light fo markers
        self.ambientMark = render.attachNewNode(AmbientLight("AmbientMark"))
        self.ambientMark.node().setColor(Vec4(0.8, 0.4, 0, 1))
        self.sunMarker.setLight(self.ambientMark)
        self.earthMarker.setLight(self.ambientMark)
        self.moonMarker.setLight(self.ambientMark)
        self.earthAxMarker.setLight(self.ambientMark)
        self.earth_orbitline.setLight(self.ambientMark)
        self.moon_orbitline.setLight(self.ambientMark)

        # Important! Enable the shader generator.
        render.setShaderAuto()
    
    def placeLight(self) :
        self.light.node().getLens().setFilmSize((2*self.moonax,self.moonax/2))
        self.light.node().getLens().setNearFar(self.ua - self.moonax, self.ua + self.moonax)
    
    def placeCamera(self) :
        #Compute camera-sun distance from fov
        fov = self.Camera.getFov()[0]
        margin = self.ua / 3
        c_s_dist = (self.ua + margin) / tan(radians(fov/2))
        self.home.setPos(0, -c_s_dist,self.ua/3)
        #Camera initialization
        camera.setPos(self.home.getPos())
        camera.lookAt(self.focus)
    
    def time_is_now(self) :
        self.simulTime = datetime(9998, 3, 20)
        self.simulTime = datetime.utcnow()
    
    def changeSpeed(self, factor):
        #if simulation is paused change previous speed
        if not self.paused :
            speed = self.simulSpeed * factor
            if speed > MAXSPEED :
                self.simulSpeed = MAXSPEED
            elif speed < -MAXSPEED :
                self.simulSpeed = -MAXSPEED
            else :
                self.simulSpeed = speed
        else :
            speed = self.previousSpeed * factor
            if speed > MAXSPEED :
                self.previousSpeed = MAXSPEED
            elif speed < -MAXSPEED :
                self.previousSpeed = -MAXSPEED
            else :
                self.previousSpeed = speed

    def setSpeed(self, speed) :
        if speed <= MAXSPEED :
            self.simulSpeed = speed

    def toggleSpeed(self):
        if not self.paused :
            self.previousSpeed = self.simulSpeed
            self.simulSpeed = MINSPEED
            #change button appearance
            self.pause_b['geom'] = self.b_map_acti
            self.paused = True
        else:
            self.simulSpeed = self.previousSpeed
            self.pause_b['geom'] = self.b_map
            self.paused = False

    def reverseSpeed(self) :
        self.changeSpeed(-1)
        #button appearance should reflect reversed state
        if not self.reverse :
            self.reverse_b['geom'] = self.b_map_acti
            self.reverse = True
        else :
            self.reverse_b['geom'] = self.b_map
            self.reverse = False
        
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
        #if new destination and not already trying to reach another
        if self.following != identity and not self.travelling :
            self.travelling = True
            #to be able to capture its position during sequence
            #and make updates before we actually follow it
            self.new = identity
            #buttons should reflect what you're looking at and what you're following
            self.update_buttons('follow')
            #hide tubular shadow of followed object
            self.update_shadows()
            #stop flow of time while traveling
            slow, fast = self.generate_speed_fade()
            travel = self.camera.posInterval(TRAVELLEN,
            self.get_current_rel_pos,
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
        self.focus.reparentTo(self.looking)
        self.focus.setPos(0, 0, 0)

    def unlock_focus(self) :
        self.focus.wrtReparentTo(self.mainScene)
        
    def look(self, identity) :
        #if new target
        if self.looking != identity and not self.travelling :
            #store new to get actual position and update interface
            self.new = identity
            self.update_buttons('look')
            #stop flow of time while changing focus
            slow, fast = self.generate_speed_fade()
            
            travel = self.focus.posInterval(FREEZELEN,
            self.get_current_rel_pos,
            blendType='easeInOut')
            sequence = Sequence(slow, Func(self.unlock_focus),
                travel, Func(self.lock_focus), fast)
            sequence.start()
            self.looking = identity

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
            
    def toggleScale(self) :
        '''a realistic scaling modifying :
        self.ua =  UA_F          
        self.earthradius = EARTHRADIUS_F           
        self.moonradius = MOONRADIUS_F
        self.sunradius = SUNRADIUS_F
        self.moonax = MOONAX_F
        '''
        if not self.realist_scale :
            LerpFunc(self.scaleSystem,
             fromData=0,
             toData=1,
             duration=SCALELEN,
             blendType='easeIn').start()

            self.fact_scale_b['geom'] = self.b_map_acti
            self.realist_scale = True
        else :
            LerpFunc(self.scaleSystem,
             fromData=1,
             toData=0,
             duration=SCALELEN,
             blendType='easeOut').start()
            
            self.fact_scale_b['geom'] = self.b_map
            self.realist_scale = False
    
    def scaleSystem(self, value) :
        '''scale the whole system from fantasist to realistic according
        to value (between 0. and 1.0)'''
        self.ua = linInt(value, UA, UA_F)
        self.earthradius = linInt(value, EARTHRADIUS, EARTHRADIUS_F)
        self.moonradius = linInt(value, MOONRADIUS, MOONRADIUS_F)
        self.sunradius = linInt(value, SUNRADIUS, SUNRADIUS_F)
        self.moonax = linInt(value, MOONAX, MOONAX_F)
        #and reposition system according to new values
        self.placeAll()
        
    def loadOrbits(self) :
        #Draw orbits
        self.earth_orbitline = graphics.makeArc(360, ORBITRESOLUTION)
        self.earth_orbitline.setHpr( 0, 90,0)
        
        self.moon_orbitline = graphics.makeArc(360, ORBITRESOLUTION)
        self.moon_orbitline.setHpr( 0, 90,0)
        
        for obj in [self.earth_orbitline, self.moon_orbitline] :
            #Camera position shouldn't make these actors disappear
            obj.node().setBounds(OmniBoundingVolume())
            obj.node().setFinal(True)
            # orbits are not affected by sunlight
            obj.hide(BitMask32.bit(0))
    
    def placeOrbits(self) :
        self.earth_orbitline.setScale(self.ua)
        self.moon_orbitline.setScale(self.moonax)

    def loadPlanets(self):
        #Create the dummy nodes
        self.dummy_root_earth = render.attachNewNode('dummy_root_earth')
        self.root_earth = self.dummy_root_earth.attachNewNode('root_earth')
        
        self.earth_system = self.root_earth.attachNewNode('earth_system')
        
        self.dummy_earth = self.earth_system.attachNewNode('dummy_earth')
        self.dummy_earth.setEffect(CompassEffect.make(render))
        
        #The moon orbits Earth, not the sun
        self.dummy_root_moon = self.earth_system.attachNewNode('dummy_root_moon')
        self.dummy_root_moon.setEffect(CompassEffect.make(render))
        
        self.root_moon = self.dummy_root_moon.attachNewNode('root_moon')
        
        self.moon_system = self.root_moon.attachNewNode('moon_system')
        
        self.dummy_moon = self.moon_system.attachNewNode('dummy_moon')
        self.dummy_moon.setHpr(0, self.moonTilt, 0)
        self.dummy_moon.setEffect(CompassEffect.make(render))
        
        #Load the sky
        self.sky = loader.loadModel("models/solar_sky_sphere")
        self.sky_tex = loader.loadTexture("models/stars_1k_tex.jpg")
        self.sky.setTexture(self.sky_tex, 1)
        self.sky.hide(BitMask32.bit(0))

        #Load the Sun
        self.sun = loader.loadModel("models/planet_sphere")
        #this particuar node should have a usable name
        self.sun.setName('sun')
        self.sun_tex = loader.loadTexture("models/sun_1k_tex.jpg")
        self.sun.setTexture(self.sun_tex, 1)
        self.sun.reparentTo(render)
        self.sun.hide(BitMask32.bit(0))

        #Load Earth
        self.earth = loader.loadModel("models/planet_sphere")
        self.earth.setName('earth')
        self.earth_tex = loader.loadTexture("models/earth_1k_tex.jpg")
        self.earth.setTexture(self.earth_tex, 1)
        self.earth.reparentTo(self.dummy_earth)
        
        #Load the moon
        self.moon = loader.loadModel("models/planet_sphere")
        self.moon.setName('moon')
        self.moon_tex = loader.loadTexture("models/moon_1k_tex.jpg")
        self.moon.setTexture(self.moon_tex, 1)
        self.moon.reparentTo(self.dummy_moon)
        
        #Camera position shouldn't make these actors disappear
        for obj in [self.sky, self.earth, self.sun, self.moon] :
            obj.node().setBounds(OmniBoundingVolume())
            obj.node().setFinal(True)
    
    def placePlanets(self) :
        '''position planetoids on orbits, set distance from their gravitationnal
        center, scale planetoids'''
        self.earth_system.setPos(self.ua,0,0)
        self.moon_system.setPos(self.moonax, 0, 0)
        
        self.sky.setScale(10 *self.ua)
        self.sun.setScale(self.sunradius)
        self.earth.setScale(self.earthradius)
        self.moon.setScale(self.moonradius)
    
    def rotatePlanets(self) :
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

    def loadShadows(self) :
        '''black areas to show the casted sadows'''
        self.earthShadow = loader.loadModel("models/tube")
        self.earthShadow.setTransparency(TransparencyAttrib.MAlpha)
        self.earthShadow.setColor(0,0,0,0.5)
        self.earthShadow.setSy(1000)

        self.moonShadow = loader.loadModel("models/tube")        
        self.moonShadow.setTransparency(TransparencyAttrib.MAlpha)
        self.moonShadow.setColor(0,0,0,0.5)
        self.moonShadow.setSy(1000)

    def loadMarkers(self) :
        #Sun
        #Create always visible marker
        self.sunMarker = graphics.makeArc()
        self.sunMarker.setScale(MARKERSCALE)
        #Earth
        #Create always visible marker
        self.earthMarker = graphics.makeArc()
        self.earthMarker.setScale(MARKERSCALE)
        #Show orientation
        self.earthAxMarker = graphics.makeCross()
        self.earthAxMarker.hide(BitMask32.bit(0))# markers are not affected by sunlight
        #the moon
        #Create always visible marker
        self.moonMarker = graphics.makeArc()
        self.moonMarker.setScale(MARKERSCALE)

    def placeMarkers(self) :
        '''set position and scale of markers'''
        self.earthAxMarker.setScale(4*self.earthradius)
        
        self.sunMarker.setPos(nodeCoordIn2d(self.sun))
        self.moonMarker.setPos(nodeCoordIn2d(self.moon))
        self.earthMarker.setPos(nodeCoordIn2d(self.earth))


    def placeAll(self) :
        self.placeCamera()
        self.placePlanets()
        self.placeMarkers()
        self.placeOrbits()
        self.placeLight()


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
        #Container for main interface
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

        def add_textarea(lines, parent) :
            """add text area filling parent
            lines is a list of strings, one str per line"""
            left, right, bottom, top = parent.bounds
            w, h = right - left, top - bottom
            out = []
            for i, line in enumerate(lines) :
                t = DirectLabel(text = line,
                    text_font=self.condensed_font,
                    text_scale=(bw/3, bh/1.3),
                    text_pos=(bw/2, bh/3),
                    text_fg=(0,0,0,1),
                    text_shadow=(1,1,1,0.7),
                    pos = (-bw/2, 0, h/2-bh-bh*i),
                    relief=None,
                    parent=parent)
                out.append(t)
            return out
        
        def add_dialog(size) :
            '''a frame with a close button
            the size must be set according to button sizes'''
            cont = DirectFrame(frameSize=size,
            frameColor=(1,1,1,0.8),
            pos=(w/2, -1, -h/2))
            close_button_coordinate = (-size[0] + size[1])/bw - 1
            add_button('X', close_button_coordinate, 0,
            self.hide_dialog, [cont], cont)
            return cont
            
        #about dialog
        text = [
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
        
        self.about_dialog = add_dialog((-5*bw, 5*bw, -10*bh, 10*bh))
        add_textarea(text, self.about_dialog)
        
        #An informational dialog
        self.info_dialog = add_dialog((-3*bw, 3*bw, -3*bh, 3*bh))
        add_textarea(['','Here some information'], self.info_dialog)
        
        #Buttons to follow
        j = 1
        add_label('Go to : ', 1, j, b_cont)
        self.earth_b = add_button('Earth', 0, j+1, self.follow, [self.earth], b_cont)
        self.moon_b = add_button('Moon', 1, j+1, self.follow, [self.moon], b_cont)
        self.sun_b = add_button('Sun', 2, j+1, self.follow, [self.sun], b_cont)
        self.ext_b = add_button('Ext', 2, j+2, self.follow, [self.home], b_cont)
        #and to look at
        j += 4
        add_label('Look at : ', 1, j, b_cont)
        self.earth_lb = add_button('Earth', 0, j+1, self.look, [self.earth], b_cont)
        self.moon_lb = add_button('Moon', 1, j+1, self.look, [self.moon], b_cont)
        self.sun_lb = add_button('Sun', 2, j+1, self.look, [self.sun], b_cont)
        #and to change speed
        j += 3
        add_label('Speed : ', 0, j, b_cont)
        self.speedlabel = add_label('Speed', 1, j, b_cont)
        add_button('-', 0, j+1, self.changeSpeed, [1./2], b_cont)
        add_button('+', 1, j+1, self.changeSpeed, [2], b_cont)
        add_button('++', 2, j+1, self.changeSpeed, [100], b_cont)
        self.reverse_b = add_button('-1', 0, j+2, self.reverseSpeed, [], b_cont)
        self.pause_b = add_button('Pause', 1, j+2, self.toggleSpeed, [], b_cont)
        add_button('Now', 2, j+2, self.time_is_now, [], b_cont)

        #date time display
        j += 4
        self.datelabel = add_label('UTC Time', 1, j, b_cont)
        self.datelabel['text_font'] = self.mono_font
        self.timelabel = add_label('UTC Time', 1, j+1, b_cont)
        self.timelabel['text_font'] = self.mono_font
        
        #factual changes
        j += 3
        add_label('Factual changes : ', 1, j, b_cont)
        self.fact_moon_b = add_button('Moon', 0, j+1, self.toggleIncl, [], b_cont)
        self.fact_moon2_b = add_button('Moon+', 1, j+1, self.toggleInclHard, [], b_cont)
        self.fact_earth_b = add_button('Earth', 2, j+1, self.toggleTilt, [], b_cont)
        self.fact_scale_b = add_button('Scale', 0, j+2, self.toggleScale, [], b_cont)
        
        #Visualization changes
        j += 4
        add_label('Display : ', 1, j, b_cont)
        self.shadow_b = add_button('Shadow', 0, j+1, self.toggleShadows, [], b_cont)
        self.mark_b = add_button('Mark', 1, j+1, self.toggleMarks, [], b_cont)
        self.star_b = add_button('Stars', 2, j+1, self.toggleStars, [], b_cont)
        
        #hidden dialogs
        j += 20
        add_button('Info', 0, j, self.show_dialog, [self.info_dialog], b_cont)
        add_button('About', 2, j, self.show_dialog, [self.about_dialog], b_cont)
        

    def show_dialog(self, frame) :
        '''show a given frame'''
        frame.reparentTo(pixel2d)
    
    def hide_dialog(self, frame) :
        frame.detachNode()
        
    def update_buttons(self, action) :
        """set buttons states and appearances according to user input
        buttons should reflect what you're looking at and what you're following"""
        identity = self.new.getName()
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

    def update_shadows(self) :
        '''hide/show tubular shadows'''
        #show them all
        if self.show_shadows :
            self.moonShadow.reparentTo(self.moon)
            self.earthShadow.reparentTo(self.earth)
        #we shouldn't hide the same shadow if we are going to follow or 
        #already following
        if self.travelling :
            name = self.new.getName()
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
                camera.lookAt(self.focus)
        #casted shadows should remain aligned with sun
        self.earthShadow.lookAt(self.sun)
        self.moonShadow.lookAt(self.sun)
        #place markers on their targets
        self.placeMarkers()
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
        #update simulation speed indicator 
        #(in scientific notation with limited significant digits)
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
        self.rotatePlanets()
        return Task.cont

#a virtual argument to bypass packing bug
def main(arg=None):
    w = World()
    w.run()

if __name__ == '__main__':
    main()
