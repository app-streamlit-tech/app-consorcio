from .config import DBNAME, USER, PASSWORD, HOST, PORT
import psycopg2

class Db_pg:
    
    def connect():
        conn = psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT)
        cur = conn.cursor()
        return cur, conn

    def disconnect(cur, conn):
        cur.close()
        conn.close()