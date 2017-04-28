
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import common
import sys
from O3DFile import *
from DDSFile import *
import os
import re

window = 0
sph = common.sphere(16, 16, 1)
camera = common.camera()
plane = common.plane(12, 12, 1., 1.)

files = [
    '/home/kirk/Desktop/Resource/Model/Obj_kaillunTree05.o3d',
    '/home/kirk/Desktop/Resource/Model/Obj_kaillunTree06.o3d',
    '/home/kirk/Desktop/Resource/Model/Obj_kaillunTree07.o3d',
    '/home/kirk/Desktop/Resource/Model/Obj_kaillunTree08.o3d',
    '/home/kirk/Desktop/Resource/Model/Obj_KaillunTree01.o3d',
    '/home/kirk/Desktop/Resource/Model/Obj_KaillunTree02.o3d',
    '/home/kirk/Desktop/Resource/Model/Obj_KaillunTree03.o3d',
    '/home/kirk/Desktop/Resource/Model/Obj_KaillunTree04.o3d'
]

obj = 0
o3ds = []

r = re.compile('Obj_.+\.o3d')
for f in os.listdir('/home/kirk/Desktop/Resource/Model'):
    if re.match(r, f) is None:
        continue
    p  = '/home/kirk/Desktop/Resource/Model/' + f
    o3d = O3DFile(p)
    print o3d
    o3ds.append(o3d)

def InitGL(width, height):
    glClearColor(0.1, 0.1, 0.5, 0.1)
    glClearDepth(1.0)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(width)/float(height), 0.1, 100.0)    
    camera.move(0.0, 5.0, -15)    
    
def DrawGLScene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)     
    camera.setLookat()
    plane.draw() 
    glTranslatef(-1.5, 0.0, 0.0)
    glBegin(GL_TRIANGLES)
    o3d = o3ds[ obj ]
    for ii in o3d.pIB:
        i = o3d.pIIB[ii]
        vertext = o3d.pvertexlist[ i ]
        glVertex3fv(vertext)
    glEnd()

    glTranslatef(3.0, 0.0, 0.0)
    sph.draw()                         
    glutSwapBuffers()

def mouseButton( button, mode, x, y ): 
    global obj  
    print mode 
    if button == GLUT_RIGHT_BUTTON:
        camera.mouselocation = [x, y]
    if button == GLUT_LEFT_BUTTON and mode == 0:
        obj = obj + 1
        if obj >= len(o3ds):
            obj = 0
        print o3ds[ obj ]

def ReSizeGLScene(Width, Height): 
    glViewport(0, 0, Width, Height)        
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(Width)/float(Height), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    
def main():
    global window
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(640, 400)
    glutInitWindowPosition(800, 400)
    window = glutCreateWindow("opengl")
    glutDisplayFunc(DrawGLScene)
    glutIdleFunc(DrawGLScene)
    glutReshapeFunc(ReSizeGLScene)
    glutMouseFunc( mouseButton )
    glutMotionFunc(camera.mouse)
    glutKeyboardFunc(camera.keypress)
    glutSpecialFunc(camera.keypress)
    InitGL(640, 480)
    glutMainLoop()

main()
