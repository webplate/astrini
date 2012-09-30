# -*- coding: utf-8-*- 
from panda3d.core import *
import math

def makeArc(angleDegrees = 360, numSteps = 32):
    ls = LineSegs()

    angleRadians = deg2Rad(angleDegrees)

    for i in range(numSteps + 1):
        a = angleRadians * i / numSteps
        y = math.sin(a)
        x = math.cos(a)

        ls.drawTo(x, 0, y)

    node = ls.create()
    return NodePath(node)

def makeLine(length):
    ls = LineSegs()
    ls.drawTo(0, 0, -length/2.)
    ls.drawTo(0, 0, length/2.)
    node = ls.create()
    return NodePath(node)

def makeCross(length):
    ls = LineSegs()
    ls.drawTo(0, 0, -length/2.)
    ls.drawTo(0, 0, length/2.)
    ls.drawTo(0, -length/2., 0)
    ls.drawTo(0, length/2., 0)
    ls.drawTo(-length/2., 0, 0)
    ls.drawTo(length/2., 0, 0)
    node = ls.create()
    return NodePath(node)
