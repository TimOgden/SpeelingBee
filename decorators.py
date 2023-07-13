import os
from functools import wraps
import MySQLdb
from google.cloud.sql.connector import Connector
import sqlalchemy


def dbc(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # initialize parameters
        connection_name = 'speelingbee:us-central1:speeling-bee'

        connector = Connector()
        def getconn():
            conn = connector.connect(
                connection_name,
                'pymysql',
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWD'),
                db=''
            )
            return conn

        pool = sqlalchemy.create_engine(
            'mysql+pymysql://',
            creator=getconn
        )
        with pool.connect() as db_conn:
            kwargs['db_conn'] = db_conn
            return func(*args, **kwargs)
    return wrapper
