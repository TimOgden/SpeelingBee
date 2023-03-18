import os

from flask import Flask, request
from google.oauth2 import id_token
from google.auth.transport import requests


app = Flask(__name__)


@app.route('/')
def index():
    return 'Speeling bee'


@app.route('/loginGoogle', methods=['POST'])
def login_google():
    token = request.get_json()['credentials']
    id_info = id_token.verify_oauth2_token(token, requests.Request(), os.getenv('GOOGLE_CLIENT_ID'))
    return id_info


if __name__ == "__main__":
    app.run(port=5000, debug=True)
