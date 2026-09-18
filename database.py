import sqlite3

DB_NAME = "taroyo.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT NOT NULL,
        assignment_name TEXT NOT NULL,
        due_date TEXT,
        completed INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

def add_assigment (class_name,assignment_name,due_date=None):
    conn=get_connection()
    cursor=conn.cursor()

    cursor.execute("""
        INSERT INTO assignments
        (class_name,assignment_name,due_date)
        VALUES (?,?,?)
        """,(class_name,assignment_name,due_date))
    conn.commit()
    conn.close()

def get_assignments():
    conn= get_connection()
    cursor= conn.cursor()

    cursor.execute("""
        SELECT id,class_name,assignment_name,due_date,completed
        FROM assignments
        ORDER BY completed ASC,due_date ASC
        """)
    assignments = cursor.fetchall ()
    conn.close()
    return assignments

def complete_assignment(assignment_id):
    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("""
    UPDATE assignments
    SET completed = 1
    WHERE id = ?
    """,(assignment_id,))
    conn.commit()
    conn.close()

def delete_assignment(assignment_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""DELETE
                          FROM assignments
                          WHERE id = ?
                       """, (assignment_id,))
        conn.commit()
        conn.close()