import socket
import threading
import sqlite3
import bcrypt
import datetime
import jwt

DB_NAME = "snake_game.db"
SECRET_KEY = "supersecretkey"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    conn.commit()
    conn.close()

class GameServer:
    def __init__(self, host="127.0.0.1", port=5050):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server running on {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"New connection from {addr}")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
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
                elif command == "UPDATE_PROFILE":
                    response = self.update_profile(*args)
                elif command == "GET_PROFILE":
                    response = self.get_profile(*args)
                else:
                    response = "ERROR|Invalid Command"

                client_socket.send(response.encode())
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def signup(self, username, password, email):
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                           (username, hashed_pw, email))
            conn.commit()
            conn.close()
            return "SUCCESS|User registered"
        except sqlite3.IntegrityError:
            return "ERROR|Username or email already exists"

    def login(self, username, password):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row:
            user_id, stored_hashed = row
            if bcrypt.checkpw(password.encode(), stored_hashed):
                token = jwt.encode({"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, 
                                   SECRET_KEY, algorithm="HS256")
                return f"SUCCESS|{token}"
        return "ERROR|Invalid credentials"

    def submit_score(self, token, score):
        """Handle score submission."""
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded["user_id"]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Ensure score is saved correctly
            cursor.execute("INSERT INTO scores (user_id, score) VALUES (?, ?)", (user_id, int(score)))
            conn.commit()
            conn.close()

            return "SUCCESS|Score submitted"
        except jwt.ExpiredSignatureError:
            return "ERROR|Token expired"
        except Exception as e:
            return f"ERROR|{str(e)}"


    def get_global_leaderboard(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT users.username, MAX(scores.score)
            FROM scores
            JOIN users ON scores.user_id = users.id
            GROUP BY scores.user_id
            ORDER BY MAX(scores.score) DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        conn.close()

        leaderboard = "GLOBAL_LEADERBOARD|" + "|".join([f"{row[0]}:{row[1]}" for row in rows])
        return leaderboard

    def get_local_leaderboard(self, token):
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded["user_id"]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT score FROM scores WHERE user_id = ? ORDER BY score DESC LIMIT 10", (user_id,))
            rows = cursor.fetchall()
            conn.close()

            leaderboard = "LOCAL_LEADERBOARD|" + "|".join([str(row[0]) for row in rows])
            return leaderboard
        except jwt.ExpiredSignatureError:
            return "ERROR|Token expired"
        except Exception as e:
            return f"ERROR|{str(e)}"

    def get_stats(self, token):
        """Fetch player's game statistics (highest score, total games played, average score)."""
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded["user_id"]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Get highest score
            cursor.execute("SELECT MAX(score) FROM scores WHERE user_id = ?", (user_id,))
            highest_score = cursor.fetchone()[0] or 0

         # Get total games played
            cursor.execute("SELECT COUNT(*) FROM scores WHERE user_id = ?", (user_id,))
            total_games = cursor.fetchone()[0] or 0

            # Get average score
            cursor.execute("SELECT AVG(score) FROM scores WHERE user_id = ?", (user_id,))
            avg_score = cursor.fetchone()[0] or 0

            conn.close()

            return f"STATS|Highest Score: {highest_score} | Total Games: {total_games} | Average Score: {round(avg_score, 2)}"
        except jwt.ExpiredSignatureError:
            return "ERROR|Token expired"
        except Exception as e:
            return f"ERROR|{str(e)}"


    def update_profile(self, token, new_username, new_email):
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded["user_id"]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET username = ?, email = ? WHERE id = ?", 
                           (new_username, new_email, user_id))
            conn.commit()
            conn.close()
            return "SUCCESS|Profile updated"
        except jwt.ExpiredSignatureError:
            return "ERROR|Token expired"
        except Exception as e:
            return f"ERROR|{str(e)}"

    def get_profile(self, token):
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded["user_id"]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT username, email, total_games, highest_score FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return f"PROFILE|{row[0]}|{row[1]}|{row[2]}|{row[3]}"
            return "ERROR|Profile not found"
        except jwt.ExpiredSignatureError:
            return "ERROR|Token expired"
        except Exception as e:
            return f"ERROR|{str(e)}"

if __name__ == "__main__":
    init_db()
    server = GameServer()
    server.start()
