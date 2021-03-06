# -*- coding: utf-8-*- 
#Core functions of PandaEngine
import panda3d.core
# Task declaration import 
from direct.task import Task
#interpolate function parameter
from direct.interval.LerpInterval import LerpFunc
from direct.interval.IntervalGlobal import Sequence, Func
#Work with time
from datetime import datetime, timedelta
import calendar

import math
import astronomia.calendar

from math import tan, radians

#Drawing functions
import graphics
#My Global config variables
from config import *


def nodeCoordIn2d(nodePath):
    '''converts coord of node in render to coord in aspect2d'''
    coord3d = nodePath.getPos(base.cam)
    #elude objects behind camera
    if coord3d[1] < 0 :
        return panda3d.core.Point3()
    coord2d = panda3d.core.Point2()
    base.camLens.project(coord3d, coord2d)
    coordInRender2d = panda3d.core.Point3(coord2d[0], 0, coord2d[1])
    coordInAspect2d = aspect2d.getRelativePoint(render2d,
                        coordInRender2d)
    return coordInAspect2d

class Planetoid(object) :
    '''rotating spherical model with markers'''
    def __init__(self, name, root, tex, radius, period = 1, offset = 0) :
        self.name = name
        self.root = root
        self.radius = radius
        self.period = period
        self.offset = offset
        self.load(tex)
        self.mod.reparentTo(self.root)
        #the model gets the same name as the planetoid
        self.mod.setName(self.name)
        
    def load(self, tex) :
        #load shape
        self.mod = loader.loadModel("models/planet_sphere")
        
        #load texture
        mod_tex = loader.loadTexture("models/"+tex)
        self.mod.setTexture(mod_tex, 1)
        
        #Camera position shouldn't make actors disappear
        self.mod.node().setBounds(panda3d.core.OmniBoundingVolume())
        self.mod.node().setFinal(True)
        
        #Create always visible marker
        self.marker = graphics.makeArc()
        self.marker.setScale(MARKERSCALE)
        self.marker.setTransparency(panda3d.core.TransparencyAttrib.MAlpha)
        self.marker.reparentTo(aspect2d)
        self.has_marker = True
        # not affected by sunlight
        self.marker.hide(panda3d.core.BitMask32.bit(0))
        # not visible by default
        self.hideMarker()
    
        #marker of orientation
        self.axis = graphics.makeCross()
        self.axis.setScale(AXSCALE * self.radius)
        self.axis.setTransparency(panda3d.core.TransparencyAttrib.MAlpha)
        self.axis.reparentTo(self.mod)
        self.has_axis = True
        # not affected by sunlight
        self.axis.hide(panda3d.core.BitMask32.bit(0))
        # not visible by default
        self.hideAxis()
        
    def showMarker(self) :
        if not self.has_marker:
            fade = self.marker.colorScaleInterval(FREEZELEN,
            panda3d.core.Vec4(1,1,1,0.5), panda3d.core.Vec4(1,1,1,0))
            self.has_marker = True
            fade.start()
        
    def hideMarker(self) :
        if self.has_marker:
            fade = self.marker.colorScaleInterval(FREEZELEN,
            panda3d.core.Vec4(1,1,1,0), panda3d.core.Vec4(1,1,1,0.5))
            self.has_marker = False
            fade.start()
    
    def showAxis(self) :
        if not self.has_axis:
            fade = self.axis.colorScaleInterval(FREEZELEN,
            panda3d.core.Vec4(1,1,1,0.5), panda3d.core.Vec4(1,1,1,0))
            self.has_axis = True
            fade.start()
        
    def hideAxis(self) :
        if self.has_axis:
            fade = self.axis.colorScaleInterval(FREEZELEN,
            panda3d.core.Vec4(1,1,1,0), panda3d.core.Vec4(1,1,1,0.5))
            self.has_axis = False
            fade.start()

    def rotate(self, julian_time) :
        '''rotate on itself according to time'''
        self.mod.setHpr((360 / self.period) * julian_time % 360 + self.offset, 0, 0)
    
    def place(self) :
        '''set position and scale'''
        self.mod.setScale(self.radius)
        #put marker in place
        self.marker.setPos(nodeCoordIn2d(self.mod))


class Orbital(Planetoid) :
    '''planetoid with an orbit, shadow
    distance from orbit root'''
    def __init__(self, name, root, tex, radius, period, offset,
    root_system, orbit_period, orbit_offset, distance) :
        Planetoid.__init__(self, name, root, tex, radius, period , offset)
        self.root_system = root_system
        self.orbit_period = orbit_period
        self.orbit_offset = orbit_offset
        self.distance = distance
        
        self.loadDummy()
        self.loadShadow()
        self.loadOrbit()
    
    def loadDummy(self) :
        '''Create the dummy nodes, the skeleton of the system'''
        self.dummy_root = self.root_system.attachNewNode('dummy_root')
        self.dummy_root.setCompass()

        self.root = self.dummy_root.attachNewNode('root')

        self.system = self.root.attachNewNode('system')
        
        self.dummy = self.system.attachNewNode('dummy')
        self.dummy.setCompass()
        
        #parent to get relative positionning
        self.mod.reparentTo(self.dummy)
    
    def orbit(self, julian_time) :
        coord = (((360 / self.orbit_period) * julian_time % 360)
         + self.orbit_offset)
        self.root.setHpr(coord , 0, 0)
    
    def rotate(self, time) :
        '''rotate on itself and around gravity center'''
        Planetoid.rotate(self, time)
        self.orbit(time)
    
    def place(self) :
        Planetoid.place(self)
        self.system.setPos(self.distance,0,0)
        self.orbit_line.setScale(self.distance)

    def loadShadow(self) :
        '''black areas to show the casted sadows'''
        self.shadow = loader.loadModel("models/tube")
        self.shadow.setTransparency(panda3d.core.TransparencyAttrib.MAlpha)
        self.shadow.reparentTo(self.mod)
        self.has_shadow = True
        self.shadow.setSy(1000)
        # hidden by default
        self.hideShadow()
    
    def showShadow(self) :
        if not self.has_shadow:
            fade = self.shadow.colorScaleInterval(FREEZELEN,
            panda3d.core.Vec4(0,0,0,0.5), panda3d.core.Vec4(0,0,0,0))
            self.has_shadow = True
            fade.start()

    def hideShadow(self) :
        if self.has_shadow:
            fade = self.shadow.colorScaleInterval(FREEZELEN,
            panda3d.core.Vec4(0,0,0,0), panda3d.core.Vec4(0,0,0,0.5))
            self.has_shadow = False
            fade.start()

    def loadOrbit(self) :
        #Draw orbits
        self.orbit_line = graphics.makeArc(360, ORBITRESOLUTION)
        self.orbit_line.setTransparency(panda3d.core.TransparencyAttrib.MAlpha)
        self.orbit_line.setHpr( 0, 90,0)
        #Camera position shouldn't make these actors disappear
        self.orbit_line.node().setBounds(panda3d.core.OmniBoundingVolume())
        self.orbit_line.node().setFinal(True)
        # orbits are not affected by sunlight
        self.orbit_line.hide(panda3d.core.BitMask32.bit(0))
        self.orbit_line.reparentTo(self.root)
        self.has_orbit = True
        self.hideOrbit()
    
    def showOrbit(self) :
        if not self.has_orbit:
            fade = self.orbit_line.colorScaleInterval(FREEZELEN,
            panda3d.core.Vec4(1,1,1,0.5), panda3d.core.Vec4(1,1,1,0))
            self.has_orbit = True
            fade.start()
        
       
    def hideOrbit(self) :
        if self.has_orbit:
            fade = self.orbit_line.colorScaleInterval(FREEZELEN,
            panda3d.core.Vec4(1,1,1,0), panda3d.core.Vec4(1,1,1,0.5))
            self.has_orbit = False
            fade.start()


class System(object) :
    '''sun earth and moon
    plus sky and lights
    methods to do factual changes'''
    def __init__(self, root):
        self.root = root
        self.initAstrofacts()
        self.loadPlanets()
        self.system = [self.sun, self.earth, self.moon]
        self.orbitals = [self.earth, self.moon]
        
        self.loadSky()
        self.loadLight()
        
        self.tilted = False
        self.inclined = False
        self.inclinedHard = False
        
        # Add Tasks procedures to the task manager.
        #lower priority to prevent jitter of objelf.moonaxects
        taskMgr.add(self.lockTask, "lockTask", priority=26)

    def initAstrofacts(self) :
        '''variables to control the relative speeds of spinning and orbits in the
        simulation'''

        self.ua =  UA_F          #Orbit scale (fantasist)
        self.moonax = MOONAX_F

        self.earthTilt = EARTHTILT
        self.moonTilt = MOONTILT
        self.moonIncli = MOONINCL
        self.moonIncliHard = MOONINCL_F

    def loadPlanets(self):
        self.sun = Planetoid('sun', self.root, 'sun_1k_tex.jpg',
        SUNRADIUS_F, SUNROT, 0)

        self.earth = Orbital('earth', self.root, 'earth_1k_tex.jpg',
        EARTHRADIUS_F, 1, EARTHROTSET, self.root,
        EARTHREVO, EPHEMSIMPLESET, self.ua)

        self.moon = Orbital('moon', self.root, 'moon_1k_tex.jpg',
        MOONRADIUS_F, MOONROT, MOONROTSET, self.earth.system,
        MOONREVO, MOONEPHEMSET, self.moonax)
    
    def loadLight(self):
        #invisible spotlight to activate shadow casting (bypass bug)
        self.unspot = self.root.attachNewNode(
        panda3d.core.Spotlight("Invisible spot"))
        self.unspot.setPos(0,0,self.ua)
        self.unspot.setHpr(0,90,0)
        self.unspot.node().getLens().setNearFar(0,0)
        self.root.setLight(self.unspot)
        
        #the light on the earth system which casts shadows on planetoids
        self.light = self.root.attachNewNode(
        panda3d.core.DirectionalLight("SunLight"))
        self.light.setPos(0,0,0)
        self.light.node().setScene(self.root)
        self.light.node().setShadowCaster(True, SHADOWRES, SHADOWRES)
        if SHOWFRUSTRUM :
            self.light.node().showFrustum()
        # a mask to define objects that shouldn't cast shadows
        self.light.node().setCameraMask(panda3d.core.BitMask32.bit(0))
        # illuminate objects
        self.earth.mod.setLight(self.light)
        self.moon.mod.setLight(self.light)

        self.alight = self.root.attachNewNode(
        panda3d.core.AmbientLight("Ambient"))
        p = 0.15
        self.alight.node().setColor(panda3d.core.Vec4(p, p, p, 1))
        self.root.setLight(self.alight)

        # Create a special ambient light specially for the sun
        # so that it appears bright
        self.ambientLava = self.root.attachNewNode(
        panda3d.core.AmbientLight("AmbientForLava"))
        self.sun.mod.setLight(self.ambientLava)
        self.sky.setLight(self.ambientLava)
        #Special light fo markers
        self.ambientMark = self.root.attachNewNode(
        panda3d.core.AmbientLight("AmbientMark"))
        self.ambientMark.node().setColor(panda3d.core.Vec4(0.8, 0.4, 0, 1))
        for obj in self.system :
            obj.marker.setLight(self.ambientMark)
            obj.axis.setLight(self.ambientMark)
        for obj in self.orbitals :
            obj.orbit_line.setLight(self.ambientMark)

        # Important! Enable the shader generator.
        self.root.setShaderAuto()

    def placeLight(self) :
        self.light.node().getLens().setFilmSize((2.1*self.earth.radius, 2.1*self.earth.radius))
        self.light.node().getLens().setNearFar(self.earth.distance - self.moon.distance,
        self.earth.distance + self.moon.distance)
    
    def loadSky(self) :
        self.sky = loader.loadModel("models/solar_sky_sphere")
        self.sky_tex = loader.loadTexture("models/stars_1k_tex.jpg")
        self.sky.setTexture(self.sky_tex, 1)
    
    def showSky(self) :
        self.sky.reparentTo(self.root)
    
    def hideSky(self) :
        self.sky.detachNode()
    
    def showShadows(self) :
        for obj in self.orbitals :
            obj.showShadow()
    
    def hideShadows(self) :
        for obj in self.orbitals :
            obj.hideShadow()
    
    def showMarkers(self) :
        for obj in self.orbitals :
            obj.showMarker()
            obj.showOrbit()
        self.earth.showAxis()

    def hideMarkers(self) :
        for obj in self.orbitals :
            obj.hideMarker()
            obj.hideOrbit()
        self.earth.hideAxis()

    def place(self) :
        for obj in self.system :
            obj.place()
        self.placeLight()
        self.sky.setScale(10*self.earth.distance)
    
    def rotate(self, time) :
        for obj in [self.sun, self.earth, self.moon] :
            obj.rotate(time)
    
    def lockTask(self, task) :
        """alignment contraints""" 
        #lighting follows earth
        self.light.lookAt(self.earth.mod)
        #casted shadows should remain aligned with sun
        self.earth.shadow.lookAt(self.sun.mod)
        self.moon.shadow.setHpr(self.earth.shadow, 0, 0, 0)
        self.place()
        return Task.cont
    
    def toggleTilt(self) :
        """earth tilt"""
        if self.tilted:
            inter = self.earth.dummy.hprInterval(TRAVELLEN,
            (0, 0, 0),
            blendType='easeIn')
            inter.start()
            self.tilted = False
        else :
            inter = self.earth.dummy.hprInterval(TRAVELLEN,
            (0, self.earthTilt, 0),
            blendType='easeIn')
            inter.start()
            self.tilted = True

    def toggleIncl(self, hard = False) :
        """moon inclination"""
        if self.inclined or self.inclinedHard :
            inter = self.moon.dummy_root.hprInterval(TRAVELLEN,
            (0, 0, 0),
            blendType='easeIn')
            inter.start()
            self.inclined = False
            self.inclinedHard = False
        else :
            if not hard :
                value = self.moonIncli
                self.inclined = True
            else :
                value = self.moonIncliHard
                self.inclinedHard = True
            inter = self.moon.dummy_root.hprInterval(TRAVELLEN,
            (0, value, 0),
            blendType='easeIn')
            inter.start()


def linInt(level, v1, v2) :
    '''linearly interpolate between v1 and v2
    according to 0<level<1 '''
    return v1 * level + v2 * (1 - level)

def stamp_to_time(t) :
    '''posix timestamp to datetime object'''
    return datetime.utcfromtimestamp(int(t))
    
def time_to_stamp(t):
    '''time object converted in timestamp'''
    return calendar.timegm(t.timetuple())

def time_to_julian(t) :
    '''time object converted in days as float'''
    julian_time = astronomia.calendar.cal_to_jde(t.year,
    t.month, t.day, t.hour, t.minute, t.second,
    gregorian=True)
    return julian_time


class Scene(object) :
    '''system with time and scale'''
    def __init__(self, world) :
        self.world = world
        self.loadEmpty()
        base.setBackgroundColor(0.2, 0.2, 0.2)    #Set the background to grey
        self.sys = System(self.root)
        #Time Control
        self.timeTravel = False # lock when changing speed
        self.sequences = [] # sequences to play when timeTraveling
        self.paused = False
        self.reverse = False
        self.jumping = False
        
        self.simul_speed = 1
        
        self.time_is_now()
        
        self.realist_scale = False
        
        self.show_shadows = False
        self.show_stars = False
        self.show_marks = False

        # Add Tasks procedures to the task managers.
        taskMgr.add(self.timeTask, "timeTask", priority = 1)
        taskMgr.add(self.placeTask, "placeTask", priority = 2)
        taskMgr.add(self.lockHomeTask, "lockHomeTask", priority=3)


    def loadEmpty(self) :
        #Create the dummy nodes
        self.root = render.attachNewNode('root')
        self.home = self.root.attachNewNode('home')
        self.home.setName('home')
        self.focus = self.root.attachNewNode('focus')
        self.focus.setName('focus')
        self.hook = self.root.attachNewNode('hook')
        self.hook.setName('hook')
    
    def placeCameraHome(self) :
        #Compute camera-sun distance from fov
        fov = base.camLens.getFov()[0]
        ua = self.sys.earth.distance
        margin = ua / 3
        c_s_dist = (ua + margin) / tan(radians(fov/2))
        self.world.home.setPos(c_s_dist,0,ua/3)

    def lockHomeTask(self, task) :
        '''keep home in place'''
        self.placeCameraHome()
        return Task.cont
    
    #Timing control :
    #
    #

    def time_is_now(self) :
        self.simul_speed = 1
        self.simul_time = datetime.utcnow()
    
    def changeSpeed(self, factor):
        #if simulation is paused change previous speed
        if not self.paused :
            speed = self.simul_speed * factor
            if speed > MAXSPEED :
                self.simul_speed = MAXSPEED
            elif speed < -MAXSPEED :
                self.simul_speed = -MAXSPEED
            else :
                self.simul_speed = speed
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
            self.simul_speed = speed

    def toggleSpeed(self):
        if not self.paused :
            self.previousSpeed = self.simul_speed
            self.simul_speed = 0.
            self.paused = True
        else:
            self.simul_speed = self.previousSpeed
            self.paused = False

    def reverseSpeed(self) :
        self.changeSpeed(-1)
        #button appearance should reflect reversed state
        if not self.reverse :
            self.reverse = True
        else :
            self.reverse = False
            
    def checkTimeTravel(self) :
        for s in self.sequences :
            if s.isPlaying() :
                self.timeTravel = True
                return
        print 'clear', self.sequences
        self.sequences = []
        self.timeTravel = False
        
    def generate_speed_fade(self, speed) :
        '''generate intervals to fade in and out from previous speed'''
        slow = LerpFunc(self.setSpeed, FREEZELEN, speed, 0.)
        fast = LerpFunc(self.setSpeed, FREEZELEN, 0., speed)
        return slow, fast

    def warp_time(self, value):
        '''interpolate simul_time between self.warp_init and self.warp_end
        '''
        if value == 0:
            self.jumping = False
        elif value == 1:
            self.jumping = True
        init = time_to_stamp(self.warp_init)
        end = time_to_stamp(self.warp_end)
        t = linInt(value, init, end)
        self.simul_time = stamp_to_time(t)
    
    def time_jump(self, jump_len):
        '''jump softly in time'''
        self.jump_len = timedelta(days=jump_len)
        self.warp_init = self.simul_time
        #datetime object is limited between year 1 and year 9999
        try :
            self.warp_end = self.simul_time + self.jump_len
        except OverflowError :
            self.warp_end = self.warp_init
        
        warp = LerpFunc(self.warp_time,
             fromData=1,
             toData=0,
             duration=SCALELEN,
             blendType='easeInOut')
        
        sequence = Sequence(warp, name='time_jump')
        sequence.start()

    def timeTask(self, task) :
        # get passed time
        dt = globalClock.getDt()
        if not self.jumping:
            #datetime object is limited between year 1 and year 9999
            try :
                #keep simulation time updated each frame
                self.simul_time +=  timedelta(seconds=dt * self.simul_speed)
            except OverflowError :
                if self.simul_speed < 0 :
                    self.simul_time =  datetime.min
                else :
                    self.simul_time = datetime.max
                self.simul_speed = 0.
        
        return Task.cont

    #Scaling control :
    #
    #

    def scaleSystem(self, value) :
        '''scale the whole system from fantasist to realistic according
        to value (between 0. and 1.0)'''
        if value == 0:
            self.realist_scale = False
        elif value == 1:
            self.realist_scale = True
        self.sys.earth.distance = linInt(value, UA, UA_F)
        self.sys.earth.radius = linInt(value, EARTHRADIUS, EARTHRADIUS_F)
        self.sys.moon.radius = linInt(value, MOONRADIUS, MOONRADIUS_F)
        self.sys.sun.radius = linInt(value, SUNRADIUS, SUNRADIUS_F)
        self.sys.moon.distance = linInt(value, MOONAX, MOONAX_F)
    
    def toggleScale(self) :
        '''a realistic scaling toggle :
        '''
        if not self.realist_scale :
            init = 0
            end = 1
        else:
            init = 1
            end = 0
        scale = LerpFunc(self.scaleSystem,
            fromData=init,
            toData=end,
            duration=SCALELEN,
            blendType='easeIn',
            name='scaling')
        
        scale.start()
    
    def placeTask(self, task) :
        self.sys.place()
        self.sys.rotate(time_to_julian(self.simul_time))
        return Task.cont
    
    #Vizualisation control
    def toggleShadows(self) :
        if self.show_shadows :
            self.show_shadows = False
        else :
            self.show_shadows = True
        self.updateShadows()
    
    def toggleSky(self) :
        if self.show_stars :
            self.sys.hideSky()
            self.show_stars = False
        else :
            self.sys.showSky()
            self.show_stars = True
    
    def toggleMarks(self) :
        if self.show_marks :
            self.sys.hideMarkers()
            self.show_marks = False
        else :
            self.sys.showMarkers()
            self.show_marks = True

    def updateShadows(self) :
        '''hide/show tubular shadows'''
        #show them all
        if self.show_shadows :
            show_earth = True
            show_moon = True
        else:
            show_earth = False
            show_moon = False
        #we shouldn't hide the same shadow if we are going to follow or 
        #already following
        #shouldn't bug if we aren't following any
        if self.world.Camera.hm.following != None :
            name = self.world.Camera.hm.following.getName()
        else :
            name = None
        #specific hide
        if name == 'earth' :
            show_earth = False
        elif name == 'moon' :
            show_moon = False
        elif name == 'sun':
            show_earth = False
            show_moon = False
        
        if show_earth:
            self.sys.earth.showShadow()
        else:
            self.sys.earth.hideShadow()
        if show_moon:
            self.sys.moon.showShadow()
        else:
            self.sys.moon.hideShadow()

    
