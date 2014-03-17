#!/usr/bin/env python
# -*- coding: utf-8-*- 
#
#  Simulation for astronomical initiation
#  by Glen Lomax
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
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
#
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from panda3d.core import *

#
# Task declaration import 
from direct.task import Task

#
# Default classes used to handle input and camera behaviour
# Useful for fast prototyping
#
from Camera import Camera
from InputHandler import InputHandler
#Drawing functions
import graphics
#Misc imports
from math import radians, tan, log, ceil

cardMaker = CardMaker('CardMaker')

def nextPowOf2(n):
    return 2**int(ceil(log(n, 2)))


def makeGeom(filename):
    """create geom from png and take care of power of two
    texture issues to permit pixel perfect blitting"""
    origImage = PNMImage()
    assert origImage.read(filename)
    oldWidth = origImage.getXSize()
    oldHeight = origImage.getYSize()
    newWidth = nextPowOf2(oldWidth)
    newHeight = nextPowOf2(oldHeight)

    newImage = PNMImage(newWidth, newHeight)
    if origImage.hasAlpha():
        newImage.addAlpha()
    newImage.copySubImage(origImage, 0, 0, 0, 0)
   
    tex = Texture()
    tex.load(newImage)
   
    cardMaker.setFrame(0, oldWidth, 0, oldHeight)

    fU = float(oldWidth)/newWidth
    fV = float(oldHeight)/newHeight

    # cardMaker.setHasUvs(True)
    cardMaker.setUvRange(Point2(0, 0), Point2(fU, fV))

    npCard = NodePath(cardMaker.generate())
    npCard.setTexture(tex)
    npCard.setTexOffset(TextureStage.getDefault(), 0, 1-fV)
    if origImage.hasAlpha():
        npCard.setTransparency(TransparencyAttrib.MAlpha)
   
    return npCard

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

        #Scene initialization
        self.initCamera()
        self.initScene()

        # Prepare locks (following procedures etc...)
        self.following = None
        self.looking = None
        self.tilted = False
        self.inclined = False
        self.realist = False
        # Add Tasks procedures to the task manager.
        #low priority to prevent jitter of camera
        self.taskMgr.add(self.lockTask, "lockTask", priority=25)
        self.taskMgr.add(self.printTask, "PrintTask")
        #Interface
        self.loadInterface()


    def initScene(self):
        self.simulSpeed = 1
        
        #variables to control the relative speeds of spinning and orbits in the
        #simulation
        #Number of seconds a full rotation of Earth around the sun should take
        secondsInDay = SECONDSINDAY
        self.yearscale = EARTHREVO * secondsInDay
        #Number of seconds a day rotation of Earth should take.
        self.dayscale = secondsInDay
        
        self.orbitscale =  UA              #Orbit scale
        self.sizescale = EARTHRADIUS              #Planet size scale
        self.sunradius = SUNRADIUS
        self.earthTilt = EARTHTILT
        self.moonTilt = MOONTILT
        self.moonIncli = MOONINCL
        
        base.setBackgroundColor(0, 0, 0)    #Set the background to black
        self.loadPlanets()                #Load and position the models
        self.loadMarkers()
        self.drawOrbits()
        self.initLight()                # light the scene
        #Finally, we call the rotatePlanets function which puts the planets,
        #sun, and moon into motion.
        self.rotatePlanets()
        self.updateSpeed()

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
        
    def getSceneNode(self):
        return self.mainScene
        
    def initCamera(self):
        #Camera initialization
        fov = self.Camera.getFov()[0]
        #Compute camera-sun distance from fov
        margin = UA / 3
        c_s_dist = (UA + margin) / tan(radians(fov/2))
        camera.setPos( 0, -c_s_dist,UA/3)          #Set the camera position (X, Y, Z)
        camera.lookAt(0.,0.,0.)
        
    
    def changeSpeed(self, factor):
        self.simulSpeed *= factor
        self.updateSpeed()
        
    def toggleSpeed(self):
        if self.simulSpeed != 0.001:
            self.previousSpeed = self.simulSpeed
            self.simulSpeed = 0.001
        else:
            self.simulSpeed = self.previousSpeed
        self.updateSpeed()

    def follow(self, identity):
        if identity == "earth" :
            self.following = self.earth
        elif identity == "moon" :
            self.following = self.moon
        elif identity == "sun" :
            self.following = self.sun
        else:
            self.following = None

    def look(self, identity):
        if identity == "earth" :
            self.looking = self.earth
        elif identity == "moon" :
            self.looking = self.moon
        elif identity == "sun" :
            self.looking = self.sun
        else:
            self.looking = None

    def unTilt(self):
        if self.tilted:
            self.dummy_earth.setHpr(0, 0, 0)
            self.tilted = False
        else:
            self.dummy_earth.setHpr(0, self.earthTilt, 0)
            self.tilted = True

    def unIncl(self):
        if self.inclined:
            self.dummy_root_moon.setHpr(0, 0, 0)
            self.inclined = False
        else:
            self.dummy_root_moon.setHpr(0, self.moonIncli, 0)
            self.inclined = True

    def realism(self):
        if self.realist:
            
            self.realist = False
        else:
            
            self.realist = True
    
    #Set the simulation play rate
    def updateSpeed(self):
        #prevent complete stop (and reset of simulation)
        if self.simulSpeed != 0 :
            self.day_period_sun.setPlayRate(self.simulSpeed)
            self.orbit_period_earthsystem.setPlayRate(self.simulSpeed)
            self.day_period_earth.setPlayRate(self.simulSpeed)
            self.orbit_period_moon.setPlayRate(self.simulSpeed)
            self.day_period_moon.setPlayRate(self.simulSpeed)
    
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
        self.root_earth = render.attachNewNode('root_earth')
        
        self.earth_system = self.root_earth.attachNewNode('earth_system')
        self.earth_system.setPos(self.orbitscale,0,0)
        
        self.dummy_earth = self.earth_system.attachNewNode('dummy_earth')
        #self.dummy_earth.setHpr(0, self.earthTilt, 0)
        self.dummy_earth.setEffect(CompassEffect.make(render))
        
        #The moon orbits Earth, not the sun
        self.dummy_root_moon = self.earth_system.attachNewNode('dummy_root_moon')
        #self.dummy_root_moon.setHpr(0, self.moonIncli, 0)
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

    def rotatePlanets(self):
        #rotatePlanets creates intervals to actually use the hierarchy we created
        #to turn the sun, planets, and moon to give a rough representation of the
        #solar system.
        self.day_period_sun = self.sun.hprInterval(self.dayscale * SUNROT,
        Vec3(360, 0, 0))

        self.orbit_period_earthsystem = self.root_earth.hprInterval(
          self.yearscale, Vec3(360, 0, 0))
        self.day_period_earth = self.earth.hprInterval(
          self.dayscale, Vec3(360, 0, 0))

        self.orbit_period_moon = self.root_moon.hprInterval(
          (self.dayscale * MOONREVO), Vec3(360, 0, 0))
        self.day_period_moon = self.moon.hprInterval(
          (self.dayscale * MOONROT), Vec3(360, 0, 0))

        self.day_period_sun.loop()
        self.orbit_period_earthsystem.loop()
        self.day_period_earth.loop()
        self.orbit_period_moon.loop()
        self.day_period_moon.loop()

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
        self.moonAxMarker = graphics.makeCross(2*self.sizescale)
        self.moonAxMarker.reparentTo(self.dummy_moon)
        self.moonAxMarker.hide(BitMask32.bit(0))# markers are not affected by sunlight

    def loadInterface(self) :
        paths = ('images/button_ready.png',
             'images/button_click.png',
             'images/button_rollover.png',
             'images/button_disabled.png')
        b_map = [makeGeom(name) for name in paths]
        #Container
        w, h = base.win.getXSize(), base.win.getYSize()
        bw, bh = BUTTONSIZE
        b_cont = DirectFrame(frameSize=(-(bw+bw/2), bw+bw/2, -h/2, h/2),
            frameColor=(1,1,1,0.2),
            pos=(bw+bw/2, -1, -h/2))
        b_cont.reparentTo(pixel2d)

        def add_button(name, i, j, command, args, parent) :
            """add button as on a button grid on parent"""
            left, right, bottom, top = parent.bounds
            w, h = right - left, top - bottom
            pos = (-w/2+bw*i,0,h/2-bh-bh*j)
            b = DirectButton(text = name,
                text_scale = (bw/3, bh/2),
                text_pos=(bw/2, bh/2),
                pos=pos,
                command=command, extraArgs=args,
                geom=b_map,
                relief=None,
                pressEffect=False,
                parent=parent)
            return b

        def add_label(name, i, j, parent) :
            """add text label as on a button grid on parent"""
            left, right, bottom, top = parent.bounds
            w, h = right - left, top - bottom
            b = DirectLabel(text = name,
                text_scale=(bw/3, bh/2),
                text_fg=(1,1,1,1),
                pos=(-w/2+bw/2+bw*i,0,h/2-bh/2-bh*j),
                relief=None,
                parent=parent)
            return b
        
        #Buttons to follow
        add_label('Go to : ', 1, 0, b_cont)
        add_button('Earth', 0, 1, self.follow, ['earth'], b_cont)
        add_button('Moon', 1, 1, self.follow, ['moon'], b_cont)
        add_button('Sun', 2, 1, self.follow, ['sun'], b_cont)
        #and to look at
        add_label('Look at : ', 1, 2, b_cont)
        add_button('Earth', 0, 3, self.look, ['earth'], b_cont)
        add_button('Moon', 1, 3, self.look, ['moon'], b_cont)
        add_button('Sun', 2, 3, self.look, ['sun'], b_cont)
        #and to change speed
        add_label('Time : ', 1, 4, b_cont)
        add_button('-', 0, 5, self.changeSpeed, [1./2], b_cont)
        add_button('+', 1, 5, self.changeSpeed, [2], b_cont)
        add_button('++', 2, 5, self.changeSpeed, [100], b_cont)
        #factual changes
        add_label('Factual changes : ', 1, 6, b_cont)
        add_button('Moon', 0, 7, self.unIncl, [], b_cont)
        add_button('Earth', 1, 7, self.unTilt, [], b_cont)


    ## TASKS :
    #
    def printTask(self, task) :
        #~ print self.camera.getPos()
        #~ print self.simulSpeed
        return Task.cont

    def lockTask(self, task) :
        """alignment contraints""" 
        #lighting follows earth
        self.light.lookAt(self.earth)
        #align if necessary
        if self.following != None :
            camera.setPos(self.following.getPos(self.render))
        if self.looking != None :
            camera.lookAt(self.looking)
        return Task.cont

    def updateMarkers(self, task):
    
        return Task.cont

#a virtual argument to bypass packing bug
def main(arg=None):
    w = World()
    w.run()
    return 0

if __name__ == '__main__':
    main()
