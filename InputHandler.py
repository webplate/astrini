# -*- coding: utf-8-*- 
from direct.showbase.DirectObject import DirectObject

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
        
        self.accept("a",self.world.Camera.hm.stop_follow)
        self.accept("w",self.world.Camera.hm.stop_look)
        
        self.accept("e",self.world.Camera.hm.follow,[self.world.earth])
        self.accept("control-e",self.world.Camera.hm.look,[self.world.earth])
        
        self.accept("r",self.world.Camera.hm.follow,[self.world.moon])
        self.accept("control-r",self.world.Camera.hm.look,[self.world.moon])
        
        self.accept("f",self.world.Camera.hm.follow,[self.world.sun])
        self.accept("control-f",self.world.Camera.hm.look,[self.world.sun])
