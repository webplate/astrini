#!/usr/bin/env python
# -*- coding: utf-8-*- 
#pyinstaller specification file for windows one exe packing
#use it like :
#   python c:\pyinstaller\PyInstaller.py main.spec
#and put upx in path for compression

PYINSTALLER_DIR = 'C:\\pyinstaller'
#****************************************PANDA3D******************************************************
PANDA_DIR = 'C:\\Panda3D-1.8.1'
import sys, os, glob
# some C/C++ runtime libraries, machine without these .dlls will crash Panda3D
runtimeLibraries=glob.glob(os.path.join(PANDA_DIR, 'bin/*.manifest'))+\
                 glob.glob(os.path.join(PANDA_DIR, 'bin/vcredist*.exe'))
P3DruntimeLibraries=[]
for r in runtimeLibraries:
   P3DruntimeLibraries.append( (r[r.rfind('\\')+1:],r,'DATA') )

P3DmissingDLLs = []
for d in os.listdir(os.path.join(PANDA_DIR, 'bin/')):
   if d[-4:] != '.dll': continue
   P3DmissingDLLs.append( (d,os.path.join(PANDA_DIR,'bin/%s' %d),'BINARY') )

#*******************************************************************************************************


a = Analysis(['main.py'],
             pathex=[PYINSTALLER_DIR])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          Tree(os.path.join(PANDA_DIR, 'etc'), prefix='etc'),
          Tree(os.path.join('models'), prefix='models'),
          Tree(os.path.join('fonts'), prefix='fonts'),
          Tree(os.path.join('images'), prefix='images'),
          a.scripts,
          a.binaries+P3DmissingDLLs,
          name='main.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True,
          icon='icon.ico' )
