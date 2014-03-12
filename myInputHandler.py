from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *

import sys, time

class InputHandler(DirectObject):
    def __init__(self):
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
        self.accept("i",myApp.changeSpeed,[-1])
        self.accept("k",myApp.changeSpeed,[1./2])
        self.accept("l",myApp.changeSpeed,[2])
        self.accept("m",myApp.changeSpeed,[1000])
        self.accept("n",myApp.toggleSpeed)
        
        self.accept("a",myApp.follow,[None])
        self.accept("w",myApp.look,[None])
        
        self.accept("e",myApp.follow,["earth"])
        self.accept("control-e",myApp.look,["earth"])
        self.accept("shift-e",myApp.unTilt)
        
        self.accept("r",myApp.follow,["moon"])
        self.accept("control-r",myApp.look,["moon"])
        self.accept("shift-r",myApp.unIncl)
        
        self.accept("f",myApp.follow,["sun"])
        self.accept("control-f",myApp.look,["sun"])
        
        self.accept("b",myApp.realism)
        
        self.accept("p", self.pressKey, ["p"])
        self.accept("p-up", self.releaseKey, ["p"])
        #self.ignore()
        taskMgr.add(self.modObjects, "objectModifierTask")
    
    def releaseKey(self,key):
        myCamera.ce.keyReleased()
        
        if key == "p":
            self.pressedP = False
    
    def pressKey(self,key):
        #default behaviour when hiding camera
        myCamera.ce.keyPressed()
        
        if key == "p":
            self.pressedP = True

