import os

import MySQLdb.cursors

from decorators import dbc
from flask import Flask, request
from google.oauth2 import id_token
from google.auth.transport import requests


app = Flask(__name__)


@app.route('/')
def index():
    return 'Speeling bee'


@app.route('/loginGoogle', methods=['POST'])
@dbc
def login_google(db_conn: MySQLdb.cursors.Cursor):
    token = request.get_json()['credential']
    id_info = id_token.verify_oauth2_token(token, requests.Request(), os.getenv('GOOGLE_CLIENT_ID'))
    db_conn.execute('select * from users.users where email=%s', (id_info['email'],))
    user_info = db_conn.fetchone()
    id_info['preferredColor'] = user_info[2]
    return id_info


if __name__ == "__main__":
    app.run(port=5000, debug=True)
