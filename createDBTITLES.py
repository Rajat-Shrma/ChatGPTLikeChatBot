import sqlite3

DBNAME = 'chat_titles.db'

def get_db_connection():
    conn = sqlite3.connect(
        database=DBNAME,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    return conn

def create_title_logs():
    conn = get_db_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS titles
    (thread_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
                 """)
    
    conn.commit()
    conn.close()
    
def insert_chat_title(thread_id,title):
    conn = get_db_connection()
    conn.execute("""
    INSERT INTO titles (thread_id, title)
    VALUES (?, ?)
    ON CONFLICT(thread_id)
    DO NOTHING
    """, (str(thread_id), title))

    conn.commit()
    conn.close()


def get_title(thread_id):
    conn= get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT title FROM titles WHERE thread_id = ?',(str(thread_id),))

    row = cursor.fetchone()
    if row is None:
        return "New Chat..."
    
    return row['title']

def update_title(thread_id, new_title):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE titles
        SET title = ?
        WHERE thread_id = ?
        """,
        (new_title, str(thread_id))
    )

    conn.commit()
    conn.close()



create_title_logs()
print(get_title('thread-1'))
insert_chat_title('thread-1','My title')
print(get_title('thread-1'))
