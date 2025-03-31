import sqlite3

DB_NAME = "snake_game.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "email" not in columns:
        print("Updating database schema: Adding 'email' column to users table.")
        
        
        cursor.execute("ALTER TABLE users RENAME TO users_old")

        
        cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE
        )
        """)

        
        cursor.execute("""
        INSERT INTO users (id, username, password)
        SELECT id, username, password FROM users_old
        """)

       
        cursor.execute("DROP TABLE users_old")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
