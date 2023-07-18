import datetime
import os
from typing import Union

import sqlalchemy
from sqlalchemy.engine.base import Connection

import numpy as np


with open(os.getenv('words_loc'), 'r') as f:
    ENGLISH_WORDS = f.read().split(',')
with open(os.getenv('primary_words_loc'), 'r') as f:
    PRIMARY_WORDS = f.read().split(',')


def get_all_words(word: str, special_character: str) -> list[tuple[str, Union[str, None]]]:
    characters = list(set(list(word)))
    all_words = [d for d in ENGLISH_WORDS if special_character in d and all(char in characters for char in d)]

    return [(word, None) for word in all_words]


def get_rank(current_points: int, max_points: int) -> str:
    score = current_points / max_points
    if score == 1:
        return 'Queen Bee'
    elif score >= 0.7:
        return 'Genius'
    elif score >= 0.5:
        return 'Amazing'
    elif score >= 0.4:
        return 'Great'
    elif score >= 0.25:
        return 'Nice'
    elif score >= 0.15:
        return 'Solid'
    elif score >= 0.08:
        return 'Good'
    elif score >= 0.05:
        return 'Moving Up'
    elif score >= 0.02:
        return 'Good Start'
    return 'Beginner'


def get_primary_word() -> tuple[str, str]:
    word = np.random.choice(PRIMARY_WORDS)
    return word, np.random.choice([d for d in word])


def update_points_gathered(dbc: Connection, date: datetime.datetime, points_: int) -> int:
    current_points_gathered = dbc.execute(sqlalchemy.text('select pointsgathered from speelingbee.dailyword '
                                                          'where date=:date'),
                                          parameters={'date': date}).fetchone()[0]

    dbc.execute(sqlalchemy.text('update speelingbee.dailyword set pointsgathered=:points where date=:date'),
                parameters={'points': points_ + current_points_gathered, 'date': date})
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
