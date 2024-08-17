from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app)

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
