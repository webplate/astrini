# -*- coding: utf-8-*- 
#Core functions of PandaEngine
from panda3d.core import *
#GUI elements
from direct.gui.DirectGui import *
# Task declaration import 
from direct.task import Task

#Drawing functions
import graphics
#My Global config variables
from config import *
#Interface content
import content

class Interface(object) :
    '''the gui of astrini'''
    def __init__(self, world) :
        self.world = world
        #load fonts
        self.condensed_font = loader.loadFont('fonts/Ubuntu-C.ttf')
        self.mono_font = loader.loadFont('fonts/UbuntuMono-R.ttf')
        
        self.loadInterface()
        #do not update interface every frame (no use slowdown)
        taskMgr.doMethodLater(INTERFACEDELAY, self.interfaceTask, "interfaceTask")
        taskMgr.add(self.buttonsTask, "buttonsTask", priority=5)

    def loadInterface(self) :
        paths = ('images/button_ready.png',
             'images/button_click.png',
             'images/button_rollover.png',
             'images/button_disabled.png')
        self.b_map = [graphics.makeGeom(name) for name in paths]
        #an alternate map to show activated buttons
        paths = ('images/button_activated.png',
             'images/button_click.png',
             'images/button_activated.png',
             'images/button_disabled.png')
        self.b_map_acti = [graphics.makeGeom(name) for name in paths]
        #Container for main interface
        w, h = base.win.getXSize(), base.win.getYSize()
        bw, bh = BUTTONSIZE
        self.b_cont = DirectFrame(frameSize=(-(bw+bw/2), bw+bw/2, -h/2, h/2),
            frameColor=(1,1,1,0.3),
            pos=(bw+bw/2, -1, -h/2))
        self.b_cont.reparentTo(pixel2d)

        def add_button(name, i, j, command, args, parent) :
            """add button as on a button grid on parent"""
            left, right, bottom, top = parent.bounds
            w, h = right - left, top - bottom
            pos = (-w/2+bw*i,0,h/2-bh-bh*j)
            b = DirectButton(text = name,
                text_font=self.condensed_font,
                text_scale = (bw/3, bh/1.3),
                text_pos=(bw/2, bh/3),
                pos=pos,
                command=command, extraArgs=args,
                geom=self.b_map,
                relief=None,
                pressEffect=False,
                parent=parent)
            return b

        def add_label(name, i, j, parent) :
            """add text label as on a button grid on parent"""
            left, right, bottom, top = parent.bounds
            w, h = right - left, top - bottom
            b = DirectLabel(text = name,
                text_font=self.condensed_font,
                text_scale=(bw/3, bh/1.3),
                text_pos=(bw/2, bh/3),
                text_fg=(1,1,1,1),
                text_shadow=(0,0,0,0.9),
                pos = (-w/2+bw*i,0,h/2-bh-bh*j),
                relief=None,
                parent=parent)
            return b

        def add_textarea(lines, parent) :
            """add text area filling parent
            lines is a list of strings, one str per line"""
            left, right, bottom, top = parent.bounds
            w, h = right - left, top - bottom
            out = []
            for i, line in enumerate(lines) :
                t = DirectLabel(text = line,
                    text_font=self.condensed_font,
                    text_scale=(bw/3, bh/1.3),
                    text_pos=(bw/2, bh/3),
                    text_fg=(0,0,0,1),
                    text_shadow=(1,1,1,0.7),
                    pos = (-bw/2, 0, h/2-bh-bh*i),
                    relief=None,
                    parent=parent)
                out.append(t)
            return out
        
        def add_dialog(size) :
            '''a frame with a close button
            the size must be set according to button sizes'''
            cont = DirectFrame(frameSize=size,
            frameColor=(1,1,1,0.8),
            pos=(w/2, -1, -h/2))
            close_button_coordinate = (-size[0] + size[1])/bw - 1
            add_button('X', close_button_coordinate, 0,
            self.hide_dialog, [cont], cont)
            return cont
            
        #about dialog
        text = content.about
        
        self.about_dialog = add_dialog((-5*bw, 5*bw, -10*bh, 10*bh))
        add_textarea(text, self.about_dialog)
        
        #Buttons to follow
        j = 1
        follow = self.world.Camera.hm.follow
        add_label('Go to : ', 1, j, self.b_cont)
        self.earth_b = add_button('Earth', 0, j+1, follow,
        [self.world.earth], self.b_cont)
        self.moon_b = add_button('Moon', 1, j+1, follow,
        [self.world.moon], self.b_cont)
        self.sun_b = add_button('Sun', 2, j+1, follow,
        [self.world.sun], self.b_cont)
        self.ext_b = add_button('Ext', 2, j+2, follow,
        [self.world.home], self.b_cont)
        #and to look at
        j += 4
        look = self.world.Camera.hm.look
        add_label('Look at : ', 1, j, self.b_cont)
        self.earth_lb = add_button('Earth', 0, j+1, look,
        [self.world.earth], self.b_cont)
        self.moon_lb = add_button('Moon', 1, j+1, look,
        [self.world.moon], self.b_cont)
        self.sun_lb = add_button('Sun', 2, j+1, look,
        [self.world.sun], self.b_cont)
        #and to change speed
        j += 3
        add_label('Speed : ', 0, j, self.b_cont)
        self.speedlabel = add_label('Speed', 1, j, self.b_cont)
        #may change optimization 
        self.speedlabel['textMayChange'] = True
        add_button('-', 0, j+1, self.world.scene.changeSpeed, [1./2], self.b_cont)
        add_button('+', 1, j+1, self.world.scene.changeSpeed, [2], self.b_cont)
        add_button('++', 2, j+1, self.world.scene.changeSpeed, [100], self.b_cont)
        self.reverse_b = add_button('-1', 0, j+2, self.world.scene.reverseSpeed,
        [], self.b_cont)
        self.pause_b = add_button('Pause', 1, j+2, self.world.scene.toggleSpeed,
        [], self.b_cont)
        add_button('Now', 2, j+2, self.world.scene.time_is_now, [], self.b_cont)

        #date time display
        j += 4
        self.datelabel = add_label('UTC Time', 1, j, self.b_cont)
        #a monospae font for counter
        self.datelabel['text_font'] = self.mono_font
        #may change optimization 
        self.datelabel['textMayChange'] = True
        self.timelabel = add_label('UTC Time', 1, j+1, self.b_cont)
        self.timelabel['text_font'] = self.mono_font
        self.timelabel['textMayChange'] = True
        
        # time jumps in seconds
        j += 3
        add_label('Jump forward : ', 1, j, self.b_cont)
        add_button('day', 0, j+1, self.world.scene.time_jump, [1], self.b_cont)
        add_button('month', 1, j+1, self.world.scene.time_jump, [30], self.b_cont)
        add_button('season', 2, j+1, self.world.scene.time_jump, [91], self.b_cont)
        add_button('year', 0, j+2, self.world.scene.time_jump, [365], self.b_cont)
        
        #factual changes
        j += 4
        add_label('Factual changes : ', 1, j, self.b_cont)
        self.fact_moon_b = add_button('Moon', 0, j+1, self.world.scene.sys.toggleIncl,
        [], self.b_cont)
        self.fact_moon2_b = add_button('Moon+', 1, j+1, self.world.scene.sys.toggleIncl,
        [True], self.b_cont)
        self.fact_earth_b = add_button('Earth', 2, j+1, self.world.scene.sys.toggleTilt,
        [], self.b_cont)
        self.fact_scale_b = add_button('Scale', 0, j+2, self.world.scene.toggleScale,
        [], self.b_cont)
        
        #Visualization changes
        j += 4
        add_label('Display : ', 1, j, self.b_cont)
        self.shadow_b = add_button('Shadow', 0, j+1, self.world.scene.toggleShadows,
        [], self.b_cont)
        self.mark_b = add_button('Mark', 1, j+1, self.world.scene.toggleMarks,
        [], self.b_cont)
        self.star_b = add_button('Stars', 2, j+1, self.world.scene.toggleSky,
        [], self.b_cont)
        
        #hidden dialogs
        j += 3
        add_button('About', 2, j, self.show_dialog, [self.about_dialog], self.b_cont)
        

    def show_dialog(self, frame) :
        '''show a given frame'''
        frame.reparentTo(pixel2d)
    
    def hide_dialog(self, frame) :
        frame.detachNode()
        
    def update_buttons(self) :
        """set buttons states and appearances according to user input
        buttons should reflect what you're looking at and what you're following"""
        if self.world.Camera.hm.following == self.world.earth :
            #show activated button for followed object
            self.earth_b['geom'] = self.b_map_acti
            self.moon_b['geom'] = self.b_map
            self.sun_b['geom'] = self.b_map
            self.ext_b['geom'] = self.b_map
        elif self.world.Camera.hm.following == self.world.moon :
            self.earth_b['geom'] = self.b_map
            self.moon_b['geom'] = self.b_map_acti
            self.sun_b['geom'] = self.b_map
            self.ext_b['geom'] = self.b_map
        elif self.world.Camera.hm.following == self.world.sun :
            self.earth_b['geom'] = self.b_map
            self.moon_b['geom'] = self.b_map
            self.sun_b['geom'] = self.b_map_acti
            self.ext_b['geom'] = self.b_map
        elif self.world.Camera.hm.following == self.world.home :
            self.earth_b['geom'] = self.b_map
            self.moon_b['geom'] = self.b_map
            self.sun_b['geom'] = self.b_map
            self.ext_b['geom'] = self.b_map_acti
        elif self.world.Camera.hm.following == None :
            self.earth_b['geom'] = self.b_map
            self.moon_b['geom'] = self.b_map
            self.sun_b['geom'] = self.b_map
            self.ext_b['geom'] = self.b_map
        
        
        if self.world.Camera.hm.looking == self.world.earth :
            #show activated button for looked object
            self.earth_lb['geom'] = self.b_map_acti
            self.moon_lb['geom'] = self.b_map
            self.sun_lb['geom'] = self.b_map
        elif self.world.Camera.hm.looking == self.world.moon :
            self.earth_lb['geom'] = self.b_map
            self.moon_lb['geom'] = self.b_map_acti
            self.sun_lb['geom'] = self.b_map
        elif self.world.Camera.hm.looking == self.world.sun :
            self.earth_lb['geom'] = self.b_map
            self.moon_lb['geom'] = self.b_map
            self.sun_lb['geom'] = self.b_map_acti
        elif self.world.Camera.hm.looking == None :
            self.earth_lb['geom'] = self.b_map
            self.moon_lb['geom'] = self.b_map
            self.sun_lb['geom'] = self.b_map
            
        if self.world.scene.reverse :
            self.reverse_b['geom'] = self.b_map_acti
        else :
            self.reverse_b['geom'] = self.b_map
            
        if self.world.scene.paused :
            self.pause_b['geom'] = self.b_map_acti
        else :
            self.pause_b['geom'] = self.b_map

        if self.world.scene.realist_scale :
            self.fact_scale_b['geom'] = self.b_map_acti
        else :
            self.fact_scale_b['geom'] = self.b_map
            
        if self.world.scene.show_shadows :
            self.shadow_b['geom'] = self.b_map_acti
        else :
            self.shadow_b['geom'] = self.b_map

        if self.world.scene.show_stars :
            self.star_b['geom'] = self.b_map_acti
        else :
            self.star_b['geom'] = self.b_map

        if self.world.scene.show_marks :
            self.mark_b['geom'] = self.b_map_acti
        else :
            self.mark_b['geom'] = self.b_map
        
        #which level of inclination
        if self.world.scene.sys.inclined :
            self.fact_moon_b['geom'] = self.b_map_acti
        elif self.world.scene.sys.inclinedHard :
            self.fact_moon2_b['geom'] = self.b_map_acti
        else :
            self.fact_moon_b['geom'] = self.b_map
            self.fact_moon2_b['geom'] = self.b_map
        
        if self.world.scene.sys.tilted :
            self.fact_earth_b['geom'] = self.b_map_acti
        else :
            self.fact_earth_b['geom'] = self.b_map
        

    def interfaceTask(self, task) :
        #update simulation speed indicator 
        #(in scientific notation with limited significant digits)
        self.speedlabel['text'] = '%.1e' % self.world.scene.simul_speed, 2
        #update clock display
        new_time = self.world.scene.simul_time.isoformat().split("T")
        self.datelabel['text'] = new_time[0]
        self.timelabel['text'] = new_time[1].split(".")[0]
        #follow window resize
        w, h = base.win.getXSize(), base.win.getYSize()
        bw, bh = BUTTONSIZE
        self.about_dialog.setPos((w/2, -1, -h/2))
        #show task timing for debug
        if PRINTTIMING :
            print taskMgr
        return Task.again
    
    def buttonsTask(self, task) :
        #buttons should reflect what camera is following or looking at
        self.update_buttons()
        #show task timing for debug
        return Task.cont
