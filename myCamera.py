from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *

import libpanda
import math 

#My Global config variables
from config import *
'''
This class is used to move camera WASD in FPS style
'''

class KeyboardMover(DirectObject):
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

class CameraEvents(DirectObject):
    def __init__(self):
        pass
    
    def keyPressed(self):
        '''
        Customize input handler keypress event
        
        TODO: insert debug infos here to help other progs
        
        '''
        pass
    
    def keyReleased(self):
        '''
        Customize input handler keyrelease event
        
        TODO: insert debug infos here to help other progs
        
        '''
        pass

'''
This class is use to move mouse when in FPS (fly) mode
setActive() -> used to activate FPS mouse slide
setUnactive() -> inactivate FPS behaviour
'''

class MouseMover(DirectObject):
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
        
class MyCamera(DirectObject):
    def __init__(self, world):
        self.world = world
        #keyboard/mouse mover
        self.km = KeyboardMover()
        self.mm = MouseMover()
        #Camera events
        self.ce = CameraEvents()
        #disabling mouse by default
        base.disableMouse()
        #setting status
        self.state = "static"
        
        self.setNearFar(1.0,10000 * UA)
        self.setFov(45)
    
    def getKeyboardMover(self):
        return self.km
    
    def getMouseMover(self):
        return self.km
    
    def getSelectionTool(self):
        return self.st
    
    def getFov(self):
        return base.camLens.getFov()
    
    def setNearFar(self,v1,v2):
        base.camLens.setNearFar(v1,v2)
    
    def setFov(self,value):
        base.camLens.setFov(value)

    '''
    This is an interface method used to switch between fly and static 
    modes dinamically through a simple string
    '''
    def getSelected(self):
        return self.st.listSelected
    
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
        #self.accept("f", self.ps.toggleFullscreen)
    
    def setUtilsUnactive(self):
        self.ignore("tab")
        self.ignore("f")
    
    def toggleState(self):
        if self.state == "static":
            self.setState("fly")
        else:
            self.setState("static")
    
    def toggleView(self):
        if self.getState() == "fly":
            #myGui.showAll()  to be removed soon
            self.world.myInputHandler.setActive()
        if self.getState() == "static":
            #myGui.hideAll()  to be removed soon
            self.world.myInputHandler.setInactive()
        #switching camera in any case
        self.toggleState()
    
    def getState(self):
        return self.state
