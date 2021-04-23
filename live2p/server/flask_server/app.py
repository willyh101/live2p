from flask import Flask, render_template, request
from live2p.server.flask_server.models import Experiment
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from live2p.workers import RealTimeQueue, Worker

app = Flask(__name__)
expt = Experiment()
workers = []


@app.route('/')
def index():
    return render_template('Live2p Server')

@app.route('/setup', methods=['POST'])
def setup():
    data = request.get_json()
    expt.update(data)
    
    for p in range(expt.nplanes):
        workers.append(RealTimeQueue(expt, p, Queue()))
    
@app.route('/acq-done', methods=['POST'])
def acq_done():
    pass

@app.route('/run-online', methods=['POST'])
def run_online():
    with ThreadPoolExecutor() as executor:
        tasks = [executor.submit(w.process_frame_from_queue) for w in workers]




if __name__ == '__main__':
    app.run()