import socket

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5050

class ServerAPI:
    def __init__(self):
        self.token = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((SERVER_IP, SERVER_PORT))

    def send_request(self, request):
        """Send request to server and get response."""
        self.client_socket.send(request.encode())
        return self.client_socket.recv(1024).decode()

    def signup(self, username, password, email):
        """Sign up a new user with an email."""
        response = self.send_request(f"SIGNUP|{username}|{password}|{email}")
        return response

    def login(self, username, password):
        """Login the user and store the JWT token."""
        response = self.send_request(f"LOGIN|{username}|{password}")
        if response.startswith("SUCCESS"):
            _, self.token = response.split("|")
        return response

    def submit_score(self, score):
        """Submit a player's score to the server."""
        if not self.token:
            return "ERROR|User not authenticated"
        return self.send_request(f"SUBMIT_SCORE|{self.token}|{score}")

    def get_global_leaderboard(self):
        """Fetch the global leaderboard (top 10 highest scores)."""
        return self.send_request("GLOBAL_LEADERBOARD")

    def get_local_leaderboard(self):
        """Fetch the local leaderboard (top 10 scores of the logged-in player)."""
        if not self.token:
            return "ERROR|User not authenticated"
        return self.send_request(f"LOCAL_LEADERBOARD|{self.token}")

    def get_stats(self):
        """Retrieve detailed game performance stats for the logged-in player."""
        if not self.token:
            return "ERROR|User not authenticated"
        return self.send_request(f"STATS|{self.token}")

    def update_profile(self, new_username, new_email):
        """Update the player's username and email."""
        if not self.token:
            return "ERROR|User not authenticated"
        return self.send_request(f"UPDATE_PROFILE|{self.token}|{new_username}|{new_email}")

    def get_profile(self):
        """Retrieve the player's profile details."""
        if not self.token:
            return "ERROR|User not authenticated"
        return self.send_request(f"GET_PROFILE|{self.token}")

    def close_connection(self):
        """Close the TCP connection."""
        self.client_socket.close()
