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
        res = func(*args, **kwargs)
        connection.commit()
        connection.cursor().close()
        connection.close()
        return res
    return wrapper
