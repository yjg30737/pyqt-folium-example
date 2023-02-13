import os, posixpath
import webbrowser

import sqlite3
import folium
from folium import Marker
from folium.plugins import MousePosition
from jinja2 import Template

from PyQt5.QtCore import QUrl, Qt, QTimer, QRect, QPoint, QEvent
from PyQt5.QtGui import QPalette, QCursor, QRegion, QPainter
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QRadioButton, QWidget, QHBoxLayout, QVBoxLayout, QMenu, \
    QSizePolicy, QStyle, QStyleOption, QStyleHintReturnMask, QLabel


# https://stackoverflow.com/questions/59902049/pyqt5-tooltip-with-clickable-hyperlink
# musicamante's answer
class ClickableTooltip(QLabel):
    __instance = None
    refWidget = None
    refPos = None
    menuShowing = False

    def __init__(self):
        super().__init__(flags=Qt.ToolTip)
        margin = self.style().pixelMetric(
            QStyle.PM_ToolTipLabelFrameWidth, None, self)
        # YJG - add margin
        self.setMargin(margin + 10)
        self.setForegroundRole(QPalette.ToolTipText)
        self.setWordWrap(True)

        self.mouseTimer = QTimer(interval=250, timeout=self.checkCursor)
        self.hideTimer = QTimer(singleShot=True, timeout=self.hide)

    def checkCursor(self):
        # ignore if the link context menu is visible
        for menu in self.findChildren(
            QMenu, options=Qt.FindDirectChildrenOnly):
                if menu.isVisible():
                    return

        # an arbitrary check for mouse position; since we have to be able to move
        # inside the tooltip margins (standard QToolTip hides itself on hover),
        # let's add some margins just for safety
        region = QRegion(self.geometry().adjusted(-10, -10, 10, 10))
        if self.refWidget:
            rect = self.refWidget.rect()
            rect.moveTopLeft(self.refWidget.mapToGlobal(QPoint()))
            region |= QRegion(rect)
        else:
            # add a circular region for the mouse cursor possible range
            rect = QRect(0, 0, 16, 16)
            rect.moveCenter(self.refPos)
            region |= QRegion(rect, QRegion.Ellipse)
        if QCursor.pos() not in region:
            self.hide()

    def show(self):
        super().show()
        QApplication.instance().installEventFilter(self)

    def event(self, event):
        # just for safety...
        if event.type() == QEvent.WindowDeactivate:
            self.hide()
        return super().event(event)

    def eventFilter(self, source, event):
        # if we detect a mouse button or key press that's not originated from the
        # label, assume that the tooltip should be closed; note that widgets that
        # have been just mapped ("shown") might return events for their QWindow
        # instead of the actual QWidget
        if source not in (self, self.windowHandle()) and event.type() in (
            QEvent.MouseButtonPress, QEvent.KeyPress):
                self.hide()
        return super().eventFilter(source, event)

    def move(self, pos):
        # ensure that the style has "polished" the widget (font, palette, etc.)
        self.ensurePolished()
        # ensure that the tooltip is shown within the available screen area
        geo = QRect(pos, self.sizeHint())
        try:
            screen = QApplication.screenAt(pos)
        except:
            # support for Qt < 5.10
            for screen in QApplication.screens():
                if pos in screen.geometry():
                    break
            else:
                screen = None
        if not screen:
            screen = QApplication.primaryScreen()
        screenGeo = screen.availableGeometry()
        # screen geometry correction should always consider the top-left corners
        # *last* so that at least their beginning text is always visible (that's
        # why I used pairs of "if" instead of "if/else"); also note that this
        # doesn't take into account right-to-left languages, but that can be
        # accounted for by checking QGuiApplication.layoutDirection()
        if geo.bottom() > screenGeo.bottom():
            geo.moveBottom(screenGeo.bottom())
        if geo.top() < screenGeo.top():
            geo.moveTop(screenGeo.top())
        if geo.right() > screenGeo.right():
            geo.moveRight(screenGeo.right())
        if geo.left() < screenGeo.left():
            geo.moveLeft(screenGeo.left())
        super().move(geo.topLeft())

    def contextMenuEvent(self, event):
        # check the children QMenu objects before showing the menu (which could
        # potentially hide the label)
        knownChildMenus = set(self.findChildren(
            QMenu, options=Qt.FindDirectChildrenOnly))
        self.menuShowing = True
        super().contextMenuEvent(event)
        newMenus = set(self.findChildren(
            QMenu, options=Qt.FindDirectChildrenOnly))
        if knownChildMenus == newMenus:
            # no new context menu? hide!
            self.hide()
        else:
            # hide ourselves as soon as the (new) menus close
            for m in knownChildMenus ^ newMenus:
                m.aboutToHide.connect(self.hide)
                m.aboutToHide.connect(lambda m=m: m.aboutToHide.disconnect())
            self.menuShowing = False

    def mouseReleaseEvent(self, event):
        # click events on link are delivered on button release!
        super().mouseReleaseEvent(event)
        self.hide()

    def hide(self):
        if not self.menuShowing:
            super().hide()

    def hideEvent(self, event):
        super().hideEvent(event)
        QApplication.instance().removeEventFilter(self)
        self.refWidget.window().removeEventFilter(self)
        self.refWidget = self.refPos = None
        self.mouseTimer.stop()
        self.hideTimer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # on some systems the tooltip is not a rectangle, let's "mask" the label
        # according to the system defaults
        opt = QStyleOption()
        opt.initFrom(self)
        mask = QStyleHintReturnMask()
        if self.style().styleHint(
            QStyle.SH_ToolTip_Mask, opt, self, mask):
                self.setMask(mask.region)

    def paintEvent(self, event):
        # we cannot directly draw the label, since a tooltip could have an inner
        # border, so let's draw the "background" before that
        qp = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        style = self.style()
        style.drawPrimitive(style.PE_PanelTipLabel, opt, qp, self)
        # now we paint the label contents
        super().paintEvent(event)

    @staticmethod
    def showText(pos, text:str, parent=None, rect=None, delay=0):
        # this is a method similar to QToolTip.showText;
        # it reuses an existent instance, but also returns the tooltip so that
        # its linkActivated signal can be connected
        if ClickableTooltip.__instance is None:
            if not text:
                return
            ClickableTooltip.__instance = ClickableTooltip()
        toolTip = ClickableTooltip.__instance

        toolTip.mouseTimer.stop()
        toolTip.hideTimer.stop()

        # disconnect all previously connected signals, if any
        try:
            toolTip.linkActivated.disconnect()
        except:
            pass

        if not text:
            toolTip.hide()
            return
        toolTip.setText(text)

        if parent:
            toolTip.refRect = rect
        else:
            delay = 0

        pos += QPoint(16, 16)

        # adjust the tooltip position if necessary (based on arbitrary margins)
        if not toolTip.isVisible() or parent != toolTip.refWidget or (
            not parent and toolTip.refPos and
            (toolTip.refPos - pos).manhattanLength() > 10):
                toolTip.move(pos)

        # we assume that, if no parent argument is given, the current activeWindow
        # is what we should use as a reference for mouse detection
        toolTip.refWidget = parent or QApplication.activeWindow()
        toolTip.refPos = pos
        toolTip.show()
        toolTip.mouseTimer.start()
        if delay:
            toolTip.hideTimer.start(delay)

        return toolTip

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        self.setWindowTitle('PyQt & Folium')

        self.__m = folium.Map(tiles='openstreetmap')

        self.__m.add_child(folium.ClickForMarker(
            '''
            <b>Latitude:</b> ${lat}<br /><b>Longitude:</b> ${lng} <br/>
            <s>Name of the location - later</s>
            '''
        ))

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

        e = folium.Element(click_js)
        html = self.__m.get_root()
        html.script.get_root().render()
        html.script._children[e.get_name()] = e

        # Add a marker to the map
        folium.Marker([34.052235, -118.243683], popup='Los Angeles, CA, USA').add_to(self.__m)

        self.__m.save("map.html")

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

    def eventFilter(self, source, event):
        if event.type() == QEvent.ToolTip and source.toolTip():
            toolTip = ClickableTooltip.showText(
                QCursor.pos(), source.toolTip(), source)
            toolTip.linkActivated.connect(self.toolTipLinkClicked)
            return True
        return super().eventFilter(source, event)

    def toolTipLinkClicked(self, url):
        webbrowser.open(url)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()