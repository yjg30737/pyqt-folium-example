import os, posixpath
import folium

from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QRadioButton, QWidget, QHBoxLayout, QVBoxLayout


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
        stamen_toner = QRadioButton('Stamen Toner')
        stamen_toner.clicked.connect(lambda: self.switch_tiles(stamen_toner.text()))
        openstreetmap = QRadioButton('OpenStreetMap')
        openstreetmap.clicked.connect(lambda: self.switch_tiles(openstreetmap.text()))
        openstreetmap.setChecked(True)
        stamen_terrain = QRadioButton('Stamen Terrain')
        stamen_terrain.clicked.connect(lambda: self.switch_tiles(stamen_terrain.text()))

        lay = QHBoxLayout()

        # Add the radio buttons to the layout
        lay.addWidget(stamen_toner)
        lay.addWidget(openstreetmap)
        lay.addWidget(stamen_terrain)
        lay.setContentsMargins(0, 0, 0, 0)

        navWidget = QWidget()
        navWidget.setLayout(lay)

        lay = QVBoxLayout()
        lay.addWidget(navWidget)
        lay.addWidget(self.__view)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

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