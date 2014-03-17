#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import subprocess

imdir = 'images/'
modir = 'models/'

def packImages() :
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
    print subprocess.call('packp3d -o astrini.p3d -d ./', shell=True)
    print subprocess.call('pdeploy -s -n astrini -N "Astrini" -v 0.0.0 -a glen_lomax -A "Glen Lomax" -e glenlomax@gmail.com -l "GNU Public License" -L gpl.txt -i images/icon.png -P linux_amd64 -P win32 -P osx_i386 astrini.p3d standalone', shell=True)

def main():
    deploy()
    


if __name__ == '__main__':
    main()


