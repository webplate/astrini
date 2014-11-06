# -*- coding: utf-8-*- 
#Core functions of PandaEngine
from panda3d.core import *
# Task declaration import 
from direct.task import Task
#interpolate function parameter
from direct.interval.LerpInterval import LerpFunc
#Work with time
from datetime import datetime, timedelta
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
        return Point3()
    coord2d = Point2()
    base.camLens.project(coord3d, coord2d)
    coordInRender2d = Point3(coord2d[0], 0, coord2d[1])
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
        self.mod.node().setBounds(OmniBoundingVolume())
        self.mod.node().setFinal(True)
        
        #Create always visible marker
        self.marker = graphics.makeArc()
        self.marker.setScale(MARKERSCALE)
    
        #marker of orientation
        self.axis = graphics.makeCross()
        
    def showMarker(self) :
        '''always visible spot on target'''
        self.marker.reparentTo(aspect2d)
    
    def hideMarker(self) :
        self.marker.detachNode()
    
    def showAxis(self) :
        '''to see orientation'''
        self.axis.reparentTo(self.mod)
    
    def hideAxis(self) :
        self.axis.detachNode()
        
    def rotate(self, julian_time) :
        '''rotate on itself according to time'''
        self.mod.setHpr((360 / self.period) * julian_time % 360 + self.offset, 0, 0)
    
    def place(self) :
        '''set position and scale'''
        self.mod.setScale(self.radius)
        #put marker in place
        self.marker.setPos(nodeCoordIn2d(self.mod))
        self.axis.setScale(4*self.radius)


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
        self.dummy_root.setEffect(CompassEffect.make(self.root))

        self.dummy_root = self.root_system.attachNewNode('dummy_root')
        self.dummy_root.setEffect(CompassEffect.make(self.root))

        self.root = self.dummy_root.attachNewNode('root')

        self.system = self.root.attachNewNode('system')
        
        self.dummy = self.system.attachNewNode('dummy')
        self.dummy.setEffect(CompassEffect.make(self.root))
        
        #parent to get relative positionning
        self.mod.reparentTo(self.dummy)
    
    def orbit(self, julian_time) :
        self.root.setHpr(
    ((360 / self.orbit_period) * julian_time % 360) - self.orbit_offset,
        0, 0)
    
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
        self.shadow.setTransparency(TransparencyAttrib.MAlpha)
        self.shadow.setColor(0,0,0,0.5)
        self.shadow.setSy(1000)
    
    def showShadow(self) :
        self.shadow.reparentTo(self.mod)
    
    def hideShadow(self) :
        self.shadow.detachNode()

    def loadOrbit(self) :
        #Draw orbits
        self.orbit_line = graphics.makeArc(360, ORBITRESOLUTION)
        self.orbit_line.setHpr( 0, 90,0)
        #Camera position shouldn't make these actors disappear
        self.orbit_line.node().setBounds(OmniBoundingVolume())
        self.orbit_line.node().setFinal(True)
        # orbits are not affected by sunlight
        self.orbit_line.hide(BitMask32.bit(0))
    
    def showOrbit(self) :
        self.orbit_line.reparentTo(self.root)
    
    def hideOrbit(self) :
        self.orbit_line.detachNode()


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
        #lower priority to prevent jitter of objects
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
        EARTHRADIUS_F, 1, 0, self.root,
        EARTHREVO, -EPHEMSIMPLESET, self.ua)

        self.moon = Orbital('moon', self.root, 'moon_1k_tex.jpg',
        MOONRADIUS_F, MOONROT, -25, self.earth.system,
        MOONREVO, 0, self.moonax)
    
    def loadLight(self):
        #invisible spotlight to activate shadow casting (bypass bug)
        self.unspot = self.root.attachNewNode(Spotlight("Invisible spot"))
        self.unspot.setPos(0,0,self.ua)
        self.unspot.setHpr(0,90,0)
        self.unspot.node().getLens().setNearFar(0,0)
        self.root.setLight(self.unspot)
        
        #the light on the earth system
        self.light = self.root.attachNewNode(DirectionalLight("SunLight"))
        self.light.setPos(0,0,0)
        self.light.node().setScene(self.root)
        self.light.node().setShadowCaster(True, 2048, 2048)
        if SHOWFRUSTRUM :
            self.light.node().showFrustum()
        # a mask to define objects unaffected by light
        self.light.node().setCameraMask(BitMask32.bit(0)) 
        self.root.setLight(self.light)

        self.alight = self.root.attachNewNode(AmbientLight("Ambient"))
        p = 0.15
        self.alight.node().setColor(Vec4(p, p, p, 1))
        self.root.setLight(self.alight)

        # Create a special ambient light specially for the sun
        # so that it appears bright
        self.ambientLava = self.root.attachNewNode(AmbientLight("AmbientForLava"))
        self.sun.mod.setLight(self.ambientLava)
        self.sky.setLight(self.ambientLava)
        #Special light fo markers
        self.ambientMark = self.root.attachNewNode(AmbientLight("AmbientMark"))
        self.ambientMark.node().setColor(Vec4(0.8, 0.4, 0, 1))
        for obj in self.system :
            obj.marker.setLight(self.ambientMark)
            obj.axis.setLight(self.ambientMark)
        for obj in self.orbitals :
            obj.orbit_line.setLight(self.ambientMark)

        # Important! Enable the shader generator.
        self.root.setShaderAuto()

    def placeLight(self) :
        self.light.node().getLens().setFilmSize((2*self.moonax,self.moonax/2))
        self.light.node().getLens().setNearFar(self.earth.distance - self.moonax,
        self.earth.distance + self.moonax)
    
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
        for obj in [self.sun, self.earth, self.moon] :
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
        self.moon.shadow.lookAt(self.sun.mod)
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




class Scene(object) :
    '''system with time'''
    def __init__(self, world) :
        self.world = world
        self.loadEmpty()
        base.setBackgroundColor(0.2, 0.2, 0.2)    #Set the background to grey
        self.sys = System(self.root)
        #Time Control
        self.paused = False
        self.reverse = False
        
        self.simulSpeed = 1
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
    
    def placeCameraHome(self) :
        #Compute camera-sun distance from fov
        fov = base.camLens.getFov()[0]
        ua = self.sys.earth.distance
        margin = ua / 3
        c_s_dist = (ua + margin) / tan(radians(fov/2))
        self.world.home.setPos(0, -c_s_dist,ua/3)

    def lockHomeTask(self, task) :
        '''keep home in place'''
        self.placeCameraHome()
        return Task.cont
    
    #Timing control :
    #
    #
    def time_is_now(self) :
        self.simulSpeed = 1
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
            self.simulSpeed = 0.            
            self.paused = True
        else:
            self.simulSpeed = self.previousSpeed
            self.paused = False

    def reverseSpeed(self) :
        self.changeSpeed(-1)
        #button appearance should reflect reversed state
        if not self.reverse :
            self.reverse = True
        else :
            self.reverse = False

    def generate_speed_fade(self, speed) :
        #generate intervals to fade in and out from previous speed
        slow = LerpFunc(self.setSpeed, FREEZELEN,
        self.simulSpeed, 0.)
        fast = LerpFunc(self.setSpeed, FREEZELEN,
        0., speed)
        return slow, fast
        
    def time(self) :
        #time in days
        now = self.simulTime
        julian_time = astronomia.calendar.cal_to_jde(now.year,
        now.month, now.day, now.hour, now.minute, now.second,
        gregorian=True)
        return julian_time
    
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
            self.simulSpeed = 0.
        return Task.cont
    
    #Scaling control :
    #
    #
     
    def toggleScale(self) :
        '''a realistic scaling modifying :
        '''
        if not self.realist_scale :
            LerpFunc(self.scaleSystem,
             fromData=0,
             toData=1,
             duration=SCALELEN,
             blendType='easeIn').start()

            self.realist_scale = True
        else :
            LerpFunc(self.scaleSystem,
             fromData=1,
             toData=0,
             duration=SCALELEN,
             blendType='easeOut').start()
            
            self.realist_scale = False
    
    def scaleSystem(self, value) :
        '''scale the whole system from fantasist to realistic according
        to value (between 0. and 1.0)'''
        self.sys.earth.distance = linInt(value, UA, UA_F)
        self.sys.earth.radius = linInt(value, EARTHRADIUS, EARTHRADIUS_F)
        self.sys.moon.radius = linInt(value, MOONRADIUS, MOONRADIUS_F)
        self.sys.sun.radius = linInt(value, SUNRADIUS, SUNRADIUS_F)
        self.sys.moon.distance = linInt(value, MOONAX, MOONAX_F)
    
    def placeTask(self, task) :
        self.sys.place()
        self.sys.rotate(self.time())
        return Task.cont
    
    #Vizualisation control
    def toggleShadows(self) :
        if self.show_shadows :
            self.sys.hideShadows()
            self.show_shadows = False
        else :
            self.sys.showShadows()
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
            self.sys.moon.showShadow()
            self.sys.earth.showShadow()
        #we shouldn't hide the same shadow if we are going to follow or 
        #already following
        if self.world.Camera.hm.cameraTravel :
            name = self.world.Camera.hm.following.getName()
        #shouldn't bug if we aren't following any
        elif (not self.world.Camera.hm.cameraTravel 
        and self.world.Camera.hm.following != None) :
            name = self.world.Camera.hm.following.getName()
        else :
            name = None
        #specific hide
        if name == 'earth' :
            self.sys.earth.hideShadow()
        elif name == 'moon' :
            self.sys.moon.hideShadow()

    
