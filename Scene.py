# -*- coding: utf-8-*- 
#Core functions of PandaEngine
from panda3d.core import *
# Task declaration import 
from direct.task import Task

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
    def __init__(self, name, parent, tex, radius, period = 1, offset = 0) :
        self.name = name
        self.radius = radius
        self.period = period
        self.offset = offset
        self.load(tex)
        self.mod.reparentTo(parent)
        
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
    def __init__(self, name, parent, tex, radius, period, offset,
    root, system, orbit_period, orbit_offset, distance) :
        Planetoid.__init__(self, name, parent, tex, radius, period , offset)
        self.root = root
        self.system = system
        self.orbit_period = orbit_period
        self.orbit_offset = orbit_offset
        self.distance = distance
        
        self.loadShadow()
        self.loadOrbit()
    
    def orbit(self, julian_time) :
        self.root.setHpr(
    ((360 / self.orbit_period) * julian_time % 360) - self.orbit_offset,
        0, 0)
    
    def rotate(self, time) :
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
    '''sun earth and moon'''
    def __init__(self):
        self.initAstrofacts()
        self.loadPlanets()
        self.loadLight()
        self.system = [self.sun, self.earth, self.moon]
        # Add Tasks procedures to the task manager.
        #lower priority to prevent jitter of objects
        taskMgr.add(self.lockTask, "lockTask", priority=26)
    
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
        
    def loadPlanets(self):
        #Create the dummy nodes
        #the skeleton of the system
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
        self.dummy_moon.setEffect(CompassEffect.make(render))
        
        #Load the sky
        self.sky = loader.loadModel("models/solar_sky_sphere")
        self.sky_tex = loader.loadTexture("models/stars_1k_tex.jpg")
        self.sky.setTexture(self.sky_tex, 1)
        #~ self.sky.hide(BitMask32.bit(0))
                
        self.sun = Planetoid('sun', render, 'sun_1k_tex.jpg',
        self.sunradius, SUNROT, 0)
        
        self.earth = Orbital('earth', self.dummy_earth, 'earth_1k_tex.jpg',
        self.earthradius, 1, 0, self.root_earth, self.earth_system,
        self.yearscale, -EPHEMSIMPLESET, self.ua)
                
        self.moon = Orbital('moon', self.dummy_moon, 'moon_1k_tex.jpg',
        self.moonradius, MOONROT, -25, self.root_moon, self.moon_system,
        MOONREVO, 0, self.moonax)
    
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
        self.light.node().showFrustum()
        # a mask to define objects unaffected by light
        self.light.node().setCameraMask(BitMask32.bit(0)) 
        render.setLight(self.light)

        self.alight = render.attachNewNode(AmbientLight("Ambient"))
        p = 0.15
        self.alight.node().setColor(Vec4(p, p, p, 1))
        render.setLight(self.alight)

        # Create a special ambient light specially for the sun
        # so that it appears bright
        self.ambientLava = render.attachNewNode(AmbientLight("AmbientForLava"))
        self.sun.mod.setLight(self.ambientLava)
        self.sky.setLight(self.ambientLava)
        #Special light fo markers
        self.ambientMark = render.attachNewNode(AmbientLight("AmbientMark"))
        self.ambientMark.node().setColor(Vec4(0.8, 0.4, 0, 1))
        for obj in [self.sun, self.earth, self.moon] :
            obj.marker.setLight(self.ambientMark)
            obj.axis.setLight(self.ambientMark)
        for obj in [self.earth, self.moon] :
            obj.orbit_line.setLight(self.ambientMark)


        # Important! Enable the shader generator.
        render.setShaderAuto()

    def placeLight(self) :
        self.light.node().getLens().setFilmSize((2*self.moonax,self.moonax/2))
        self.light.node().getLens().setNearFar(self.ua - self.moonax, self.ua + self.moonax)

    def place(self) :
        for obj in [self.sun, self.earth, self.moon] :
            obj.place()
        self.placeLight()
    
    def lockTask(self, task) :
        """alignment contraints""" 
        #lighting follows earth
        self.light.lookAt(self.earth.mod)
        #casted shadows should remain aligned with sun
        self.earth.shadow.lookAt(self.sun.mod)
        self.moon.shadow.lookAt(self.sun.mod)
        self.place()
        return Task.cont


class Scene(object) :
    '''system'''
    def __init__(self):
        self.initEmpty()
        base.setBackgroundColor(0.2, 0.2, 0.2)    #Set the background to grey
        self.sys = System()
        self.sys.place()
        
        for obj in self.sys.system :
            obj.showMarker()
        
        self.sys.earth.showShadow()
        self.sys.earth.showOrbit()
        self.sys.earth.showAxis()
        self.sys.moon.showShadow()
        self.sys.moon.showOrbit()

    def initEmpty(self) :
        #Create the dummy nodes
        self.home = render.attachNewNode('home')
        self.home.setName('home')
        self.focus = render.attachNewNode('focus')
        self.focus.setName('focus')
    
    def time(self) :
        #time in days
        now = self.simulTime
        julian_time = calendar.cal_to_jde(now.year, now.month, now.day,
        now.hour, now.minute, now.second, gregorian=True)
