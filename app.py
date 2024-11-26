from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Shadow'

# Health check route to bypass health check failures
@app.route('/health')
def health_check():
    return 'OK', 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

