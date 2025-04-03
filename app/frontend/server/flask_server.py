from flask import Flask, jsonify, request, send_from_directory, Response
import os, requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, '..', 'static')


app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')

FASTAPI_BACKEND = "http://127.0.0.1:8000"

@app.route('/')
def index():
    return send_from_directory(STATIC_FOLDER, 'index.html')

@app.route('/prompt', methods=['POST'])
def prompt_proxy():
    data = request.get_json()
    try:
        backend_response = requests.post('http://127.0.0.1:8000/prompt', json=data)
        print(backend_response)
        backend_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"response": f"Flask proxy error: {str(e)}"}), 500

    return jsonify(backend_response.json())

@app.route('/create_project', methods=['POST'])
def create_project_proxy():
    data = request.get_json()
    try:
        backend_response = requests.post(f'{FASTAPI_BACKEND}/create_project', json=data)
        backend_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"response": f"Flask proxy error: {str(e)}"}), 500

    return jsonify(backend_response.json())

@app.route('/build_view_project', methods=['POST'])
def build_view_project_proxy():
    data = request.get_json()
    try:
        backend_response = requests.post(f'{FASTAPI_BACKEND}/build_view_project', json=data)
        backend_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"response": f"Flask proxy error: {str(e)}"}), 500

    return jsonify(backend_response.json())


@app.route('/export', methods=['GET'])
def export_proxy():
    project_name = request.args.get('project_name')
    if not project_name:
        return jsonify({"response": "Missing 'project_name' query parameter."}), 400

    try:
        backend_response = requests.get(
            f'{FASTAPI_BACKEND}/export',
            params={'project_name': project_name},
            stream=True
        )
        backend_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"response": f"Flask proxy error: {str(e)}"}), 500

    # Stream the file download back to the client
    response = app.response_class(
        backend_response.raw,
        content_type=backend_response.headers.get('Content-Type'),
        direct_passthrough=True
    )
    response.headers["Content-Disposition"] = backend_response.headers.get("Content-Disposition")
    return response

    
@app.route('/<path:path>', methods=['GET'])
def static_proxy(path):
    return send_from_directory(STATIC_FOLDER, path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5173, debug=True)