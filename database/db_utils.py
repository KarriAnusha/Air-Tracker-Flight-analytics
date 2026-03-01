from database.db_connection import get_connection


def execute_query(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("DB ERROR:", e)
    finally:
        cur.close()
        conn.close()
