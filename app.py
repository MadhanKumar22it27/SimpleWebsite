from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
import threading

app = Flask(__name__) 
socketio = SocketIO(app)

countdown_duration = 0 
end_time = None 
timer_thread = None

@app.route('/') 
def index():
    return render_template('index.html')
    
@app.route('/driver')
def driver():
    return render_template('driver.html')

@app.route('/student')
def student():
    return render_template('student.html')

def countdown():
    global countdown_duration, end_time
    while True:
        if end_time:
            remaining_time = max(0, end_time - time.time())
            socketio.emit('update', {'remaining_time': remaining_time})
            if remaining_time <= 0:
                end_time = None
                socketio.emit('beep')
        time.sleep(1)

@socketio.on('start')
def handle_start(data):
    global countdown_duration, end_time
    countdown_duration = data['duration']
    end_time = time.time() + countdown_duration
    emit('update', {'remaining_time': countdown_duration}, broadcast=True)

if __name__ == '__main__':
    timer_thread = threading.Thread(target=countdown)
    timer_thread.daemon = True
    timer_thread.start()
    socketio.run(app, debug=True)
