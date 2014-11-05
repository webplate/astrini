# -*- coding: utf-8-*- 
from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *

from math import tan, radians

#My Global config variables
from config import *
'''
This class is used to move camera WASD in FPS style
'''

class KeyboardMover(DirectObject):   #TRY REMOVE DIRECTOBJECT HERITAGE
    def __init__(self):
        #ballancer
        self.scrollSpeed = 2
        #moving camera vars
        self.pressedUp = False
        self.pressedDown = False
        self.pressedLeft = False
        self.pressedRight = False
        self.pressedFUp = False
        self.pressedFDown = False
        #setting up keys
        keys = ["z","s","q","d","t","g"]
        self.setupKeys(keys)
    
    def moveCamera(self,task):
        dt = globalClock.getDt()
        if self.pressedUp == True:
            camera.setY(camera, self.scrollSpeed*10*dt)
        if self.pressedDown == True:
            camera.setY(camera, -1*self.scrollSpeed*10*dt)
        if self.pressedLeft == True:
            camera.setX(camera, -1*self.scrollSpeed*10*dt)
        if self.pressedRight == True:
            camera.setX(camera, self.scrollSpeed*10*dt)
        if self.pressedFUp == True:
            camera.setZ(camera, self.scrollSpeed*10*dt)
        if self.pressedFDown == True:
            camera.setZ(camera, -1*self.scrollSpeed*10*dt)
        return Task.cont
    
    def setUnactive(self):
        self.ignoreAll()
        taskMgr.remove("keyboardMoverTask")
    
    def setActive(self):
        self.accept(self.up, self.pressKey, ["up"])
        self.accept(self.down, self.pressKey, ["down"])
        self.accept(self.left, self.pressKey, ["left"])
        self.accept(self.right, self.pressKey, ["right"])
        self.accept(self.FUp, self.pressKey, ["fup"])
        self.accept(self.FDown, self.pressKey, ["fdown"])
        self.accept(self.up+"-up", self.releaseKey, ["up"])
        self.accept(self.down+"-up", self.releaseKey, ["down"])
        self.accept(self.left+"-up", self.releaseKey, ["left"])
        self.accept(self.right+"-up", self.releaseKey, ["right"])
        self.accept(self.FUp+"-up", self.releaseKey, ["fup"])
        self.accept(self.FDown+"-up", self.releaseKey, ["fdown"])
        #self.ignore()
        taskMgr.add(self.moveCamera, "keyboardMoverTask")
    
    def releaseKey(self,key):
        if key == "up":
            self.pressedUp = False
        if key == "down":
            self.pressedDown = False
        if key == "left":
            self.pressedLeft = False
        if key == "right":
            self.pressedRight = False
        if key == "fup":
            self.pressedFUp = False
        if key == "fdown":
            self.pressedFDown = False
    
    def pressKey(self,key):
        if key == "up":
            self.pressedUp = True
        if key == "down":
            self.pressedDown = True
        if key == "left":
            self.pressedLeft = True
        if key == "right":
            self.pressedRight = True
        if key == "fup":
            self.pressedFUp = True
        if key == "fdown":
            self.pressedFDown = True
    
    def getKeys(self):
        keys = [self.up, self.down, self.left, self.right, self.FUp, self.FDown]
        return keys
    
    def setupKeys(self,keys):
        self.up = keys[0]
        self.down = keys[1]
        self.left = keys[2]
        self.right = keys[3]
        self.FUp = keys[4]
        self.FDown = keys[5]



class MouseMover(DirectObject):
    '''
This class is use to move mouse when in FPS (fly) mode
setActive() -> used to activate FPS mouse slide
setUnactive() -> inactivate FPS behaviour
'''
    def __init__(self):
        #camera rotation settings
        self.heading = 0
        self.pitch = 0
        #used to restore last mouse position in editor
        self.lastCoo = []
    
    def flyCamera(self,task):
        # figure out how much the mouse has moved (in pixels)
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, 300, 300):
            self.heading = self.heading - (x - 300) * 0.1
            self.pitch = self.pitch - (y - 300) * 0.1
        if (self.pitch < -85): self.pitch = -85
        if (self.pitch >  85): self.pitch =  85
        base.camera.setH(self.heading)
        base.camera.setP(self.pitch)
        return Task.cont
    
    def hideMouse(self):
        #hiding mouse
        props = WindowProperties()
        props.setCursorHidden(True) 
        base.win.requestProperties(props)
    
    def showMouse(self):
        props = WindowProperties()
        props.setCursorHidden(False) 
        base.win.requestProperties(props)
        
    def setActive(self):
        #hiding mouse
        self.hideMouse()
        #storing infos
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        self.lastCoo = [x,y]
        #start activating this shit
        base.win.movePointer(0,300,300)
        taskMgr.add(self.flyCamera, "mouseMoverTask")
    
    def setUnactive(self):
        #showing mouse
        self.showMouse()
        #then removing task and resetting pointer to previous position
        taskMgr.remove("mouseMoverTask")
        base.win.movePointer(0,self.lastCoo[0],self.lastCoo[1])
        
class Camera(DirectObject):
    def __init__(self, world):
        self.world = world
        #keyboard/mouse mover
        self.km = KeyboardMover()
        self.mm = MouseMover()
        #disabling mouse by default
        base.disableMouse()
        #setting status
        self.state = "static"
        #default config when just opened
        self.mm.showMouse()
        self.setUtilsActive()
        self.placeCameraHome()
        #low priority to prevent jitter of camera
        taskMgr.add(self.lockCameraTask, "lockCameraTask", priority=25)
        taskMgr.add(self.lockHomeTask, "lockHomeTask", priority=3)
        
        self.setNearFar(0.1,CAMERAFAR)
        self.setFov(45)
    
    def getFov(self):
        return base.camLens.getFov()
    
    def setNearFar(self,v1,v2):
        base.camLens.setNearFar(v1,v2)
    
    def setFov(self,value):
        base.camLens.setFov(value)

    '''
    This is an interface method used to switch between fly and static 
    modes dynamically through a simple string
    '''

    def setState(self,s):
        #if there is a real change in camera state
        if s != self.state:
            #actually change state
            if s == "fly":
                #re-enabling all gui elements
                self.mm.setActive()
                self.km.setActive()
            if s == "static":
                self.mm.setUnactive()
                self.km.setUnactive()
            #changing state variable at the end of method execution
            self.state = s
    
    def setUtilsActive(self):
        self.accept("tab", self.toggleView)
    
    def setUtilsUnactive(self):
        self.ignore("tab")
    
    def toggleState(self):
        if self.state == "static":
            self.setState("fly")
        else:
            self.setState("static")
    
    def toggleView(self):
        if self.state == "fly":
            #myGui.showAll()  to be removed soon
            self.world.InputHandler.setActive()
        if self.state == "static":
            #myGui.hideAll()  to be removed soon
            self.world.InputHandler.setInactive()
        #switching camera in any case
        self.toggleState()

    def placeCameraHome(self) :
        #Compute camera-sun distance from fov
        fov = self.getFov()[0]
        ua = self.world.scene.sys.earth.distance
        margin = ua / 3
        c_s_dist = (ua + margin) / tan(radians(fov/2))
        self.world.home.setPos(0, -c_s_dist,ua/3)

    def lockCameraTask(self, task) :
        """alignment contraints""" 
        #align if necessary
        if self.world.following != None :
            camera.setPos(self.world.following.getPos(render))
        if self.world.looking != None :
            camera.lookAt(self.world.focus)
        return Task.cont
        
    def lockHomeTask(self, task) :
        '''keep home in place'''
        self.placeCameraHome()
        return Task.cont
