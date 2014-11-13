# -*- coding: utf-8-*- 
import panda3d.core
from math import ceil, log, sin, cos


#importation and conversion of textures (power of 2 problem)
cardMaker = panda3d.core.CardMaker('CardMaker')

def nextPowOf2(n):
    return 2**int(ceil(log(n, 2)))


def makeGeom(filename):
    """create geom from png and take care of power of two
    texture issues to permit pixel perfect blitting"""
    origImage = panda3d.core.PNMImage()
    origImage.read(filename)
    oldWidth = origImage.getXSize()
    oldHeight = origImage.getYSize()
    newWidth = nextPowOf2(oldWidth)
    newHeight = nextPowOf2(oldHeight)

    newImage = panda3d.core.PNMImage(newWidth, newHeight)
    if origImage.hasAlpha():
        newImage.addAlpha()
    newImage.copySubImage(origImage, 0, 0, 0, 0)
   
    tex = panda3d.core.Texture()
    tex.load(newImage)
   
    cardMaker.setFrame(0, oldWidth, 0, oldHeight)

    fU = float(oldWidth)/newWidth
    fV = float(oldHeight)/newHeight

    # cardMaker.setHasUvs(True)
    cardMaker.setUvRange(panda3d.core.Point2(0, 0),
    panda3d.core.Point2(fU, fV))

    npCard = panda3d.core.NodePath(cardMaker.generate())
    npCard.setTexture(tex)
    npCard.setTexOffset(panda3d.core.TextureStage.getDefault(), 0, 1-fV)
    if origImage.hasAlpha():
        npCard.setTransparency(panda3d.core.TransparencyAttrib.MAlpha)
   
    return npCard


def makeArc(angleDegrees = 360, numSteps = 32):
    ls = panda3d.core.LineSegs()

    angleRadians = panda3d.core.deg2Rad(angleDegrees)

    for i in range(numSteps + 1):
        a = angleRadians * i / numSteps
        y = sin(a)
        x = cos(a)

        ls.drawTo(x, 0, y)

    node = ls.create()
    return panda3d.core.NodePath(node)

def makeLine(length):
    ls = panda3d.core.LineSegs()
    ls.drawTo(0, 0, -length/2.)
    ls.drawTo(0, 0, length/2.)
    node = ls.create()
    return panda3d.core.NodePath(node)

def makeCross(length = 1):
    ls = panda3d.core.LineSegs()
    ls.drawTo(0, 0, -length/2.)
    ls.drawTo(0, 0, length/2.)
    ls.drawTo(0, 0, 0)
    ls.drawTo(0, -length/2., 0)
    ls.drawTo(0, length/2., 0)
    ls.drawTo(0, 0, 0)
    ls.drawTo(-length/2., 0, 0)
    ls.drawTo(length/2., 0, 0)
    node = ls.create()
    return panda3d.core.NodePath(node)
    
