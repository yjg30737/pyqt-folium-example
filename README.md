# pyqt-folium-example
Showing folium(based on leaflet.js) map with PyQt desktop app

## Requirements
* folium
* QtWebEngineView
* jinja2

## How to Use
1. git clone ~
2. python -m pip install PyQt5-stubs - if this is not installed, QtWebEngineWidgets might not work
3. python -m pip install PyQtWebEngine
4. python -m pip install folium
5. python main.py

## Preview

![image](https://user-images.githubusercontent.com/55078043/218347247-bd0ce881-e07d-46f7-8469-95eb702103b2.png)

This is very basic one. Zoom in and out and you can see the country's name and region or anything like that

You can switch between each tile by clicking on each radio button.

Each time you click one of them, the Folium HTML file is saved and the QWebEngineView is reloaded.

## Note

main.html will be generated for showing the folium map. main.html contains folium related scripts.

You can just remove it if you want. If you run main.py script it will be generated again anyways

## TODO
* Connect one's route to the other
* Get the location's name with tooltip

## See Also
* <a href="https://github.com/yjg30737/pyqt-googlemap-example">PyQt Google Map Example</a>
* <a href="https://github.com/yjg30737/pyqt-plotly-example.git">PyQt Plotly Example</a>
