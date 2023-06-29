import datetime
from typing import Union

import MySQLdb
from english_words import get_english_words_set
import numpy as np

ENGLISH_WORDS = [d.upper() for d in get_english_words_set(['gcide'], lower=True, alpha=True) if len(d) > 3]
PRIMARY_WORDS = [d for d in ENGLISH_WORDS if len(set(d)) == 7]


def get_all_words(word: str, special_character: str) -> list[tuple[str, Union[str, None]]]:
    characters = list(set(list(word)))
    all_words = [d for d in ENGLISH_WORDS if special_character in d and all(char in characters for char in d)]

    return [(word, None) for word in all_words]


def get_primary_word() -> tuple[str, str]:
    word = np.random.choice(PRIMARY_WORDS)
    return word, np.random.choice([d for d in word])


def update_points_gathered(dbc: MySQLdb.cursors.Cursor, date: datetime.datetime, points_: int) -> int:
    dbc.execute('select pointsgathered from speelingbee.dailyword where date=%s', (date,))
    current_points_gathered = dbc.fetchone()[0]

    dbc.execute('update speelingbee.dailyword set pointsgathered=%s where date=%s',
                (points_ + current_points_gathered, date))
    return points_ + current_points_gathered


def points(word: str) -> tuple[int, bool]:
    if len(set(word)) == 7:
        return len(word) + 7, True
    return len(word), False


def main():
    # primary_word, primary_character = get_primary_word()
    all_words = get_all_words('ASTROITE', 'S')
    # print(primary_word, primary_character)
    print(all_words)
    print(len(all_words))


if __name__ == '__main__':
    main()
