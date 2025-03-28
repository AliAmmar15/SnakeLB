# 🐍 Snake Game Leaderboard

A snake game with a leaderboard, player stats, and authentication using Python, Flask, SQLite, and Pygame.

## 🚀 Features
- User Authentication (Sign Up, Login with JWT Tokens)
- Score Submission (Send scores to the server after each game)
- Global Leaderboard (See top players across all users)
- Local Leaderboard (See your personal best scores)
- Player Statistics (Track highest score, total games, average score)
- Multiplayer-ready server using Flask & SQLite
- Smooth Pygame UI for a classic snake experience

## 🛠️ Installation Guide

### 1️⃣ Clone the Repository
Clone the repository and navigate into the project directory.

### 2️⃣ Set Up Virtual Environments (Recommended)
Set up a virtual environment for both the server and client.

Install dependencies from requirements.txt.

## 🎮 Running the Game

### 1️⃣ Start the Server
Navigate to the server directory.

Activate the virtual environment.

Run the server script.

### 2️⃣ Start the Game (Client)
Navigate to the client directory.

Activate the virtual environment.

Run the game script.

Choose to sign up or log in when prompted.

## 🎯 How to Play
- Use arrow keys to control the snake.
- Eat food to grow your score.
- Avoid hitting walls or yourself.
- After game over, submit your score.
- Press "G" for the global leaderboard.
- Press "L" for the local leaderboard.
- Press "S" for player statistics.

## 🖥️ API Endpoints
The server provides the following API endpoints:

- `/signup` – Register a new user
- `/login` – Authenticate a user
- `/submit_score` – Submit game score
- `/leaderboard` – Fetch the top 10 global scores
- `/stats` – Fetch the player's statistics

## 🛠️ Tech Stack
- Python (Flask for the server, Pygame for the client)
- SQLite (Database for users and scores)
- JWT Authentication (Secure login system)
- Socket Communication (Client-server interaction)


## 👨‍💻 Contributors
- Ali Ammar
- Omar Mahmoud

