from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *

import sys, time

class InputHandler(DirectObject):
    def __init__(self, world):
        self.world = world
        #setting it active by default
        self.setActive()
        
        self.pressedP = False
    
    
    def modObjects(self,task):
        dt = globalClock.getDt()
        
        #resolving P event
        if self.pressedP == True:
            # figure out how much the mouse has moved (in pixels)
            millis = int(round(time.time() * 1000))
            print "ping happened at ",millis,"!"
        
        return Task.cont
    
    def setInactive(self):
        # Main Modifier
        self.ignoreAll()
        taskMgr.remove("objectModifierTask")
    
    def setActive(self):
        # Main Modifier
        base.accept("escape", sys.exit)
        #My shortcuts
        self.accept("i",self.world.changeSpeed,[-1])
        self.accept("k",self.world.changeSpeed,[1./2])
        self.accept("l",self.world.changeSpeed,[2])
        self.accept("m",self.world.changeSpeed,[1000])
        self.accept("n",self.world.toggleSpeed)
        
        self.accept("a",self.world.follow,[None])
        self.accept("w",self.world.look,[None])
        
        self.accept("e",self.world.follow,["earth"])
        self.accept("control-e",self.world.look,["earth"])
        self.accept("shift-e",self.world.unTilt)
        
        self.accept("r",self.world.follow,["moon"])
        self.accept("control-r",self.world.look,["moon"])
        self.accept("shift-r",self.world.unIncl)
        
        self.accept("f",self.world.follow,["sun"])
        self.accept("control-f",self.world.look,["sun"])
        
        self.accept("b",self.world.realism)
        
        self.accept("p", self.pressKey, ["p"])
        self.accept("p-up", self.releaseKey, ["p"])
        #self.ignore()
        taskMgr.add(self.modObjects, "objectModifierTask")
    
    def releaseKey(self,key):
        self.world.myCamera.ce.keyReleased()
        
        if key == "p":
            self.pressedP = False
    
    def pressKey(self,key):
        #default behaviour when hiding camera
        self.world.myCamera.ce.keyPressed()
        
        if key == "p":
            self.pressedP = True

