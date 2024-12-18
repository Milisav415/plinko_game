# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import pygame
import sys
import math
import random

pygame.init()

# Screen dimensions
WIDTH = 800
HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
RED = (255, 0, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Casino-Style Plinko with Adjusted Multipliers for EV < 1")
clock = pygame.time.Clock()

# Game parameters
GRAVITY = 0.1
BALL_RADIUS = 10
PEG_RADIUS = 5

# Define the number of rows and top row pins
N = 10
initial_pegs = 3
vertical_spacing = 60
horizontal_spacing = 50
top_offset = 100

max_pegs = initial_pegs + (N - 1)
total_width = (max_pegs - 1) * horizontal_spacing

# Create peg positions in a triangular layout
pegs = []
for r in range(N):
    row_pegs = initial_pegs + r
    row_width = (row_pegs - 1) * horizontal_spacing
    row_left = (WIDTH - row_width) / 2
    y = top_offset + r * vertical_spacing
    for c in range(row_pegs):
        x = row_left + c * horizontal_spacing
        pegs.append((x, y))

# The bins are at the bottom
num_bins = max_pegs + 1
bin_width = horizontal_spacing
bottom_y = top_offset + N * vertical_spacing + 50
start_x = (WIDTH - (num_bins * bin_width)) / 2
bins = []
for i in range(num_bins):
    bx1 = start_x + i * bin_width
    bx2 = bx1 + bin_width
    bins.append((bx1, bx2))

# Probability and multiplier calculation
def normal_pdf(x, mean=0, std=1):
    return (1.0 / (math.sqrt(2 * math.pi) * std)) * math.exp(-0.5 * ((x - mean) / std)**2)

def integrate_simpson(f, a, b, n=50):
    # Numerical integration using Simpson's rule
    if n % 2 == 1:
        n += 1
    dx = (b - a) / n
    total = f(a) + f(b)
    for i in range(1, n):
        x = a + i * dx
        w = 4 if i % 2 == 1 else 2
        total += w * f(x)
    return total * dx / 3.0

def compute_bin_probabilities(num_bins, x_min=-3, x_max=3):
    # Divide [x_min, x_max] into num_bins equal segments
    dx = (x_max - x_min) / num_bins
    probabilities = []
    for i in range(num_bins):
        a = x_min + i * dx
        b = a + dx
        p = integrate_simpson(normal_pdf, a, b, n=100)
        probabilities.append(p)
    return probabilities

bin_probabilities = compute_bin_probabilities(num_bins, x_min=-3, x_max=3)

# Compute raw multipliers as inverse of probability
raw_multipliers = []
for p in bin_probabilities:
    # If p is extremely small (practically zero), handle gracefully
    if p < 1e-15:
        # Assign a very large number, but still finite
        raw_multipliers.append(1e9)
    else:
        raw_multipliers.append(1.0 / p)

# Compute the raw EV
# EV_raw = sum(prob * raw_multiplier) = sum(1) = num_bins
EV_raw = num_bins

# We want EV < 1, so we scale all multipliers down by a factor > num_bins
scale_factor = num_bins * 1.1  # This makes EV ~ 0.909
payouts = [m / scale_factor for m in raw_multipliers]

# Now EV = sum(prob_i * payouts[i]) ~ EV_raw / scale_factor = num_bins / (num_bins*1.1) = ~0.909 < 1

ball_x = None
ball_y = None
ball_vx = 0
ball_vy = 0
ball_dropping = False
current_payout = 0.0
message = "Press SPACE to drop the ball (Bet: 1 Credit)"

def drop_ball():
    global ball_x, ball_y, ball_vx, ball_vy, ball_dropping, current_payout, message
    ball_x = WIDTH / 2
    ball_y = 50
    ball_vx = 0
    ball_vy = 0
    ball_dropping = True
    current_payout = 0.0
    message = "Ball dropped..."

def update_ball():
    global ball_x, ball_y, ball_vx, ball_vy, ball_dropping, current_payout, message

    if not ball_dropping:
        return

    # Apply gravity
    ball_vy += GRAVITY

    # Update position
    ball_x += ball_vx
    ball_y += ball_vy

    # Check collisions with pegs
    for px, py in pegs:
        dx = ball_x - px
        dy = ball_y - py
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < (BALL_RADIUS + PEG_RADIUS):
            # Collision detected
            overlap = (BALL_RADIUS + PEG_RADIUS) - dist
            angle = math.atan2(dy, dx)
            ball_x += math.cos(angle) * overlap
            ball_y += math.sin(angle) * overlap

            # Random bounce
            ball_vx = (ball_vx * -0.5) + (random.uniform(-0.5, 0.5))
            ball_vy *= 0.9

    # Check if ball reached bottom
    if ball_y > bottom_y:
        # Determine which bin it fell into
        landed_bin = None
        for i, (bx1, bx2) in enumerate(bins):
            if bx1 <= ball_x <= bx2:
                landed_bin = i
                break
        if landed_bin is not None:
            current_payout = payouts[landed_bin]
            message = f"You won {current_payout:.2f}x your bet! Press SPACE to play again."
        else:
            current_payout = 0.0
            message = "You won nothing! Press SPACE to play again."
        ball_dropping = False

def draw_pegs():
    for (px, py) in pegs:
        pygame.draw.circle(screen, GREY, (int(px), int(py)), PEG_RADIUS)

def draw_bins():
    for i, (bx1, bx2) in enumerate(bins):
        rect = pygame.Rect(bx1, bottom_y, bin_width, 50)
        pygame.draw.rect(screen, GREY, rect)
        # Draw payout text
        font = pygame.font.SysFont(None, 24)
        txt = f"{payouts[i]:.2f}x"
        score_surf = font.render(txt, True, BLACK)
        score_rect = score_surf.get_rect(center=(bx1 + bin_width/2, bottom_y + 25))
        screen.blit(score_surf, score_rect)

def draw_ball():
    if ball_x is not None and ball_y is not None and ball_dropping:
        pygame.draw.circle(screen, RED, (int(ball_x), int(ball_y)), BALL_RADIUS)

def draw_message():
    font = pygame.font.SysFont(None, 32)
    message_surf = font.render(message, True, BLACK)
    message_rect = message_surf.get_rect(center=(WIDTH//2, 30))
    screen.blit(message_surf, message_rect)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    running = True
    while running:
        clock.tick(FPS)
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not ball_dropping:
                    drop_ball()

        update_ball()

        # Draw everything
        draw_pegs()
        draw_bins()
        draw_ball()
        draw_message()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
