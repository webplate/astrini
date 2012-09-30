from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *

import time

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

