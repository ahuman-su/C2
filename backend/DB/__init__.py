import os

import pymysql

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "c2")
DB_USER = os.getenv("DB_USER", "c2")
DB_PASSWORD = os.getenv("DB_PASSWORD", "c2_pass")
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        charset=DB_CHARSET,
        cursorclass=pymysql.cursors.DictCursor,
    )
