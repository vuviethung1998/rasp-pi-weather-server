from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/test', methods=['POST', 'GET'])
def test_json():
    print(request.get_json())
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

# Run in HTTP
if __name__=="__main__":
    app.run(host='0.0.0.0', port='5000', debug=True)