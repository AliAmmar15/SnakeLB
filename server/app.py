import socket
import threading
import sqlite3
import bcrypt
import datetime
import jwt
import time

DB_NAME = "snake_game.db"
SECRET_KEY = "supersecretkey"

db_lock = threading.Lock()  # 🔒 Added global lock for thread safety

def init_db():
    """Initialize the database and create required tables if they do not exist."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=10)  # ✅ Set timeout to prevent locking
    cursor = conn.cursor()

    # Enable WAL mode for concurrent reads/writes
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
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

    conn.commit()
    conn.close()
    print("[✔] Database initialized successfully.")

class GameServer:
    def __init__(self, host="127.0.0.1", port=5050):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # ✅ Use a single persistent connection for better performance
        self.db_conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=10)
        self.db_cursor = self.db_conn.cursor()

    def start(self):
        """Start the server and listen for client connections."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server running on {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"New connection from {addr}")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        """Handle incoming client requests."""
        try:
            while True:
                request = client_socket.recv(1024).decode()
                if not request:
                    break

                command, *args = request.split("|")

                if command == "SIGNUP":
                    response = self.signup(*args)
                elif command == "LOGIN":
                    response = self.login(*args)
                elif command == "SUBMIT_SCORE":
                    response = self.submit_score(*args)
                elif command == "GLOBAL_LEADERBOARD":
                    response = self.get_global_leaderboard()
                elif command == "LOCAL_LEADERBOARD":
                    response = self.get_local_leaderboard(*args)
                elif command == "STATS":
                    response = self.get_stats(*args)
                else:
                    response = "ERROR|Invalid Command"

                client_socket.send(response.encode())
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def execute_query(self, query, params=(), fetch_one=False, fetch_all=False):
        """Execute SQL queries with a global lock to avoid database locking issues."""
        max_retries = 5
        delay = 0.5

        for attempt in range(max_retries):
            with db_lock:  # 🔒 Ensures only one thread writes at a time
                try:
                    self.db_cursor.execute(query, params)
                    if fetch_one:
                        result = self.db_cursor.fetchone()
                    elif fetch_all:
                        result = self.db_cursor.fetchall()
                    else:
                        result = None

                    self.db_conn.commit()
                    return result
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        print(f"Database is locked. Retrying ({attempt+1}/{max_retries})...")
                        time.sleep(delay)
                    else:
                        raise e

    def signup(self, username, password, email):
        """Register a new user."""
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        try:
            self.execute_query(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                (username, hashed_pw, email)
            )
            return "SUCCESS|User registered"
        except sqlite3.IntegrityError:
            return "ERROR|Username or email already exists"

    def login(self, username, password):
        """Authenticate user and return JWT token."""
        row = self.execute_query("SELECT id, password FROM users WHERE username = ?", 
                                 (username,), fetch_one=True)

        if row:
            user_id, stored_hashed = row
            if bcrypt.checkpw(password.encode(), stored_hashed):
                token = jwt.encode(
                    {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
                    SECRET_KEY,
                    algorithm="HS256"
                )
                return f"SUCCESS|{token}"
        return "ERROR|Invalid credentials"

    def submit_score(self, token, score):
        """Submit a player's score."""
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded["user_id"]

            self.execute_query("INSERT INTO scores (user_id, score) VALUES (?, ?)", 
                               (user_id, int(score)))
            return "SUCCESS|Score submitted"
        except jwt.ExpiredSignatureError:
            return "ERROR|Token expired"
        except Exception as e:
            return f"ERROR|{str(e)}"

    def get_global_leaderboard(self):
        """Retrieve the global leaderboard (Top 10 highest scores)."""
        rows = self.execute_query("""
            SELECT users.username, MAX(scores.score)
            FROM scores
            JOIN users ON scores.user_id = users.id
            GROUP BY scores.user_id
            ORDER BY MAX(scores.score) DESC
            LIMIT 10
        """, fetch_all=True)

        leaderboard = "GLOBAL_LEADERBOARD|" + "|".join([f"{row[0]}:{row[1]}" for row in rows])
        return leaderboard

    def get_local_leaderboard(self, token):
        """Retrieve the player's top 10 personal scores."""
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded["user_id"]

            rows = self.execute_query(
                "SELECT score FROM scores WHERE user_id = ? ORDER BY score DESC LIMIT 10", 
                (user_id,), fetch_all=True
            )

            leaderboard = "LOCAL_LEADERBOARD|" + "|".join([str(row[0]) for row in rows])
            return leaderboard
        except jwt.ExpiredSignatureError:
            return "ERROR|Token expired"
        except Exception as e:
            return f"ERROR|{str(e)}"

    def get_stats(self, token):
        """Retrieve player's game statistics (highest score, total games played, average score)."""
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded["user_id"]

            highest_score = self.execute_query(
                "SELECT MAX(score) FROM scores WHERE user_id = ?", 
                (user_id,), fetch_one=True
            )[0] or 0

            total_games = self.execute_query(
                "SELECT COUNT(*) FROM scores WHERE user_id = ?", 
                (user_id,), fetch_one=True
            )[0] or 0

            avg_score = self.execute_query(
                "SELECT AVG(score) FROM scores WHERE user_id = ?", 
                (user_id,), fetch_one=True
            )[0] or 0

            return f"STATS|Highest Score: {highest_score} | Total Games: {total_games} | Average Score: {round(avg_score, 2)}"
        except jwt.ExpiredSignatureError:
            return "ERROR|Token expired"
        except Exception as e:
            return f"ERROR|{str(e)}"

if __name__ == "__main__":
    init_db()
    server = GameServer()
    server.start()
