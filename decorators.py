import os
from functools import wraps
import MySQLdb


def dbc(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        connection = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWD')
        )
        kwargs['db_conn'] = connection.cursor()
        return func(*args, **kwargs)
    return wrapper
