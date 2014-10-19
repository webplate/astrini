#!/usr/bin/env python
# -*- coding: utf-8-*- 
#

#Tune panda packing

import sys
# add the working directory to the path so local files and modules can be found
sys.path.insert(0,'')

class Astrini(p3d):
    require('panda3d', 'numpy') # include some other packages

    config(display_name="Astrini") 

    #module('core.*') # include the python package core, and its submodules
    module('astronomia')
    dir('fonts',newDir='fonts') # include font files
    dir('models',newDir='models')
    dir('images',newDir='images')
    mainModule('main') # include and set the main module that runs when the p3d is run
    file('license.txt') # include text files
    file('README')
