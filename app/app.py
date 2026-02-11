from flask import Flask, request, jsonify, send_file, abort
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
import time
import hashlib

# Configure logging BEFORE creating the Flask app
def setup_logging():
    # Create a custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler (optional, but recommended)
    file_handler = RotatingFileHandler(
        'app.log', 
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

# Load environment variables
load_dotenv()
host = os.getenv("servername")
oracle_user = os.getenv("DBUSER")
calypso_user = os.getenv("CALYPSOUSER")

users = [host, oracle_user, calypso_user]
if_datas = ["B737-800", "A350-900", "B777-200ER"]

# Create Flask app
app = Flask(__name__)

# Disable Flask's default logger to avoid duplicate logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

@app.before_request
def log_request():
    """Log each incoming request"""
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def log_response(response):
    """Log each outgoing response"""
    logger.info(f"Response: {request.method} {request.path} - Status {response.status_code}")
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Log all exceptions"""
    logger.error(f"Error occurred: {str(e)}", exc_info=True)
    return "Internal Server Error", 500

@app.route('/')
def helloworld():
    return '<h1>CI/CD works</h1>'

@app.route('/users')
def user_data():
    return users

@app.route('/clouds')
def clouds():
    filename = './images/clouds2.jpg' 
    return send_file(filename, mimetype='image/png')    

@app.route('/stars')
def stars():
    filename = './images/stars.jpg' 
    return send_file(filename, mimetype='image/png')

@app.route('/infinite-flight')
def if_data():
    filename = './images/InfiniteFlightDebrief.png'
    return send_file(filename, mimetype='image/png')

@app.route('/health')
def health():
    # """
    # ⚠️ BROKEN HEALTH CHECK - Returns 500 error
    # Use this to test health check failures and AWS target group unhealthy alerts
    # """
    logger.error("Health check passed!")
    return "<h1>App is Up</h1>", 200

@app.route('/stress-test')
def stress_test():
    """
    Resource-intensive endpoint for testing monitoring metrics.
    Performs CPU-intensive hash calculations.
    """
    start_time = time.time()
    logger.info("Starting stress test...")
    
    # CPU-intensive operation: Calculate millions of hashes
    result = []
    iterations = 10000000  # Adjust this number to control intensity
    
    for i in range(iterations):
        # Create hash computations to consume CPU
        data = f"stress_test_{i}".encode()
        hash_result = hashlib.sha256(data).hexdigest()
        
        # Every 100k iterations, do more work
        if i % 10000000 == 0:
            for _ in range(10000000):
                hashlib.sha512(hash_result.encode()).hexdigest()
    
    # Memory-intensive operation: Create large list
    large_list = [i ** 2 for i in range(10000000)]
    
    end_time = time.time()
    elapsed = round(end_time - start_time, 2)
    
    logger.info(f"Stress test completed in {elapsed} seconds")
    
    return jsonify({
        "status": "completed",
        "iterations": iterations,
        "elapsed_seconds": elapsed,
        "message": "Resource-intensive operation finished"
    })

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    logger.info(f"Environment loaded - Host: {host}")
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)

@app.route('/infinite-loop')
def infinite_loop():
    """
    ⚠️ WARNING: This endpoint causes an infinite loop!
    Use this to test AWS CloudWatch alarms for high CPU usage and unresponsive applications.
    The request will timeout but the loop will continue consuming CPU.
    """
    logger.warning("⚠️ INFINITE LOOP TRIGGERED - CPU will spike to 100%")
    
    counter = 0
    # Infinite loop that consumes CPU
    while True:
        counter += 1
        # Do some CPU-intensive work in the loop
        hash_result = hashlib.sha256(f"loop_{counter}".encode()).hexdigest()
        
        # Optional: Log every million iterations (can comment out to reduce I/O)
        if counter % 1000000 == 0:
            logger.warning(f"Still looping... iteration {counter}")

@app.route('/memory-bomb')
def memory_bomb():
    """
    ⚠️ WARNING: This endpoint will consume increasing amounts of memory!
    Use this to test AWS CloudWatch alarms for high memory usage.
    """
    logger.warning("⚠️ MEMORY BOMB TRIGGERED - Memory usage will spike")
    
    memory_hog = []
    counter = 0
    
    # Infinite loop that consumes memory
    while True:
        # Append large chunks of data to consume memory
        memory_hog.append([0] * 1000000)  # Add ~8MB per iteration
        counter += 1
        
        if counter % 10 == 0:
            logger.warning(f"Memory bomb iteration {counter} - approximately {counter * 8}MB consumed")

if __name__ == '__main__':
    logger.info("Flask application starting...")
    app.run(host='0.0.0.0', port=5000)
