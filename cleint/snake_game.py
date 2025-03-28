import pygame
import sys
import random
from networking import ServerAPI

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CELL_SIZE = 20

SNAKE_COLOR = (0, 255, 0)       
FOOD_COLOR = (255, 0, 0)        
TEXT_COLOR = (255, 255, 255)    
BGCOLOR = (0, 0, 0)             
BOUNDARY_COLOR = (255, 255, 0)  

class SnakeGame:
    def get_stats(self):
        if not self.token:
            return "ERROR|User not authenticated"
        return self.send_request(f"STATS|{self.token}")

    def draw_elements(self):
        """Draw the background, boundary, snake, food, and score."""
        self.screen.fill(BGCOLOR)

        # Draw boundary
        pygame.draw.rect(self.screen, BOUNDARY_COLOR, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 4)

        # Draw the snake
        for x, y in self.snake_positions:
            pygame.draw.rect(self.screen, SNAKE_COLOR, (x, y, CELL_SIZE, CELL_SIZE))

        # Draw the food
        fx, fy = self.food_position
        pygame.draw.rect(self.screen, FOOD_COLOR, (fx, fy, CELL_SIZE, CELL_SIZE))

        # Display the score
        score_text = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_text, (10, 10))

    def check_collisions(self):
        """Detect collisions with walls or itself."""
        head_x, head_y = self.snake_positions[0]

        # Check collision with walls
        if head_x < 0 or head_x >= SCREEN_WIDTH or head_y < 0 or head_y >= SCREEN_HEIGHT:
            self.game_over = True

        # Check collision with itself
        if len(self.snake_positions) > 4 and (self.snake_positions[0] in self.snake_positions[1:]):
            self.game_over = True

    def update_snake(self):
        """Move the snake in the current direction and check for food collision."""
        head_x, head_y = self.snake_positions[0]

        if self.snake_direction == "UP":
            head_y -= CELL_SIZE
        elif self.snake_direction == "DOWN":
            head_y += CELL_SIZE
        elif self.snake_direction == "LEFT":
            head_x -= CELL_SIZE
        elif self.snake_direction == "RIGHT":
            head_x += CELL_SIZE

        new_head = (head_x, head_y)
        self.snake_positions.insert(0, new_head)

        snake_rect = pygame.Rect(head_x, head_y, CELL_SIZE, CELL_SIZE)
        food_x, food_y = self.food_position
        food_rect = pygame.Rect(food_x, food_y, CELL_SIZE, CELL_SIZE)

        if snake_rect.colliderect(food_rect):
            self.score += 1
            self.food_position = self.random_food_position()  
            print(f"Food eaten! Score is now {self.score}")
        else:
            self.snake_positions.pop()

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Multiplayer Snake")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)

        self.server_api = ServerAPI()
        self.username = None

        self.reset_game()

    def reset_game(self):
        """Reset snake positions, direction, food, and score."""
        self.snake_positions = [
            (100, 50),  
            (80, 50),
            (60, 50),   
        ]
        self.snake_direction = "RIGHT"
        self.food_position = self.random_food_position()
        self.score = 0
        self.game_over = False

    def random_food_position(self):
        """Return a random (x, y) position, aligned to the grid."""
        max_x = (SCREEN_WIDTH - CELL_SIZE) // CELL_SIZE
        max_y = (SCREEN_HEIGHT - CELL_SIZE) // CELL_SIZE
        x = random.randint(0, max_x) * CELL_SIZE
        y = random.randint(0, max_y) * CELL_SIZE
        return (x, y)

    def run(self):
        """Main game loop: handle events, update, draw."""
        self.handle_user_auth() 
        while True:
            self.handle_events()

            if not self.game_over:
                self.update_snake()
                self.check_collisions()
                self.draw_elements()
            else:
                self.show_game_over()

            pygame.display.update()
            self.clock.tick(10)  

    def handle_user_auth(self):
        """Prompt user to sign up or log in (console-based)."""
        print("Welcome! Please choose an option:")
        print("1) Sign Up")
        print("2) Log In")
        choice = input("Enter 1 or 2: ")

        username = input("Username: ")
        password = input("Password: ")

        if choice == "1":
            email = input("Email: ")  
            response = self.server_api.signup(username, password, email)  
            print(response)
            if "SUCCESS" in response:
                print("Sign up successful! Now logging in...")
            else:
                print("Sign up failed:", response)
                sys.exit(0)

        response = self.server_api.login(username, password)
        if "SUCCESS" in response:
            self.username = username
            print(f"Logged in as {username}")
        else:
            print("Login failed:", response)
            sys.exit(0)

    def show_game_over(self):
        """Handle GAME OVER screen."""
        self.server_api.submit_score(self.score)
        
        while True:
            self.screen.fill(BGCOLOR)
            game_over_text = self.font.render(
                "GAME OVER! [R]estart | [Q]uit | [G]lobal LB | [L]ocal LB | [S]tats",
                True,
                TEXT_COLOR
            )
            self.screen.blit(game_over_text, (SCREEN_WIDTH // 8, SCREEN_HEIGHT // 2))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                        return  
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_g:
                        self.show_global_leaderboard()
                    elif event.key == pygame.K_l:
                        self.show_local_leaderboard()
                    elif event.key == pygame.K_s:
                        self.show_stats_screen()

    def show_global_leaderboard(self):
        """Fetch and display global leaderboard (Top 10 scores across all users)."""
        leaderboard_data = self.server_api.get_global_leaderboard()

        print("\n=== GLOBAL LEADERBOARD ===")

        if "LEADERBOARD" in leaderboard_data:
            leaderboard_entries = leaderboard_data.split("|")[1:]

            if not leaderboard_entries or leaderboard_entries == ['']:
                print("No scores available yet.")
                return

            for i, entry in enumerate(leaderboard_entries):
                try:
                    username, score = entry.split(":")
                    print(f"{i+1}. {username} - {score}")
                except ValueError:
                    print(f"Skipping malformed entry: {entry}")

        else:
            print("Error retrieving leaderboard.")


    def show_local_leaderboard(self):
        """Fetch and display local leaderboard (Top 10 scores of logged-in user)."""
        leaderboard_data = self.server_api.get_local_leaderboard()
        print("\n=== YOUR BEST SCORES ===")
        if "LEADERBOARD" in leaderboard_data:
            leaderboard_entries = leaderboard_data.split("|")[1:]
            for i, score in enumerate(leaderboard_entries):
                print(f"{i+1}. Score: {score}")
        else:
            print("Error retrieving leaderboard.")

    def show_stats_screen(self):
        """Fetch and display player statistics."""
        stats_data = self.server_api.get_stats()

        print("\n=== PLAYER STATS ===")

        if "STATS" in stats_data:
            stats_parts = stats_data.split("|")[1:]
            for stat in stats_parts:
                print(stat)
        else:
            print("No stats available yet.")


    def handle_events(self):
        """Process user input/events (arrow keys, quit, etc.)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and self.snake_direction != "DOWN":
                    self.snake_direction = "UP"
                elif event.key == pygame.K_DOWN and self.snake_direction != "UP":
                    self.snake_direction = "DOWN"
                elif event.key == pygame.K_LEFT and self.snake_direction != "RIGHT":
                    self.snake_direction = "LEFT"
                elif event.key == pygame.K_RIGHT and self.snake_direction != "LEFT":
                    self.snake_direction = "RIGHT"

def main():
    game = SnakeGame()
    game.run()

if __name__ == "__main__":
    main()

