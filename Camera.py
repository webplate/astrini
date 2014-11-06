# -*- coding: utf-8-*- 
from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *
#Sequence and parallel for intervals
from direct.interval.IntervalGlobal import *

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
This class is used to move mouse when in FPS (fly) mode
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

class HunterMover(DirectObject):
    '''
This class is used to hunt planetoids
(look and follow them softly)
'''
    def __init__(self, scene):
        self.scene = scene
        #Prepare locks (following procedures etc...)
        self.cameraTravel = False
        self.focusTravel = False
        self.timeTravel = False
        self.speed = self.scene.simulSpeed
        self.sequences = []
        self.looking = None
        self.following = None
    
    def setActive(self):
        #low priority to prevent jitter of camera
        taskMgr.add(self.moveCameraTask, "hunterMoverTask", priority=25)
    
    def setUnactive(self):
        #then removing task and resetting pointer to previous position
        taskMgr.remove("hunterMoverTask")
        taskMgr.remove("lockHomeTask")
    
    def softMove(self, nod, posFunc) :
        #select correct speed of reference
        if not self.timeTravel :
            self.speed = self.scene.simulSpeed
            self.timeTravel = True
        #stop flow of time while traveling
        slow, fast = self.scene.generate_speed_fade(self.speed)
        
        travel = nod.posInterval(TRAVELLEN,
            posFunc(), blendType='easeInOut')
        
        check = Func(self.checkTimeTravel)
        return slow, fast, travel, check
    
    def checkTimeTravel(self) :
        for s in self.sequences :
            if s.isPlaying() :
                self.timeTravel = True
                return
        self.sequences = []
        self.timeTravel = False

    def moveCameraTask(self, task) :
        """alignment contraints""" 
        #align if necessary
        if self.looking != None :
            camera.lookAt(self.scene.focus)
        return Task.cont
        
    def get_curr_look_rel_pos(self) :
        return self.looking.getPos(render)
        
    def get_curr_follow_rel_pos(self) :
        return self.following.getPos(render)

    def stop_follow(self) :
        self.following = None

    def lock_camera(self) :
        self.cameraTravel = False
        camera.reparentTo(self.following)
        camera.setPos(0, 0, 0)

    def unlock_camera(self) :
        camera.wrtReparentTo(render)

    def follow(self, identity):
        #if new destination and not already trying to reach another
        if self.following != identity and not self.cameraTravel :
            self.following = identity
            self.cameraTravel = True
            #hide tubular shadow of followed object
            self.scene.updateShadows()
            
            #select correct speed of reference
            if not self.timeTravel :
                self.speed = self.scene.simulSpeed
                self.timeTravel = True
            #stop flow of time while traveling
            slow, fast = self.scene.generate_speed_fade(self.speed)
            
            travel = camera.posInterval(TRAVELLEN,
            self.get_curr_follow_rel_pos, blendType='easeInOut')
            
            check = Func(self.checkTimeTravel)
            
            #slow sim, release, travel, lock, resume speed, stop time warp
            sequence = Sequence(slow, Func(self.unlock_camera),
            travel, Func(self.lock_camera), fast, check)
            self.sequences.append(sequence)
            sequence.start()

    def stop_look(self) :
        self.looking = None

    def lock_focus(self) :
        self.focusTravel = False
        self.scene.focus.reparentTo(self.looking)
        self.scene.focus.setPos(0, 0, 0)

    def unlock_focus(self) :
        self.scene.focus.wrtReparentTo(render)

    def look(self, identity) :
        #if new target
        if self.looking != identity and not self.focusTravel :
            self.looking = identity
            self.focusTravel = True
            
            #select correct speed of reference
            if not self.timeTravel :
                self.speed = self.scene.simulSpeed
                self.timeTravel = True
            #stop flow of time while traveling
            slow, fast = self.scene.generate_speed_fade(self.speed)
            
            travel = self.scene.focus.posInterval(TRAVELLEN,
                self.get_curr_look_rel_pos, blendType='easeInOut')
            
            check = Func(self.checkTimeTravel)
                
            sequence = Sequence(slow, Func(self.unlock_focus),
                travel, Func(self.lock_focus), fast, check)
            self.sequences.append(sequence)
            sequence.start()


class Camera(DirectObject):
    def __init__(self, world):
        self.world = world
        #keyboard/mouse mover
        self.km = KeyboardMover()
        self.mm = MouseMover()
        #interface mover
        self.hm = HunterMover(self.world.scene)
        #disabling mouse by default
        base.disableMouse()
        #setting status
        self.state = "static"
        #default config when just opened
        self.mm.showMouse()
        self.hm.setActive()
        self.setUtilsActive()
        
        self.setNearFar(0.1,CAMERAFAR)
        self.setFov(45)

    
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
                self.hm.setUnactive()
            if s == "static":
                self.mm.setUnactive()
                self.km.setUnactive()
                self.hm.setUnactive()
            if s == "hunter":
                self.mm.setUnactive()
                self.km.setUnactive()
                self.hm.setActive()
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
