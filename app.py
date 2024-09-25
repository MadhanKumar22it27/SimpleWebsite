from flask import Flask, render_template, request , jsonify, render_template_string
from flask_socketio import SocketIO, emit
import time
import threading
import folium
from opencage.geocoder import OpenCageGeocode
import math


app = Flask(__name__)
socketio = SocketIO(app)

opencage_api_key = 'd0912921b03b43ef94bf5cccb2194195'

geocoder = OpenCageGeocode(opencage_api_key)
# Static locations for Device 1 and Device 2
device_coordinates = {
    'device1': (11.0835, 76.9966),  # Static location for Device 1 KGISL
    'device2': (11.4771273, 77.147258)  # Static location for Device 2 PriyaBharathi House
}

driver_location = None  # Global variable to store the driver's location

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in km
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance
# Global timer state
timer_state = {
    'remaining_time': 300,  # Default to 5 minutes in seconds
    'is_running': False
}

# To stop the timer thread
stop_timer_thread = False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/driver')
def driver():
    return render_template('driver.html')

from flask import Flask, render_template, request, jsonify
import folium
from geopy.distance import geodesic


# KGISL Institute of Technology coordinates
kgisl_lat, kgisl_lng = 11.084320842094604, 76.9971686531164

# Store student locations
student_locations = []

# student count for the geo fencing 


@app.route('/geo_fencing')
def geo_fencing():
    students_count = 0
    # Create a Folium map centered around KGISL Institute of Technology
    mymap = folium.Map(location=[kgisl_lat, kgisl_lng], zoom_start=45)

    # Add a circle representing the 1km geofence
    folium.Circle(
        radius=20,
        location=[kgisl_lat, kgisl_lng],
        color='blue',
        fill=True,
        fill_opacity=0.2
    ).add_to(mymap)


    # Add student markers to the map
    for student in student_locations:
        # color = 'green' if is_within_geofence(student['lat'], student['lng'], kgisl_lat, kgisl_lng) else 'red' , students_count = students_count + 1
        if is_within_geofence(student['lat'], student['lng'], kgisl_lat, kgisl_lng):
            color = 'green'
        else:
            color = 'red'
            students_count = students_count + 1
        folium.Marker(
            location=[student['lat'], student['lng']],
            icon=folium.Icon(color=color)
        ).add_to(mymap)

    # Save the map to an HTML string and pass it to the template
    map_html = mymap._repr_html_()
    return render_template('map.html', map_html=map_html, students_count = students_count)

@app.route('/studenticon')
def studenticon():
    return render_template('student_icon.html')
    

@app.route('/add_student_location', methods=['POST'])
def add_student_location():
    data = request.get_json()
    lat = data['lat']
    lng = data['lng']
    student_locations.append({'lat': lat, 'lng': lng})
    return jsonify({'status': 'success'})

@app.route('/count_students', methods=['GET'])
def count_students():
    count = sum(1 for student in student_locations if is_within_geofence(student['lat'], student['lng'], kgisl_lat, kgisl_lng))
    return jsonify({'count': count})

def is_within_geofence(device_lat, device_lng, kgisl_lat, kgisl_lng, radius=20):
    distance = geodesic((kgisl_lat, kgisl_lng), (device_lat, device_lng)).meters
    return distance <= radius


@app.route('/view_map')
def view_map(): 
    return render_template('view_map.html')
@app.route('/start_tracking')
def start_tracking():
    return  render_template_string('''
    <!DOCTYPE html>
    <html> 
    <head>
        <title>Device Tracking</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.js"></script>
    </head>
    <body>
        <h1>Device Tracking</h1>
        <!-- <button onclick="startTracking()">Start Tracking</button> -->
         <button onclick="viewMap()">View Map</button>
                                  
        <div id="map" style="height: 600px;"></div>
        <p id="distance"></p>
        <script>
window.onload = function() {
     startTracking();
};
            let driverMarker;
            let tracking = false;
            let map;

function startTracking() {
    tracking = true;
    getLocation();
}

function getLocation() {
    if (navigator.geolocation && tracking) {
        navigator.geolocation.getCurrentPosition((position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            fetch(`/driver_location?lat=${lat}&lon=${lon}`)
                .then(response => response.json())
                .then(data => {
                    updateDriverMarker(lat, lon);
                });

            setTimeout(getLocation, 20000);  // Fetch location every 20 seconds
        });
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

function updateDriverMarker(lat, lon) {
    if (!map) {
        map = L.map('map').setView([lat, lon], 50);  // Initialize the map if not already initialized
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
    }

    if (!driverMarker) {
        driverMarker = L.marker([lat, lon]).addTo(map).bindPopup("Driver's Current Location").openPopup();
    } else {
        driverMarker.setLatLng([lat, lon]);  // Update the marker's position
    }
}

function viewMap() {
    fetch('/coordinates')
        .then(response => response.json())
        .then(data => {
            updateCombinedMap(data);
        });
}

function updateCombinedMap(data) {
    if (!map) {
        map = L.map('map').setView([11.0835, 76.9966], 30);  // Initialize map centered on Device 1 if not already initialized
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
    }

    const latLngs = [
        L.latLng(data['device1'][0], data['device1'][1]),
        L.latLng(data['device2'][0], data['device2'][1])
    ];

    if (data['driver']) {
        latLngs.push(L.latLng(data['driver'][0], data['driver'][1]));
    }

    L.Routing.control({
        waypoints: latLngs,
        createMarker: function(i, waypoint, n) {
            let markerText = (i < 2) ? `Device ${i + 1}` : `Driver`;
            return L.marker(waypoint.latLng).bindPopup(markerText);
        },
        lineOptions: {
            styles: [{ color: 'blue', weight: 6 }]
        }
    }).addTo(map);

    map.fitBounds(L.latLngBounds(latLngs));
}

        </script>
    </body>
    </html>
    ''')

@app.route('/driver_location')
def driver_location():
    global driver_location
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    driver_location = (lat, lon)
    return jsonify({'driver': driver_location})

@app.route('/coordinates')
def coordinates():
    data = {
        'device1': device_coordinates['device1'],
        'device2': device_coordinates['device2']
    }
    if driver_location:
        data['driver'] = driver_location
    return jsonify(data)


@app.route('/student')
def student():
    return render_template('student.html')

@socketio.on('start_timer')
def handle_start_timer():
    global timer_state, stop_timer_thread
    if not timer_state['is_running']:
        timer_state['is_running'] = True
        stop_timer_thread = False
        thread = threading.Thread(target=countdown)
        thread.start()
    emit('timer_update', timer_state, broadcast=True)

@socketio.on('stop_timer')
def handle_stop_timer():
    global timer_state, stop_timer_thread
    timer_state['is_running'] = False
    stop_timer_thread = True
    emit('timer_update', timer_state, broadcast=True)

@socketio.on('reset_timer')
def handle_reset_timer():
    global timer_state, stop_timer_thread
    timer_state['remaining_time'] = 300  # Reset to 5 minutes
    timer_state['is_running'] = False
    stop_timer_thread = True
    emit('timer_update', timer_state, broadcast=True)

@socketio.on('set_time')
def handle_set_time(data):
    global timer_state, stop_timer_thread
    timer_state['remaining_time'] = data['new_time']
    timer_state['is_running'] = False
    stop_timer_thread = True
    emit('timer_update', timer_state, broadcast=True)

def countdown():
    global timer_state, stop_timer_thread
    while timer_state['is_running'] and timer_state['remaining_time'] > 0 and not stop_timer_thread:
        time.sleep(1)
        timer_state['remaining_time'] -= 1
        if timer_state['remaining_time'] <= 30:
            socketio.emit('beep')
        if timer_state['remaining_time'] == 0:
            timer_state['is_running'] = False
            socketio.emit('beep')
        socketio.emit('timer_update', timer_state)
 
if __name__ == '__main__':
    socketio.run(app, debug=True)
