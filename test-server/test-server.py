from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/test', methods=['POST', 'GET'])
def test():
    data = request.json
    print(data)
    if data is None:
        return jsonify({"message":"text not found"})
    else:
        return jsonify(data)


# Run in HTTP
if __name__=="__main__":
    app.run(host='127.0.0.1', port='5000', debug=True)