import os
import psycopg2


def connect():
    return psycopg2.connect(
        'dbname = ' + os.environ['DBNAME'] +
        ' user = ' + os.environ['DBUSER'] +
        ' password = ' + os.environ['DBPASS'] +
        ' port = ' + os.environ['DBPORT'])