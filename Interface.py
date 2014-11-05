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
        b_cont = DirectFrame(frameSize=(-(bw+bw/2), bw+bw/2, -h/2, h/2),
            frameColor=(1,1,1,0.3),
            pos=(bw+bw/2, -1, -h/2))
        b_cont.reparentTo(pixel2d)

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
        text = [
        '',
        '',
        'Astrini',
        '',
        'An Open source project for educational astronomy',
        'Version 0.1',
        '',
        'Design : Roberto Casati and Glen Lomax.',
        'Based on ideas from Roberto Casati,',
        'Dov\'è il Sole di notte, Milano : Raffaello Cortina 2013,',
        'partly developed during Glen Lomax CogMaster internship,',
        'École des Hautes Études en Sciences Sociales, 2011-2012.',
        '',
        'Code : Glen Lomax',
        'Engine : Panda3D (https://www.panda3d.org)',
        'Licence : GPL v3',
        'Contact : glenlomax@gmail.com',
        'The source code is available at : https://github.com/webplate/astrini']
        
        self.about_dialog = add_dialog((-5*bw, 5*bw, -10*bh, 10*bh))
        add_textarea(text, self.about_dialog)
        
        #An informational dialog
        self.info_dialog = add_dialog((-3*bw, 3*bw, -3*bh, 3*bh))
        add_textarea(['','Here some information'], self.info_dialog)
        
        #Buttons to follow
        j = 1
        add_label('Go to : ', 1, j, b_cont)
        self.earth_b = add_button('Earth', 0, j+1, self.world.follow, [self.world.earth], b_cont)
        self.moon_b = add_button('Moon', 1, j+1, self.world.follow, [self.world.moon], b_cont)
        self.sun_b = add_button('Sun', 2, j+1, self.world.follow, [self.world.sun], b_cont)
        self.ext_b = add_button('Ext', 2, j+2, self.world.follow, [self.world.home], b_cont)
        #and to look at
        j += 4
        add_label('Look at : ', 1, j, b_cont)
        self.earth_lb = add_button('Earth', 0, j+1, self.world.look, [self.world.earth], b_cont)
        self.moon_lb = add_button('Moon', 1, j+1, self.world.look, [self.world.moon], b_cont)
        self.sun_lb = add_button('Sun', 2, j+1, self.world.look, [self.world.sun], b_cont)
        #and to change speed
        j += 3
        add_label('Speed : ', 0, j, b_cont)
        self.speedlabel = add_label('Speed', 1, j, b_cont)
        add_button('-', 0, j+1, self.world.changeSpeed, [1./2], b_cont)
        add_button('+', 1, j+1, self.world.changeSpeed, [2], b_cont)
        add_button('++', 2, j+1, self.world.changeSpeed, [100], b_cont)
        self.reverse_b = add_button('-1', 0, j+2, self.world.reverseSpeed, [], b_cont)
        self.pause_b = add_button('Pause', 1, j+2, self.world.toggleSpeed, [], b_cont)
        add_button('Now', 2, j+2, self.world.time_is_now, [], b_cont)

        #date time display
        j += 4
        self.datelabel = add_label('UTC Time', 1, j, b_cont)
        self.datelabel['text_font'] = self.mono_font
        self.timelabel = add_label('UTC Time', 1, j+1, b_cont)
        self.timelabel['text_font'] = self.mono_font
        
        #factual changes
        j += 3
        add_label('Factual changes : ', 1, j, b_cont)
        self.fact_moon_b = add_button('Moon', 0, j+1, self.world.toggleIncl, [], b_cont)
        self.fact_moon2_b = add_button('Moon+', 1, j+1, self.world.toggleInclHard, [], b_cont)
        self.fact_earth_b = add_button('Earth', 2, j+1, self.world.toggleTilt, [], b_cont)
        self.fact_scale_b = add_button('Scale', 0, j+2, self.world.toggleScale, [], b_cont)
        
        #Visualization changes
        j += 4
        add_label('Display : ', 1, j, b_cont)
        self.shadow_b = add_button('Shadow', 0, j+1, self.world.toggleShadows, [], b_cont)
        self.mark_b = add_button('Mark', 1, j+1, self.world.toggleMarks, [], b_cont)
        self.star_b = add_button('Stars', 2, j+1, self.world.toggleStars, [], b_cont)
        
        #hidden dialogs
        j += 20
        add_button('Info', 0, j, self.show_dialog, [self.info_dialog], b_cont)
        add_button('About', 2, j, self.show_dialog, [self.about_dialog], b_cont)
        

    def show_dialog(self, frame) :
        '''show a given frame'''
        frame.reparentTo(pixel2d)
    
    def hide_dialog(self, frame) :
        frame.detachNode()
        
    def update_buttons(self) :
        """set buttons states and appearances according to user input
        buttons should reflect what you're looking at and what you're following"""
        if self.world.following == self.world.earth :
            #disable buttons to prevent looking at own position
            self.earth_lb['state'] = DGG.DISABLED
            self.moon_lb['state'] = DGG.NORMAL
            self.sun_lb['state'] = DGG.NORMAL
            #show activated button for followed object
            self.earth_b['geom'] = self.b_map_acti
            self.moon_b['geom'] = self.b_map
            self.sun_b['geom'] = self.b_map
            self.ext_b['geom'] = self.b_map
        elif self.world.following == self.world.moon :
            self.earth_lb['state'] = DGG.NORMAL
            self.moon_lb['state'] = DGG.DISABLED
            self.sun_lb['state'] = DGG.NORMAL
            self.earth_b['geom'] = self.b_map
            self.moon_b['geom'] = self.b_map_acti
            self.sun_b['geom'] = self.b_map
            self.ext_b['geom'] = self.b_map
        elif self.world.following == self.world.sun :
            self.earth_lb['state'] = DGG.NORMAL
            self.moon_lb['state'] = DGG.NORMAL
            self.sun_lb['state'] = DGG.DISABLED
            self.earth_b['geom'] = self.b_map
            self.moon_b['geom'] = self.b_map
            self.sun_b['geom'] = self.b_map_acti
            self.ext_b['geom'] = self.b_map
        elif self.world.following == self.world.home :
            self.earth_lb['state'] = DGG.NORMAL
            self.moon_lb['state'] = DGG.NORMAL
            self.sun_lb['state'] = DGG.NORMAL
            self.earth_b['geom'] = self.b_map
            self.moon_b['geom'] = self.b_map
            self.sun_b['geom'] = self.b_map
            self.ext_b['geom'] = self.b_map_acti
        elif self.world.following == None :
            self.earth_lb['state'] = DGG.NORMAL
            self.moon_lb['state'] = DGG.NORMAL
            self.sun_lb['state'] = DGG.NORMAL
            self.earth_b['geom'] = self.b_map
            self.moon_b['geom'] = self.b_map
            self.sun_b['geom'] = self.b_map
            self.ext_b['geom'] = self.b_map
        
        
        if self.world.looking == self.world.earth :
            #disable buttons to prevent going at looked object
            self.earth_b['state'] = DGG.DISABLED
            self.moon_b['state'] = DGG.NORMAL
            self.sun_b['state'] = DGG.NORMAL
            #show activated button for looked object
            self.earth_lb['geom'] = self.b_map_acti
            self.moon_lb['geom'] = self.b_map
            self.sun_lb['geom'] = self.b_map
        elif self.world.looking == self.world.moon :
            self.earth_b['state'] = DGG.NORMAL
            self.moon_b['state'] = DGG.DISABLED
            self.sun_b['state'] = DGG.NORMAL
            self.earth_lb['geom'] = self.b_map
            self.moon_lb['geom'] = self.b_map_acti
            self.sun_lb['geom'] = self.b_map
        elif self.world.looking == self.world.sun :
            self.earth_b['state'] = DGG.NORMAL
            self.moon_b['state'] = DGG.NORMAL
            self.sun_b['state'] = DGG.DISABLED
            self.earth_lb['geom'] = self.b_map
            self.moon_lb['geom'] = self.b_map
            self.sun_lb['geom'] = self.b_map_acti
        elif self.world.looking == None :
            self.earth_b['state'] = DGG.NORMAL
            self.moon_b['state'] = DGG.NORMAL
            self.sun_b['state'] = DGG.NORMAL
            self.earth_lb['geom'] = self.b_map
            self.moon_lb['geom'] = self.b_map
            self.sun_lb['geom'] = self.b_map

    def interfaceTask(self, task) :
        #update simulation speed indicator 
        #(in scientific notation with limited significant digits)
        self.speedlabel['text'] = '%.1e' % self.world.simulSpeed, 2
        #update clock display
        new_time = self.world.simulTime.isoformat().split("T")
        self.datelabel['text'] = new_time[0]
        self.timelabel['text'] = new_time[1].split(".")[0]
        #buttons should reflect what camera is following or looking at
        self.update_buttons()
        #show task timing for debug
        if PRINTTIMING :
            print self.taskMgr
        return Task.again
