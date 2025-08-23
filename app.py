from flask import Flask, request, jsonify
from NeteaseCloudMusic import NeteaseCloudMusicApi

app = Flask(__name__)
netease = NeteaseCloudMusicApi()

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    phone = data.get('phone')
    captcha = data.get('captcha')
    if not phone or not captcha:
        return jsonify({'error': 'phone and captcha required'}), 400
    res = netease.request('login/cellphone', {'phone': f'{phone}', 'captcha': f'{captcha}'})
    return jsonify(res)

@app.route('/status', methods=['GET'])
def status():
    res = netease.request('login/status')
    return jsonify(res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
