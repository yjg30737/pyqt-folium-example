import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/add_marker', methods=['POST'])
def add_marker():
    try:
        # Get the marker data from the request body
        data = request.get_json()
        print('saved in server-side')

        # Save the marker data to the SQLite3 database file
        conn = sqlite3.connect('markers.db')
        c = conn.cursor()
        c.execute('INSERT INTO markers (lat, lng) VALUES (?, ?)', (data['lat'], data['lng']))
        conn.commit()
        conn.close()

        # Do something with the lat and lng values, like adding them to a database
        return jsonify({'status': 'ok'})
    except Exception as e:
        print(e)
        raise Exception


def flask_thread():
    app.run()

# for test by Chrome DevTools
# app.run()