import os, posixpath
import random
import webbrowser
import requests

import sqlite3
import folium
from folium import Marker
from folium.plugins import MousePosition
from jinja2 import Template

from PyQt5.QtCore import QUrl, Qt, QTimer, QRect, QPoint, QEvent
from PyQt5.QtGui import QPalette, QCursor, QRegion, QPainter
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QRadioButton, QWidget, QHBoxLayout, QVBoxLayout, QMenu, \
    QSizePolicy, QStyle, QStyleOption, QStyleHintReturnMask, QLabel, QPushButton, QFrame, QLineEdit, QTableWidget, \
    QGroupBox

from clickableTooltip import ClickableTooltip


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        self.setWindowTitle('PyQt & Folium')

        self.__m = folium.Map(tiles='openstreetmap')
        # '''
        # var url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`;
        #                         let locationName;
        #                         await fetch(url)
        #                         .then(response => response.json())
        #                         .then(data => {
        #                           // Get the location name from the API response
        #                           locationName = data.display_name;
        #                           console.log(locationName); // Do something with the location name
        #                         })
        #                         .catch(error => console.error(error));
        # '''
        click_template = """
                {% macro script(this, kwargs) %}
                    async function newMarker(e){
                        var new_mark = L.marker().setLatLng(e.latlng).addTo({{this._parent.get_name()}});
                        new_mark.dragging.enable();
                        new_mark.on('dblclick', function(e){ {{this._parent.get_name()}}.removeLayer(e.target)})
                        var lat = e.latlng.lat.toFixed(4),
                           lng = e.latlng.lng.toFixed(4);
                        new_mark.bindPopup({{ this.popup }});
                        };
                    {{this._parent.get_name()}}.on('click', newMarker);
                {% endmacro %}"""

        marker = folium.ClickForMarker(
            '''
            <b>Latitude:</b> ${lat}<br /><b>Longitude:</b> ${lng} <br/>
            <s>Name of the location - Coming soon (hopefully)</s>
            '''
        )

        marker._name = 'CustomElement'

        marker._template = Template(click_template)

        self.__m.add_child(marker)

        lat_formatter = "function(num) {return `<b>Latitude</b>: ${L.Util.formatNum(num, 3)}º`;};"
        lng_formatter = "function(num) {return `<b>Longitude</b>: ${L.Util.formatNum(num, 3)}º`;};"

        MousePosition(
            position="topright",
            separator="<br />",
            empty_string="",
            lng_first=False,
            num_digits=20,
            # show the browser when clicked the coordinate
            prefix="Coordinate received by <a href=\"https://github.com/python-visualization/folium/blob/main/examples/plugin-MousePosition.ipynb\">MousePosition plugin</a>: <br />",
            lat_formatter=lat_formatter,
            lng_formatter=lng_formatter,
        ).add_to(self.__m)

        # Modify Marker template to include the onClick event
        click_template = """
        {% macro script(this, kwargs) %}
            let {{ this.get_name() }} = L.marker(
                {{ this.location|tojson }},
                {{ this.options|tojson }}
            ).addTo({{ this._parent.get_name() }}).on('click', onClick);
        {% endmacro %}"""

        # Change template to custom template
        Marker._template = Template(click_template)

        # Create the onClick listener function as a branca element and add to the map html
        click_js = """
        function onClick(e) {
            let point = e.latlng;
        }
        """

        # e = folium.Element(click_js)
        # html = self.__m.get_root()
        # html.script.get_root().render()
        # html.script._children[e.get_name()] = e

        e = folium.Element(click_js)
        html = self.__m.get_root()
        html.script.get_root().render()
        html.script._children[e.get_name()] = e

        # Add a marker to the map
        folium.Marker([34.052235, -118.243683], popup='Los Angeles, CA, USA').add_to(self.__m)

        self.__m.save('map.html')

        # Connect to the database (creates the database if it doesn't exist)
        conn = sqlite3.connect('markers.db')
        cursor = conn.cursor()

        # Create the table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS markers (
            id INTEGER PRIMARY KEY,
            lat REAL NOT NULL,
            lng REAL NOT NULL
        );
        ''')

        # Add the marker's latitude and longitude to the database
        lat = 34.052235
        lng = -118.243683
        cursor.execute('''
        INSERT INTO markers (lat, lng)
        VALUES (?, ?);
        ''', (lat, lng))

        cursor.execute('SELECT * FROM markers')
        print(cursor.fetchall())

        # Commit the changes to the database
        conn.commit()

        # Close the connection
        conn.close()

        cur_dir = os.path.dirname(__file__)
        map_filename = os.path.join(cur_dir, 'map.html').replace(os.path.sep, posixpath.sep)

        self.__view = QWebEngineView()
        self.__view.selectionChanged.connect(self.__selectionChanged)
        self.__view.load(QUrl.fromLocalFile(map_filename))


        # Create the radio buttons for each tile provider
        # tooltip description from https://deparkes.co.uk/2016/06/10/folium-map-tiles/
        stamen_toner = QRadioButton('Stamen Toner')
        stamen_toner.clicked.connect(lambda: self.switch_tiles(stamen_toner.text()))
        stamen_toner.setToolTip('The <a href="http://maps.stamen.com/#toner/12/37.7706/-122.3782">Stamen Toner</a> map tiles produce a black and white map that both looks striking and would be more suitable for printing than some of the other Folium map tiles.')
        stamen_toner.installEventFilter(self)
        openstreetmap = QRadioButton('OpenStreetMap')
        openstreetmap.clicked.connect(lambda: self.switch_tiles(openstreetmap.text()))
        openstreetmap.setChecked(True)
        openstreetmap.setToolTip('<a href="https://www.openstreetmap.org/#map=1/19/-99">Folium</a> defaults to using openstreetmap tiles.')
        openstreetmap.installEventFilter(self)
        stamen_terrain = QRadioButton('Stamen Terrain')
        stamen_terrain.clicked.connect(lambda: self.switch_tiles(stamen_terrain.text()))
        stamen_terrain.setToolTip('''
                                    <a href="http://maps.stamen.com/#watercolor/12/37.7706/-122.3782">Stamen Terrain</a> produce some cool map tiles which typically work at all zoom levels. 
                                    These terrain tiles are only available for the USA unfortunately.
                                  ''')
        stamen_terrain.installEventFilter(self)
        stamen_terrain.setToolTipDuration(0)

        lay = QHBoxLayout()

        # Add the radio buttons to the layout
        lay.addWidget(stamen_toner)
        lay.addWidget(openstreetmap)
        lay.addWidget(stamen_terrain)

        typeWidget = QGroupBox()
        typeWidget.setTitle('Type of Map')
        typeWidget.setLayout(lay)
        typeWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        lay = QVBoxLayout()
        lay.addWidget(typeWidget)
        lay.addWidget(self.__view)

        leftWidget = QWidget()
        leftWidget.setLayout(lay)

        singleMarkerRadBtn = QRadioButton('Single')
        multiMarkerRadBtn = QRadioButton('Multiple')
        multiMarkerRadBtn.setChecked(True)

        lay = QVBoxLayout()
        lay.addWidget(singleMarkerRadBtn)
        lay.addWidget(multiMarkerRadBtn)

        markerOptionGrpBox = QGroupBox()
        markerOptionGrpBox.setTitle('Marker Option')
        markerOptionGrpBox.setLayout(lay)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)

        routeLineEdit = QLineEdit()

        addRouteBtn = QPushButton('Add')
        addRouteBtn.clicked.connect(self.__addMark)

        delRouteBtn = QPushButton('Delete')
        connectBtn = QPushButton('Polygon')

        lay = QHBoxLayout()
        lay.addWidget(addRouteBtn)
        lay.addWidget(delRouteBtn)
        lay.addWidget(connectBtn)
        lay.setContentsMargins(0, 0, 0, 0)

        routeBtnWidget = QWidget()
        routeBtnWidget.setLayout(lay)

        tableWidget = QTableWidget()

        lay = QVBoxLayout()
        lay.addWidget(markerOptionGrpBox)
        lay.addWidget(sep)
        lay.addWidget(QLabel('Name of Route'))
        lay.addWidget(routeLineEdit)
        lay.addWidget(routeBtnWidget)
        lay.addWidget(tableWidget)
        lay.setAlignment(Qt.AlignTop)
        lay.setContentsMargins(0, 0, 0, 0)

        controlWidget = QWidget()
        controlWidget.setLayout(lay)

        lay = QHBoxLayout()
        lay.addWidget(leftWidget)
        lay.addWidget(controlWidget)

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

    # TODO maintain the coordinate after switching
    # TODO script keep adding, it makes the file bigger and bigger, so how about replacing instead of adding?

    def __selectionChanged(self):
        print('__selectionChanged')

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

    def __showRoute(self):
        line = folium.PolyLine(locations=[[57, -70], [47, 73]], color='red')
        line.add_to(self.__m)
        self.__m.save("map.html")
        self.__view.reload()

    def eventFilter(self, source, event):
        if event.type() == QEvent.ToolTip and source.toolTip():
            toolTip = ClickableTooltip.showText(
                QCursor.pos(), source.toolTip(), source)
            toolTip.linkActivated.connect(self.toolTipLinkClicked)
            return True
        return super().eventFilter(source, event)

    def toolTipLinkClicked(self, url):
        webbrowser.open(url)

    def __addMark(self):
        print()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()