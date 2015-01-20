#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Use panda3d packing tools to generate p3d file
#according to packagedef.py
#and bundle it in auto panda installer
import subprocess

imdir = 'images/'
modir = 'models/'

def call(command) :
    print subprocess.call(command, shell=True)
    
def packImages() :
    #deprecated... now directly loading pngs...
    buttons = ['button_ready.png', 'button_click.png', 'button_rollover.png', 'button_disabled.png']
    buttons = [imdir+b for b in buttons]
    size = '102,25'
    command = ['egg-texture-cards', '-o', modir+'button_maps.egg', '-p']
    command.append(size)
    command.extend(buttons)
    print subprocess.call(command)
    #~ command = ['egg-texture-cards', '-o', modir+'button.egg', imdir+'button_click.png']
    #~ print subprocess.call(command)

def deploy() :
    #pack whole app as p3d
    call('ppackage packagedef.py')
    #create deployable executables
    #some other platforms : linux_amd64  osx_i386
    call('pdeploy -s -n astrini -N "Astrini" -v 0.0.0 -a glen_lomax \
    -A "Glen Lomax" -e glenlomax@gmail.com -l "GNU Public License" \
    -L gpl.txt -i images/icon.png -P win32 \
    Astrini.p3d standalone')

def main():
    deploy()
    


if __name__ == '__main__':
    main()


