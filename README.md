# pyqt-folium-example
Showing folium(based on leaflet.js) map with PyQt desktop app

This is not the static map viewer, this is basic client-server side web app.

## Requirements
* folium
* QtWebEngineView
* jinja2 - to use javascript in the Python source
* flask - to save the information in DB
* flask_cors - to fix the CORS error

## How to Use
1. git clone ~
2. python -m pip install PyQt5-stubs - if this is not installed, QtWebEngineWidgets might not work
3. python -m pip install PyQtWebEngine
4. python -m pip install folium
5. python main.py

## How to check the error
This script doesn't support error log on its own(it is very hard), so we need to use the browser like Chrome, Edge, Firefox.

1. Go to the root directory
2. Open the script.py file and uncomment the code below
```python
# for test by browser
# app.run()
```
3. python server.py
4. open map.html
5. Chrome, for example, you can see the log to figure it out it works well or not. It doesn't work for some reasons, you can fix the error on your own.

![image](https://user-images.githubusercontent.com/55078043/226232439-00c79606-fa9a-4805-b99f-16455e93fa38.png)

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
