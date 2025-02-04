import sys
import math
import time
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QScrollArea, QSizePolicy, QGridLayout

sys.path.append('..')
from aniplot import AniplotWidget

STANDARD_DPI = 96

class SignalGenerator(object):
        ''' This can be used for testing purposes '''
        seed = 0

        def __init__(self):
            SignalGenerator.seed += 1
            self.i = self.seed

        def get(self):
            if 1:
                s = math.sin(time.time()*(self.i+1)*30+self.i*2) * 1.
                s += math.sin(time.time()*(self.i+1)*32.3+self.i*2) * 2.
                s += math.sin(time.time()*(self.i+1)*33.3+self.i*2) * 1.
                s += math.sin(time.time()*(self.i+1)*55.3+self.i*2) * 1.
                s += math.sin(time.time()*(self.i+1)*1.1+self.i*2) * 20.
                s += math.sin(time.time()*(self.i+1)*1.3+self.i*2) * 20.
                s += math.sin(time.time()*(self.i+1)*.2124+self.i*2) * 40.
                s += math.sin(time.time()*(self.i+1)*.0824+self.i*2) * 40.
                s += math.sin(time.time()*(self.i+1)*.0324+self.i*2) * 40.
                s += 127.
            else:
                s = math.sin(time.time()*(self.i+1)*.5+self.i*2) * 133.
                s += 127.
            s = min(s, 255.)
            s = max(s, 0.)

            return s


if __name__ == '__main__':

    class MainWindow(QMainWindow):
        def __init__(self, scale=1):
            super(MainWindow, self).__init__()

            # setup GUI
            centralWidget = QWidget()
            self.setCentralWidget(centralWidget)

            self.aniplot = AniplotWidget(scale)

            self.glWidgetArea = QScrollArea()
            self.glWidgetArea.setWidget(self.aniplot)
            self.glWidgetArea.setWidgetResizable(True)
            self.glWidgetArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.glWidgetArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.glWidgetArea.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.glWidgetArea.setMinimumSize(50, 50)

            centralLayout = QGridLayout()
            centralLayout.addWidget(self.glWidgetArea, 0, 0)
            centralWidget.setLayout(centralLayout)

            self.setWindowTitle("QAniplotTest")
            self.resize(400 * scale, 300 * scale)

            # setup data source
            self.source1 = SignalGenerator()
            self.source2 = SignalGenerator()
            # interestingly, every frequency larger than screen refresh rate results in incorrect speed and jerkyness.
            self.ch1 = self.aniplot.create_channel(frequency=60, value_min=0., value_min_raw=0., value_max=5., value_max_raw=255., legend="fast data")
            self.ch2 = self.aniplot.create_channel(frequency=5, value_min=0., value_min_raw=0., value_max=3.3, value_max_raw=255., legend="slow data", color=QtGui.QColor(0, 238, 0))

            self.timer1 = QtCore.QTimer(self)
            self.timer1.timeout.connect(self.timer1_fired)
            self.timer2 = QtCore.QTimer(self)
            self.timer2.timeout.connect(self.timer2_fired)

            self.aniplot.start()
            # NB! still NEVER use timers for this in real life. timers can skip updates, and
            # the graphs will lose their sync and it could be invisible. always update the slowest
            # graph at every tenth fastest graph update or something like that.. only the fastest
            # graph can use timers.
            self.timer1.start(int(1. / self.ch1.freq * 1000.))
            self.timer2.start(int(1. / self.ch2.freq * 1000.))

        def timer1_fired(self):
            self.ch1.append(self.source1.get())

        def timer2_fired(self):
            self.ch2.append(self.source2.get())

    #QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
    #QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons
    app = QApplication(sys.argv)
    display_dpi = max(app.desktop().logicalDpiX(), app.desktop().physicalDpiX())
    scale = round(display_dpi * 1.0 / STANDARD_DPI)
    print(f"Detected display DPI {display_dpi}, using {scale} x scaling")
    mainWin = MainWindow(scale)
    mainWin.show()
    if sys.platform == "darwin":
        # this line is here because on macosx the main window always starts below the terminal that opened the app.
        # the reason for getattr is that myapp.raise() caused a syntax error.
        getattr(mainWin, "raise")()

    sys.exit(app.exec_())
