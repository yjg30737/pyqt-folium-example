import os, posixpath
import folium

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWidgets import QApplication, QMainWindow, QRadioButton, QWidget, QHBoxLayout, QVBoxLayout, QMenu, QMenuBar, \
    QAction, QSizePolicy


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        self.setWindowTitle('PyQt & Folium')

        self.__m = folium.Map(tiles='openstreetmap')
        self.__m.save("map.html")

        cur_dir = os.path.dirname(__file__)
        map_filename = os.path.join(cur_dir, 'map.html').replace(os.path.sep, posixpath.sep)

        self.__view = QWebEngineView()
        self.__view.load(QUrl.fromLocalFile(map_filename))

        # Create the radio buttons for each tile provider
        # tooltip description from https://deparkes.co.uk/2016/06/10/folium-map-tiles/
        stamen_toner = QRadioButton('Stamen Toner')
        stamen_toner.clicked.connect(lambda: self.switch_tiles(stamen_toner.text()))
        stamen_toner.setToolTip('The <a href="http://maps.stamen.com/#toner/12/37.7706/-122.3782">Stamen Toner</a> map tiles produce a black and white map that both looks striking and would be more suitable for printing than some of the other Folium map tiles.')
        openstreetmap = QRadioButton('OpenStreetMap')
        openstreetmap.clicked.connect(lambda: self.switch_tiles(openstreetmap.text()))
        openstreetmap.setChecked(True)
        openstreetmap.setToolTip('<a href="https://www.openstreetmap.org/#map=1/19/-99">Folium</a> defaults to using openstreetmap tiles.')
        stamen_terrain = QRadioButton('Stamen Terrain')
        stamen_terrain.clicked.connect(lambda: self.switch_tiles(stamen_terrain.text()))
        stamen_terrain.setToolTip('''
                                    <a href="http://maps.stamen.com/#watercolor/12/37.7706/-122.3782">Stamen Terrain</a> produce some cool map tiles which typically work at all zoom levels. 
                                    These terrain tiles are only available for the USA unfortunately.
                                  ''')
        stamen_terrain.setToolTipDuration(0)

        lay = QHBoxLayout()

        # Add the radio buttons to the layout
        lay.addWidget(stamen_toner)
        lay.addWidget(openstreetmap)
        lay.addWidget(stamen_terrain)
        lay.setContentsMargins(0, 0, 0, 0)

        navWidget = QWidget()
        navWidget.setLayout(lay)
        navWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        lay = QVBoxLayout()
        lay.addWidget(navWidget)
        lay.addWidget(self.__view)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

        # submenu of menu bar doesn't show up after full screen - this is bug of PyQt5
        # self.__view.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        # self.__view.page().fullScreenRequested.connect(lambda request: request.accept())
        # doesn't work either

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_F11:
            self.showFullScreen()
        elif e.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
        return super().keyPressEvent(e)

    # TODO show tooltip & hyperlink to explain the detail of each tile
    # TODO maintain the coordinate after switching
    # TODO script keep adding, it makes the file bigger and bigger, so how about replacing instead of adding?
    # Create a function to switch the folium tiles when the radio buttons are clicked
    def switch_tiles(self, text):
        if text == 'Stamen Toner':
            folium.TileLayer('Stamen Toner').add_to(self.__m)
            self.__m.save('map.html')
            self.__view.reload()
        elif text == 'OpenStreetMap':
            folium.TileLayer('OpenStreetMap').add_to(self.__m)
            self.__m.save('map.html')
            self.__view.reload()
        elif text == 'Stamen Terrain':
            folium.TileLayer('Stamen Terrain').add_to(self.__m)
            self.__m.save('map.html')
            self.__view.reload()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()