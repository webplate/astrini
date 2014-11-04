from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *

import sys, time

class InputHandler(DirectObject):
    def __init__(self, world):
        self.world = world
        #setting it active by default
        self.setActive()

    def setInactive(self):
        # Main Modifier
        self.ignoreAll()
    
    def setActive(self):
        # Main Modifier
        base.accept("escape", sys.exit)
        #My shortcuts
        
        self.accept("a",self.world.stop_follow)
        self.accept("w",self.world.stop_look)
        
        self.accept("e",self.world.follow,[self.world.earth])
        self.accept("control-e",self.world.look,[self.world.earth])
        self.accept("shift-e",self.world.toggleTilt)
        
        self.accept("r",self.world.follow,[self.world.moon])
        self.accept("control-r",self.world.look,[self.world.moon])
        self.accept("shift-r",self.world.toggleIncl)
        
        self.accept("f",self.world.follow,[self.world.sun])
        self.accept("control-f",self.world.look,[self.world.sun])
