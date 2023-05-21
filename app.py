import datetime
import itertools
import json
import os

import MySQLdb.cursors

from decorators import dbc
from flask import Flask, request, render_template, url_for
from google.oauth2 import id_token
import requests
from google.auth.transport import requests as rq

from speeling_bee import get_all_words, get_primary_word, points

app = Flask(__name__)


@app.route('/')
def index():
    return 'Speeling bee'


@app.route('/loginGoogle', methods=['POST'])
@dbc
def login_google(db_conn: MySQLdb.cursors.Cursor):
    token = request.get_json()['credential']
    id_info = id_token.verify_oauth2_token(token, rq.Request(), os.getenv('GOOGLE_CLIENT_ID'))
    db_conn.execute('select * from users.users where email=%s', (id_info['email'],))
    user_info = db_conn.fetchone()
    id_info['preferredColor'] = user_info[2]
    return id_info


@app.route('/date/<date>/words', methods=['GET'])
@dbc
def get_words_of_day(date: str, db_conn: MySQLdb.cursors.Cursor):
    date = datetime.datetime.strptime(date, '%Y-%m-%d')

    db_conn.execute('select dailyword, specialcharacter from speelingbee.dailyword where date=%s', (date, ))
    daily_word = db_conn.fetchone()

    if not daily_word:
        daily_word, special_character = get_primary_word()

        db_conn.execute('insert into speelingbee.dailyword (date, dailyword, specialcharacter) VALUES (%s, %s, %s)',
                        (date, daily_word, special_character))
        all_words = get_all_words(daily_word, special_character)
        for word in all_words:
            db_conn.execute('insert into speelingbee.words (date, word) VALUES (%s, %s)', (date, word))

    else:
        daily_word, special_character = daily_word
        db_conn.execute('select word, foundBy from speelingbee.words where date=%s', (date, ))
        all_words = db_conn.fetchall()
    all_words = [{'word': d[0], 'foundBy': d[1]} for d in all_words]
    letters = list(set(daily_word))

    if letters[3] != special_character:
        index_ = letters.index(special_character)
        letters[index_], letters[3] = letters[3], letters[index_]

    all_words.sort(key=lambda x: x['word'])
    return {
        'primary_word': daily_word,
        'primary_character': special_character,
        'all_letters': letters,
        'all_words': all_words
    }


@app.route('/date/<date>/user/<user>/submit', methods=['POST'])
@dbc
def submit(date: str, user: str, db_conn: MySQLdb.cursors.Cursor):
    date = datetime.datetime.strptime(date, '%Y-%m-%d')
    word = request.get_json()['word']

    # reinit words
    db_conn.execute('select specialcharacter from speelingbee.dailyword where date=%s', (date,))
    row = db_conn.fetchone()
    try:
        special_character = row[0]
    except IndexError:
        requests.get(f'http://localhost:5000/date/{date.date()}/words')
        db_conn.execute('select specialcharacter from speelingbee.dailyword where date=%s', (date,))
        special_character = db_conn.fetchone()[0]

    if special_character not in word:
        return {'alreadyFound': False,
                'points': 0,
                'isPangram': False,
                'foundBy': None,
                'validWord': False,
                'hasCenterLetter': False}

    db_conn.execute('select * from speelingbee.words where date=%s and word=%s', (date, word))
    if row := db_conn.fetchone():
        already_found = row[-1] is not None
        if not already_found:
            db_conn.execute('update speelingbee.words set foundBy=%s where date=%s and word=%s', (user, date, word))
            num_points, is_pangram = points(word)
            return {'alreadyFound': already_found,
                    'points': num_points,
                    'isPangram': is_pangram,
                    'foundBy': user,
                    'validWord': True,
                    'hasCenterLetter': True}
        return {'alreadyFound': already_found,
                'points': 0,
                'isPangram': False,
                'foundBy': row[-1],
                'validWord': True,
                'hasCenterLetter': True}
    else:
        return {'alreadyFound': False,
                'points': 0,
                'isPangram': False,
                'foundBy': None,
                'validWord': False,
                'hasCenterLetter': True}


@app.route('/date/<date>/summary', methods=['GET'])
def summary(date: str):
    words = requests.get(f'http://localhost:5000/date/{date}/words')
    words = json.loads(words.content)
    return render_template('summary.html', date=date, rank='Good', all_letters=words['all_letters'],
                           all_words=words['all_words'])


@app.route('/date/<date>/todaysHints', methods=['GET'])
def todays_hints(date: str):
    words = requests.get(f'http://localhost:5000/date/{date}/words')
    words = json.loads(words.content)

    num_words = len(words['all_words'])
    num_points = sum(points(word['word'])[0] for word in words['all_words'])
    num_pangrams = len([word for word in words['all_words'] if len(set(word['word'])) == 7])
    return render_template('todays_hints.html', date=date, num_words=num_words,
                           num_points=num_points, num_pangrams=num_pangrams)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
