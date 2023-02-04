import psycopg2
from VK_settings import db_name, db_user_name, db_password


def check_pair(user_id,meet_id):
    with conn.cursor() as cur:
        cur.execute("""
        SELECT pair_id FROM pairs WHERE user_id=%s AND meet_it=%s;""",(user_id, meet_id))
        result = cur.fetchall()
        if len(result) > 0:
            return True
        else:
            return False

def add_pair(user_id, meet_id):
    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO pairs(user_id, meet_it) VALUES(%s, %s);
        """, (user_id, meet_id))
    conn.commit()

def user_registration(user_id):
    with conn.cursor() as cur:
        cur.execute("""
        INSERT INTO users(user_id) VALUES(%s);
        """, ([user_id]))
    conn.commit()  

def is_user_registered(user_id):
    with conn.cursor() as cur:
        cur.execute("""
        SELECT user_id FROM users WHERE user_id=%s;""",(user_id,))
        result = cur.fetchall()
        if len(result) > 0:
            return True
        else:
            return False  

def create_db():
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS pairs(
            pair_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id),
            meet_it INTEGER NOT NULL
        );
        """)
    conn.commit()

def run_db():
    global conn 
    conn = psycopg2.connect(database=db_name, user=db_user_name, password=db_password)

def disconnect_db():
    conn.close()