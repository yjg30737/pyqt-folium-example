import os, posixpath
import folium

from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        self.setWindowTitle('PyQt & Folium')

        m = folium.Map()
        m.save("map.html")

        cur_dir = os.path.dirname(__file__)
        map_filename = os.path.join(cur_dir, 'map.html').replace(os.path.sep, posixpath.sep)

        view = QWebEngineView()
        view.load(QUrl.fromLocalFile(map_filename))

        self.setCentralWidget(view)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()