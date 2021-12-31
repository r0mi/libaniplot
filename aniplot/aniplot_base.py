import os
import sys
import time
import traceback
from PyQt5 import QtCore, QtGui, QtOpenGL

from OpenGL.GL import * # Otherwise gltext import fails
import gltext
import copengl as gl

from . import fps_counter
from . import graph_window
from . import graph_renderer



class AniplotBase(QtOpenGL.QGLWidget):
    ''' Aniplot baseclass - this is not used directly in real application.
        Use AniplotWidget instead.
    '''
    width = -1
    height = -1
    scale = 1

    def __init__(self, parent=None, scale=1):
        super(AniplotBase, self).__init__(parent)
        self.scale = scale

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)

        self.gltext = gltext.GLText(os.path.join(os.path.dirname(__file__), 'data', 'font_proggy_opti_small.txt').encode('utf-8'))

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()
        self.setMouseTracking(True)

        # renders graphs, grids, legend, scrollbar, border.
        self.grapher = graph_renderer.GraphRenderer(self.gltext)
        self.channels = []
        self.graph_window = None

        self._fps_counter = fps_counter.FpsCounter()
        self._mouse_last_pos = None # event.pos()
        self._mouse_dragging = False
        self._last_tick_time = time.time()
        self.width = super().size().width()
        self.height = super().size().height()

    def _start(self):
        ''' begins drawing if all channels are setup '''
        self.grapher.setup(self.channels)
        # converts input events to smooth zoom/movement of the graph.
        self.graph_window = graph_window.GraphWindow(self, font=self.gltext, graph_renderer=self.grapher, keys=None, x=0, y=0, w=10, h=10, scale=self.scale)
        self.timer.start(1./60*1000)

    def __del__(self):
        self.makeCurrent()

    def initializeGL(self):
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_FOG)
        gl.glDisable(gl.GL_DITHER)
        gl.glDisable(gl.GL_LIGHTING)
        gl.glShadeModel(gl.GL_FLAT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_LINE_SMOOTH)
        gl.glEnable(gl.GL_POINT_SMOOTH)
        gl.glDisable(gl.GL_LINE_STIPPLE)
        gl.glDisable(gl.GL_LIGHT1)
        #glFrontFace(gl.GL_CW)

        gl.glEnable(gl.GL_NORMALIZE)
        gl.glHint(gl.GL_PERSPECTIVE_CORRECTION_HINT, gl.GL_NICEST)
        gl.glDisable(gl.GL_CULL_FACE)
        #glCullFace(gl.GL_BACK)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        # wireframe view
        #glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

        self.gltext.init()

    def tick(self):
        t = time.time()
        self._fps_counter.tick(t - self._last_tick_time)
        self.updateGL()
        self._last_tick_time = t

    def gl_coordinates(self, x, y):
        return x, self.size().height() - y

    def paintGL(self):
        try:
            self.render()
        except:
            traceback.print_exc()
            sys.exit(1)

    def render(self):
        if self.graph_window:
            w = self.size().width()
            h = self.size().height()
            if w <= 0 or h <= 0:
                return

            self.grapher.tick()
            self.graph_window.tick()

            gl.glClearColor(0.2, 0.2, 0.2, 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

            gl.glViewport(0, 0, w, h)

            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            gl.glOrtho(0., w, h, 0., -100, 100)

            gl.glDisable(gl.GL_DEPTH_TEST)
            gl.glDisable(gl.GL_TEXTURE_2D)
            gl.glDisable(gl.GL_LIGHTING)

            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()
            gl.glScalef(1. * self.scale, 1. * self.scale, -1.)

            self.graph_window.x = -1
            self.graph_window.y = -1
            self.graph_window.w = w + 2
            self.graph_window.h = h + 2

            # render 2d objects
            gl.glDisable(gl.GL_DEPTH_TEST)
            gl.glDisable(gl.GL_TEXTURE_2D)
            self.graph_window.render()
            gl.glEnable(gl.GL_TEXTURE_2D)
            self.gltext.drawbr(f"fps: {self._fps_counter.fps:.0f}".encode('utf-8'), w / self.scale - 3, h / self.scale - 3, fgcolor = (.9, .9, .9, 1.), bgcolor = (0.3, 0.3, 0.3, .0))
            self.gltext.drawbm(b"usage: arrows, shift, mouse", w / self.scale / 2, h / self.scale - 3, fgcolor = (.5, .5, .5, 1.), bgcolor = (0., 0., 0., .0))
        else:
            gl.glClearColor(0., 0., 0., 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    def size(self):
        return QtCore.QSize(self.width, self.height)

    def resizeGL(self, width, height):
        self.width = width
        self.height = height

    @QtCore.pyqtSlot(QtGui.QKeyEvent)
    def keyPressEvent(self, event):
        key = event.key()
        if self.graph_window:
            # if shift is not pressed, move the graph.
            if not (event.modifiers() & QtCore.Qt.ShiftModifier):
                d = 1. / 3
                if key == QtCore.Qt.Key_Left:
                    self.graph_window.move_by_ratio(-d, 0.)
                if key == QtCore.Qt.Key_Right:
                    self.graph_window.move_by_ratio(d, 0.)
                if key == QtCore.Qt.Key_Up:
                    self.graph_window.move_by_ratio(0., -d)
                if key == QtCore.Qt.Key_Down:
                    self.graph_window.move_by_ratio(0., d)
            # shift was pressed. zoom the graph.
            else:
                d = 1. / 3
                if key == QtCore.Qt.Key_Left:
                    self.graph_window.zoom_out(d, 0.)
                if key == QtCore.Qt.Key_Right:
                    self.graph_window.zoom_in(d, 0.)
                if key == QtCore.Qt.Key_Up:
                    self.graph_window.zoom_in(0., d)
                if key == QtCore.Qt.Key_Down:
                    self.graph_window.zoom_out(0., d)

    @QtCore.pyqtSlot(QtGui.QKeyEvent)
    def keyReleaseEvent(self, event):
        pass

    @QtCore.pyqtSlot(QtGui.QMouseEvent)
    def mousePressEvent(self, event):
        if self.graph_window:
            self._mouse_last_pos = event.pos()
            if event.button() == QtCore.Qt.LeftButton:
                self._mouse_dragging = True
                self.graph_window.set_smooth_movement(False)

    @QtCore.pyqtSlot(QtGui.QMouseEvent)
    def mouseReleaseEvent(self, event):
        if self.graph_window:
            if event.button() == QtCore.Qt.LeftButton:
                self._mouse_dragging = False
                self.graph_window.set_smooth_movement(True)

    @QtCore.pyqtSlot(QtGui.QMouseEvent)
    def mouseMoveEvent(self, event):
        if self.graph_window:
            if not self._mouse_last_pos:
                self._mouse_last_pos = event.pos()
            dx = event.x() - self._mouse_last_pos.x()
            dy = event.y() - self._mouse_last_pos.y()
            if self._mouse_dragging:
                self.graph_window.move_by_pixels(dx, dy)
            self._mouse_last_pos = event.pos()
