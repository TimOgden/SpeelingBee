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

from speeling_bee import get_all_words, get_primary_word, points, update_points_gathered, get_rank

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

    db_conn.execute('select dailyword, specialcharacter, pointsgathered from speelingbee.dailyword where date=%s', (date, ))
    daily_word = db_conn.fetchone()

    if not daily_word:
        daily_word, special_character = get_primary_word()

        db_conn.execute('insert into speelingbee.dailyword (date, dailyword, specialcharacter) VALUES (%s, %s, %s)',
                        (date, daily_word, special_character))
        all_words = get_all_words(daily_word, special_character)
        for word in [d[0] for d in all_words]:
            db_conn.execute('insert into speelingbee.words (date, word) VALUES (%s, %s)', (date, word))

    else:
        daily_word, special_character, points_gathered = daily_word
        db_conn.execute('select word, foundBy from speelingbee.words where date=%s', (date, ))
        all_words = db_conn.fetchall()

    db_conn.execute('select email, profilePicture from users.users;')
    users = dict(db_conn.fetchall())
    all_words = [{'word': d[0], 'foundBy': d[1], 'profilePicture': users[d[1]] if d[1] else None} for d in all_words]

    max_points = sum((points(word['word'])[0] for word in all_words))
    current_points = sum((points(word['word'])[0] for word in all_words if word['foundBy'] is not None))
    letters = list(set(daily_word))

    if letters[3] != special_character:
        index_ = letters.index(special_character)
        letters[index_], letters[3] = letters[3], letters[index_]

    all_words.sort(key=lambda x: x['word'])
    return {
        'primary_word': daily_word,
        'primary_character': special_character,
        'all_letters': letters,
        'all_words': all_words,
        'max_points': max_points,
        'current_points': current_points
    }


@app.route('/date/<date>/user/<user>/submit', methods=['POST'])
@dbc
def submit(date: str, user: str, db_conn: MySQLdb.cursors.Cursor):
    date = datetime.datetime.strptime(date, '%Y-%m-%d')
    json_obj = request.get_json()
    word = json_obj['word']
    profile_picture = json_obj['profilePicture']

    # reinit words
    db_conn.execute('select specialcharacter from speelingbee.dailyword where date=%s', (date,))
    row = db_conn.fetchone()
    try:
        special_character = row[0]
    except IndexError:
        requests.get(os.path.join(os.getenv("routes/nodejs_server"), f'date/{date.date()}/words'))
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
            db_conn.execute('update speelingbee.words set foundBy=%s '
                            'where date=%s and word=%s', (user, date, word))
            db_conn.execute('update users.users set profilePicture=%s where email=%s', (profile_picture, user))
            num_points, is_pangram = points(word)

            current_points = update_points_gathered(db_conn, date, num_points)
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
    words = requests.get(url_for('get_words_of_day', date=date, _external=True))
    words = json.loads(words.content)

    word_to_pangram = {word['word']: points(word['word'])[1] for word in words['all_words']}
    for pangram_word in {k: v for k, v in word_to_pangram.items() if v}:
        index_ = next(i for i, v in enumerate(words['all_words']) if v['word'] == pangram_word)
        words['all_words'].insert(0, words['all_words'].pop(index_))
    rank = get_rank(words['current_points'], words['max_points'])

    return render_template('summary.html', date=date, rank=rank, all_letters=words['all_letters'],
                           all_words=words['all_words'], word_to_pangram=word_to_pangram)


@app.route('/date/<date>/todaysHints', methods=['GET'])
def todays_hints(date: str):
    words = requests.get(url_for('get_words_of_day', date=date, _external=True))
    words = json.loads(words.content)

    primary_character = words['all_letters'].pop(words['all_letters'].index(words['primary_character']))
    words['all_letters'] = sorted(words['all_letters'])
    words['all_letters'].insert(0, primary_character)

    num_words = len(words['all_words'])
    num_points = sum(points(word['word'])[0] for word in words['all_words'])
    num_pangrams = len([word for word in words['all_words'] if len(set(word['word'])) == 7])

    word_lengths = set([len(word['word']) for word in words['all_words']])

    letter_to_counts = {}
    for letter in words['all_letters']:
        letter_to_counts[letter] = [len([word for word in words['all_words']
                                         if word['word'][0] == letter and len(word['word']) == length])
                                    for length in sorted(list(word_lengths))]
        letter_to_counts[letter].append(sum(letter_to_counts[letter]))

    totals = [sum(letter_to_counts[letter][i] for letter in letter_to_counts)
              for i in range(len(letter_to_counts[words['primary_character']]))]

    all_two_letter_pairs = set([word['word'][:2] for word in words['all_words']])
    all_two_letter_counts = []
    for letter in words['all_letters']:
        row = []
        for pair in [word for word in all_two_letter_pairs if word[0] == letter]:
            all_words_matching_start = [word for word in words['all_words'] if word['word'][:2] == pair]
            found = [word for word in all_words_matching_start if word['foundBy'] is not None]
            row.append((pair, len(found), len(all_words_matching_start)))
        all_two_letter_counts.append(row)
    return render_template('todays_hints.html', date=date, num_words=num_words,
                           num_points=num_points, num_pangrams=num_pangrams, word_lengths=word_lengths,
                           all_letters=words['all_letters'], primary_character=words['primary_character'],
                           letter_to_counts=letter_to_counts, totals=totals,
                           two_letter_counts=all_two_letter_counts)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
