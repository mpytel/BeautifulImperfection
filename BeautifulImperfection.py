import pygame
import sys
import math
import random
import os
import datetime
import json
from pygame import gfxdraw
import copy

# Import our classes
from classes.Button import Button
from classes.Element import Element
from classes.FractalStructure import FractalStructure
from classes.KnobControl import KnobControl

# Initialize pygame
pygame.init()
pygame.mixer.init()  # Initialize the mixer for audio

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Beautiful Imperfection")

# Define Slider class
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.active = False
        self.handle_radius = height * 1.5
        self.handle_color = (100, 100, 255)
        self.handle_hover_color = (150, 150, 255)
        self.track_color = (200, 200, 200)
        self.track_active_color = (150, 150, 200)
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', 12)

        # Calculate handle position
        self.handle_pos = self.get_handle_pos()

    def get_handle_pos(self):
        # Convert value to position
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + int(ratio * self.rect.width)

    def get_value_at_pos(self, x_pos):
        # Convert position to value
        ratio = max(0, min(1, (x_pos - self.rect.x) / self.rect.width))
        return self.min_val + ratio * (self.max_val - self.min_val)

    def update(self, mouse_pos, mouse_pressed):
        x, y = mouse_pos

        # Check if mouse is over handle
        handle_rect = pygame.Rect(
            self.handle_pos - self.handle_radius,
            self.rect.centery - self.handle_radius,
            self.handle_radius * 2,
            self.handle_radius * 2
        )
        self.is_hovered = handle_rect.collidepoint(x, y)

        # Update active state
        if mouse_pressed and self.is_hovered:
            self.active = True
        elif not mouse_pressed:
            self.active = False

        # Update value if active
        if self.active:
            self.value = self.get_value_at_pos(x)
            self.value = max(self.min_val, min(self.max_val, self.value))
            self.handle_pos = self.get_handle_pos()
            return True  # Value changed

        return False  # Value unchanged

    def draw(self, surface):
        # Draw track
        track_color = self.track_active_color if self.active else self.track_color
        pygame.draw.rect(surface, track_color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 1)  # Border

        # Draw handle
        handle_color = self.handle_hover_color if self.is_hovered or self.active else self.handle_color
        pygame.draw.circle(surface, handle_color, (self.handle_pos, self.rect.centery), self.handle_radius)
        pygame.draw.circle(surface, (0, 0, 0), (self.handle_pos, self.rect.centery), self.handle_radius, 1)  # Border

        # Draw label
        if self.label:
            label_text = self.font.render(self.label, True, (0, 0, 0))
            surface.blit(label_text, (self.rect.x, self.rect.y - 20))

        # Draw value
        value_text = self.font.render(f"{int(self.value)}", True, (0, 0, 0))
        surface.blit(value_text, (self.handle_pos - value_text.get_width() // 2, self.rect.centery + self.handle_radius + 5))

        # Draw difficulty labels
        if self.min_val == 1 and self.max_val == 10:  # Only for difficulty slider
            # No target
            if self.value <= 2:
                diff_text = self.font.render("No Target", True, (100, 100, 100))
            # Easy
            elif self.value <= 4:
                diff_text = self.font.render("Easy", True, (0, 150, 0))
            # Normal
            elif self.value <= 8:
                diff_text = self.font.render("Normal", True, (0, 0, 150))
            # Hard
            else:
                diff_text = self.font.render("Hard", True, (150, 0, 0))

            surface.blit(diff_text, (self.rect.x + self.rect.width + 10, self.rect.centery - diff_text.get_height() // 2))

def calculate_target_from_slider(level, difficulty_value):
    """Calculate target harmony based on difficulty slider value (1-10)"""
    # At difficulty 1, no target (0%)
    if difficulty_value <= 1:
        return 0

    # At difficulty 2-4 (easy): 30-40% base
    elif difficulty_value <= 4:
        # Map 2-4 to 0-1
        t = (difficulty_value - 2) / 2
        base_target = 30 + t * 10
        variation = (level % 3) * 2  # 0, 2, or 4 percent variation
        return min(75, base_target + variation + (level - 1) * 3)

    # At difficulty 5-8 (normal): 40-50% base
    elif difficulty_value <= 8:
        # Map 5-8 to 0-1
        t = (difficulty_value - 5) / 3
        base_target = 40 + t * 10
        variation = (level % 3) * 3  # 0, 3, or 6 percent variation
        return min(85, base_target + variation + (level - 1) * 4)

    # At difficulty 9-10 (hard): 50-60% base
    else:
        # Map 9-10 to 0-1
        t = (difficulty_value - 9)
        base_target = 50 + t * 10
        variation = (level % 3) * 5  # 0, 5, or 10 percent variation
        return min(95, base_target + variation + (level - 1) * 5)

# Game states
STATE_PLAYING = 0
STATE_GAME_OVER = 1
STATE_HIGH_SCORE_ENTRY = 2
STATE_HIGH_SCORE_DISPLAY = 3
STATE_TUTORIAL = 4

# Difficulty settings
DIFFICULTY_EASY = 0
DIFFICULTY_NORMAL = 1
DIFFICULTY_HARD = 2

# Current game state
game_state = STATE_PLAYING
current_difficulty = DIFFICULTY_NORMAL

# Create score tracking
player_score = 0
level_bonuses = []

# Create assets directories if they don't exist
if not os.path.exists('assets/Images'):
    os.makedirs('assets/Images', exist_ok=True)
if not os.path.exists('assets/Sounds'):
    os.makedirs('assets/Sounds', exist_ok=True)
if not os.path.exists('assets/Music'):
    os.makedirs('assets/Music', exist_ok=True)

# Function to check if all required music files are present
def check_music_files():
    """Check if all required music files (01-10) are present in the Music directory"""
    music_dir = 'assets/Music'
    missing_tracks = []
    
    for i in range(1, 11):
        track_num = f"{i:02d}"
        track_found = False
        
        # Check if any file starts with the track number
        if os.path.exists(music_dir):
            for file in os.listdir(music_dir):
                if file.startswith(f"{track_num}_") and file.endswith('.mp3'):
                    track_found = True
                    break
        
        if not track_found:
            missing_tracks.append(i)
    
    if missing_tracks:
        print(f"Warning: Music files for tracks {missing_tracks} are missing from {music_dir}")
        print("The game will still run, but some levels will not have unique music.")
    else:
        print("All music tracks (1-10) are present.")
    
    return len(missing_tracks) == 0

# Function to load and play level-specific music
def load_level_music(level):
    """Load and play music based on the current level"""
    # For levels 1-10, play the corresponding track
    # For levels > 10, cycle through tracks 1-10
    music_level = ((level - 1) % 10) + 1
    
    # Format the track number with leading zero
    track_num = f"{music_level:02d}"
    
    # Get list of music files
    music_dir = 'assets/Music'
    try:
        music_files = [f for f in os.listdir(music_dir) if f.startswith(f"{track_num}_") and f.endswith('.mp3')]
        
        if music_files:
            music_path = os.path.join(music_dir, music_files[0])
            print(f"Loading music for level {level}: {music_path}")
            
            # Load and play the music
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.5)  # Set volume to 50%
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            return True
        else:
            print(f"No music file found for level {level} (track {track_num})")
            return False
    except (FileNotFoundError, pygame.error) as e:
        print(f"Error loading music for level {level}: {e}")
        return False

# Create sound effects placeholders if they don't exist
sound_files = {
    'level_complete': 'assets/Sounds/level_complete.wav',
    'game_over': 'assets/Sounds/game_over.wav',
    'high_score': 'assets/Sounds/high_score.wav',
    'button_click': 'assets/Sounds/button_click.wav',
    'connect': 'assets/Sounds/connect.wav',
    'disconnect': 'assets/Sounds/disconnect.wav',
    'evolve': 'assets/Sounds/evolve.wav',
    'error': 'assets/Sounds/error.wav'
}

# Create placeholder sounds
for sound_name, sound_path in sound_files.items():
    if not os.path.exists(sound_path):
        try:
            # Create a simple beep sound as placeholder
            import wave
            import struct

            # Parameters for the sound
            duration = 0.3  # seconds
            frequency = 440  # Hz (A4)
            volume = 0.5  # 0.0 to 1.0
            fs = 44100  # sampling rate, Hz

            # Adjust parameters based on sound type
            if sound_name == 'level_complete':
                frequency = 880  # Higher pitch for success
                duration = 0.5
            elif sound_name == 'game_over':
                frequency = 220  # Lower pitch for failure
                duration = 0.7
            elif sound_name == 'high_score':
                frequency = 660  # Happy sound
                duration = 0.6
            elif sound_name == 'button_click':
                frequency = 440
                duration = 0.1
            elif sound_name == 'connect':
                frequency = 550
                duration = 0.2
            elif sound_name == 'disconnect':
                frequency = 330
                duration = 0.2
            elif sound_name == 'evolve':
                frequency = 660
                duration = 0.4
            elif sound_name == 'error':
                frequency = 220
                duration = 0.3

            # Generate samples
            samples = []
            for i in range(int(duration * fs)):
                sample = volume * math.sin(2 * math.pi * frequency * i / fs)
                samples.append(struct.pack('h', int(sample * 32767)))

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(sound_path), exist_ok=True)

            # Write to file
            with wave.open(sound_path, 'w') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(fs)
                f.writeframes(b''.join(samples))

            print(f"Created placeholder sound: {sound_path}")
        except Exception as e:
            print(f"Could not create sound file {sound_path}: {e}")

# Load sounds
sounds = {}
for sound_name, sound_path in sound_files.items():
    try:
        sounds[sound_name] = pygame.mixer.Sound(sound_path)
    except pygame.error as e:
        print(f"Could not load sound {sound_path}: {e}")
        # Create a silent sound as fallback
        sounds[sound_name] = pygame.mixer.Sound(buffer=bytearray(44100))  # 1 second of silence

# Create a placeholder winning balance image if it doesn't exist
if not os.path.exists('assets/Images/winningBalance.jpg'):
    # Create a simple placeholder image
    placeholder = pygame.Surface((150, 150))
    placeholder.fill((200, 200, 255))
    pygame.draw.circle(placeholder, (255, 100, 100), (75, 75), 50)
    pygame.draw.circle(placeholder, (100, 100, 255), (75, 75), 50, 5)
    pygame.image.save(placeholder, 'assets/Images/winningBalance.jpg')

# Check music files at startup
check_music_files()

# Try to load level 1 music initially
try:
    if not load_level_music(1):
        # Fallback to a default music file if level-specific music fails
        pygame.mixer.music.load('assets/Sounds/01_beautiful_imperfection.mp3')
        pygame.mixer.music.set_volume(0.5)  # Set volume to 50%
        pygame.mixer.music.play(-1)  # -1 means loop indefinitely
except pygame.error as e:
    print(f"Could not load or play background music: {e}")

# Load the winning balance image
try:
    winning_balance_img = pygame.image.load('assets/Images/winningBalance.jpg')
    # Scale the image to 150x300
    winning_balance_img = pygame.transform.scale(winning_balance_img, (150, 300))
except pygame.error:
    # Create a fallback image if loading fails
    winning_balance_img = pygame.Surface((150, 300))
    winning_balance_img.fill((200, 200, 255))

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LOVE = (255, 141, 0)    # #FF8D00 - Orange for love
LOGIC = (1, 148, 220)   # #0194DC - Blue for logic
BALANCE = (151, 218, 167)  # #97DAA7 - Green for perfect balance
PURPLE = (128, 0, 128)
GRAY = (200, 200, 200)
GREEN = (0, 128, 0)
BACKGROUND = (255, 255, 255)  # Base white background
BACKGROUND_OVERLAY = (255, 150, 0, 50)  # Orange with 10% opacity (26 out of 255)

def draw_hint_box(surface, hint_text, score):
    """Draw a hint box at the bottom of the screen with hint text and score"""
    box_height = 60
    box_width = WIDTH - 20
    box_x = 10
    box_y = HEIGHT - box_height - 10

    # Draw box background
    pygame.draw.rect(surface, (240, 240, 240), (box_x, box_y, box_width, box_height))
    pygame.draw.rect(surface, BLACK, (box_x, box_y, box_width, box_height), 2)

    # Draw hint text on the left
    hint_font = pygame.font.SysFont('Arial', 14)
    hint_label = hint_font.render("Hint:", True, BLACK)
    hint_content = hint_font.render(hint_text, True, BLACK)
    surface.blit(hint_label, (box_x + 10, box_y + 10))
    surface.blit(hint_content, (box_x + 10, box_y + 30))

    # Draw score on the right
    score_font = pygame.font.SysFont('Arial', 18, bold=True)
    score_text = score_font.render(f"Score: {score:.1f}", True, PURPLE)
    surface.blit(score_text, (box_x + box_width - score_text.get_width() - 20, box_y + box_height//2 - score_text.get_height()//2))

# Fonts
font = pygame.font.SysFont('Arial', 12)  # Reduced from 14 to 12
title_font = pygame.font.SysFont('Arial', 24, bold=True)

# Create high scores directory if it doesn't exist
if not os.path.exists('high_scores'):
    os.makedirs('high_scores', exist_ok=True)

# High score file path
HIGH_SCORES_FILE = 'high_scores/scores.json'

# Initialize high scores
high_scores = []
if os.path.exists(HIGH_SCORES_FILE):
    try:
        with open(HIGH_SCORES_FILE, 'r') as f:
            high_scores = json.load(f)
    except json.JSONDecodeError:
        high_scores = []
else:
    # Create initial high scores file
    high_scores = [
        {"name": "AI", "score": 50.0, "level": 5, "date": datetime.datetime.now().strftime("%Y-%m-%d")},
        {"name": "BOT", "score": 30.0, "level": 3, "date": datetime.datetime.now().strftime("%Y-%m-%d")},
        {"name": "CPU", "score": 15.0, "level": 2, "date": datetime.datetime.now().strftime("%Y-%m-%d")}
    ]
    with open(HIGH_SCORES_FILE, 'w') as f:
        json.dump(high_scores, f)

def save_high_scores():
    """Save high scores to file"""
    with open(HIGH_SCORES_FILE, 'w') as f:
        json.dump(high_scores, f)

def check_high_score(score, level):
    """Check if score qualifies for high score and return position (0-based) or -1"""
    global high_scores

    # Sort high scores by score (descending)
    high_scores.sort(key=lambda x: x["score"], reverse=True)

    # Limit to top 10
    high_scores = high_scores[:10]

    # Check if score qualifies
    if len(high_scores) < 10 or score > high_scores[-1]["score"]:
        return True

    return False

def add_high_score(name, score, level):
    """Add a new high score"""
    global high_scores

    # Create new high score entry
    new_score = {
        "name": name,
        "score": score,
        "level": level,
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "is_current": True  # Mark as current player's score
    }

    # Remove is_current flag from all other scores
    for s in high_scores:
        if "is_current" in s:
            del s["is_current"]

    # Add to list
    high_scores.append(new_score)

    # Sort and trim
    high_scores.sort(key=lambda x: x["score"], reverse=True)
    high_scores = high_scores[:10]

    # Save to file
    save_high_scores()

    # Play high score sound
    sounds['high_score'].play()

# Create fractal structure
fractal = FractalStructure()

# Functions for game state management
def save_game_state():
    """Save the current game state for undo functionality"""
    global elements, fractal, player_score, level_bonuses

    # Create a copy of the current state
    state = {
        'elements_data': [],
        'connections': [],
        'level': fractal.level,
        'harmony_score': fractal.harmony_score,
        'player_score': player_score,
        'level_bonuses': level_bonuses.copy() if level_bonuses else []
    }

    # Save element data
    for i, e in enumerate(elements):
        element_data = {
            'x': e.x,
            'y': e.y,
            'size': e.size,
            'love_logic_ratio': e.love_logic_ratio,
            'level': e.level,
            'shape': e.shape,
            'structure_pattern': e.structure_pattern
        }
        state['elements_data'].append(element_data)

    # Save connections (as indices)
    for i, e in enumerate(elements):
        connections = []
        for c in e.connections:
            c_idx = elements.index(c)
            connections.append(c_idx)
        state['connections'].append(connections)

    return state

def restore_game_state(state):
    """Restore a previously saved game state"""
    global elements, fractal, player_score, level_bonuses

    # Restore elements
    new_elements = []
    for data in state['elements_data']:
        e = Element(data['x'], data['y'], size=data['size'],
                   love_logic_ratio=data['love_logic_ratio'],
                   level=data['level'], structure_pattern=data['structure_pattern'])
        e.shape = data['shape']
        new_elements.append(e)

    # Restore connections
    for i, connections in enumerate(state['connections']):
        for c_idx in connections:
            new_elements[i].connections.append(new_elements[c_idx])

    # Update elements list
    elements = new_elements

    # Restore fractal structure
    fractal.elements = elements
    fractal.level = state['level']
    fractal.harmony_score = state['harmony_score']

    # Restore scores
    player_score = state['player_score']
    level_bonuses = state['level_bonuses']

def restart_game():
    """Restart the game at level 1"""
    global elements, fractal, player_score, level_bonuses, game_state, tutorial_step, particles

    # Reset scores
    player_score = 0
    level_bonuses = []

    # Reset game state
    game_state = STATE_PLAYING
    tutorial_step = 0
    particles = []

    # Reset fractal structure
    fractal = FractalStructure()

    # Create initial element for level 1
    elements = [
        Element(WIDTH // 2, HEIGHT // 2, size=40, love_logic_ratio=0.5)
    ]

    for element in elements:
        fractal.add_element(element)

    # Play sound effect
    sounds['button_click'].play()
    
    # Reset music to level 1
    load_level_music(1)

    print("Game restarted at level 1")

def calculate_level_target_for_difficulty(level, difficulty):
    """Calculate the target harmony score for the current level based on difficulty"""
    # Base target calculation from FractalStructure
    if difficulty == DIFFICULTY_EASY:
        # Easier targets (30% start, slower progression)
        base_target = 30 + 15 * (1 - (1 / (level + 1)))
        variation = (level % 3) * 2  # 0, 2, or 4 percent variation
        return min(75, base_target + variation)
    elif difficulty == DIFFICULTY_NORMAL:
        # Normal targets (40% start, medium progression)
        base_target = 40 + 20 * (1 - (1 / (level + 0.5)))
        variation = (level % 3) * 3  # 0, 3, or 6 percent variation
        return min(85, base_target + variation)
    else:  # DIFFICULTY_HARD
        # Harder targets (50% start, faster progression)
        base_target = 50 + 25 * (1 - (1 / level))
        variation = (level % 3) * 5  # 0, 5, or 10 percent variation
        return min(95, base_target + variation)

def show_tutorial(screen, step=0):
    """Display tutorial information based on the current step"""
    # Tutorial content
    tutorial_steps = [
        {
            "title": "Welcome to Beautiful Imperfection",
            "text": [
                "This game is about finding harmony between love and logic.",
                "Create fractal structures by connecting elements and balancing",
                "forces.",
                "Press SPACE to continue to the next tutorial step."
            ]
        },
        {
            "title": "Basic Controls",
            "text": [
                "Click and drag elements to move them.",
                "Click one element then another to connect them.",
                "Use UP/DOWN arrows to adjust love/logic balance.",
                "Press SPACE to evolve elements to higher forms."
            ]
        },
        {
            "title": "Advanced Controls",
            "text": [
                "Press S to change an element's shape.",
                "Press C to create a child element.",
                "Press Z to undo your last action.",
                "Press M to toggle background music."
            ]
        },
        {
            "title": "Completing Levels",
            "text": [
                "Each level has a target harmony score to reach.",
                "The harmony meter shows your current score.",
                "When you reach the target, press COMPLETE to advance.",
                "Higher levels incorporate structures from previous levels."
            ]
        },
        {
            "title": "Game Philosophy",
            "text": [
                "Life is love or logic: Never both simultaneously,",
                "but a mix at any instance."
                "Steps for perfection: Proof then modify.",
                "Finding miracles in the ordinary: The crux isvdealing",
                "with the finer details.",
                "Press SPACE to start playing!"
            ]
        }
    ]

    # Ensure step is within bounds
    step = min(step, len(tutorial_steps) - 1)
    current_step = tutorial_steps[step]

    # Draw semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Black with 70% transparency
    screen.blit(overlay, (0, 0))

    # Draw tutorial box
    box_width, box_height = 600, 400
    box_x = WIDTH // 2 - box_width // 2
    box_y = HEIGHT // 2 - box_height // 2

    # Draw background
    pygame.draw.rect(screen, (240, 240, 240), (box_x, box_y, box_width, box_height))
    pygame.draw.rect(screen, (0, 0, 0), (box_x, box_y, box_width, box_height), 2)

    # Draw title
    title_font = pygame.font.SysFont('Arial', 28, bold=True)
    title_text = title_font.render(current_step["title"], True, (0, 0, 0))
    screen.blit(title_text, (box_x + box_width // 2 - title_text.get_width() // 2, box_y + 30))

    # Draw content
    content_font = pygame.font.SysFont('Arial', 18)
    y_offset = box_y + 80
    for line in current_step["text"]:
        text = content_font.render(line, True, (0, 0, 0))
        screen.blit(text, (box_x + 50, y_offset))
        y_offset += 30

    # Draw progress indicator
    progress_font = pygame.font.SysFont('Arial', 14)
    progress_text = progress_font.render(f"Step {step + 1} of {len(tutorial_steps)}", True, (100, 100, 100))
    screen.blit(progress_text, (box_x + box_width // 2 - progress_text.get_width() // 2, box_y + box_height - 50))

    # Draw continue instruction
    continue_font = pygame.font.SysFont('Arial', 16)
    continue_text = continue_font.render("Press SPACE to continue", True, (0, 0, 0))
    screen.blit(continue_text, (box_x + box_width // 2 - continue_text.get_width() // 2, box_y + box_height - 30))

    return step

def show_high_scores(screen):
    """Display the high scores screen"""
    # Draw semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Black with 70% transparency
    screen.blit(overlay, (0, 0))

    # Draw high scores box
    box_width, box_height = 600, 500
    box_x = WIDTH // 2 - box_width // 2
    box_y = HEIGHT // 2 - box_height // 2

    # Draw background
    pygame.draw.rect(screen, (240, 240, 240), (box_x, box_y, box_width, box_height))
    pygame.draw.rect(screen, (0, 0, 0), (box_x, box_y, box_width, box_height), 2)

    # Draw title
    title_font = pygame.font.SysFont('Arial', 32, bold=True)
    title_text = title_font.render("HIGH SCORES", True, (0, 0, 0))
    screen.blit(title_text, (box_x + box_width // 2 - title_text.get_width() // 2, box_y + 20))

    # Draw column headers
    header_font = pygame.font.SysFont('Arial', 18, bold=True)
    rank_text = header_font.render("Rank", True, (0, 0, 0))
    name_text = header_font.render("Name", True, (0, 0, 0))
    score_text = header_font.render("Score", True, (0, 0, 0))
    level_text = header_font.render("Level", True, (0, 0, 0))
    date_text = header_font.render("Date", True, (0, 0, 0))

    # Column positions
    rank_x = box_x + 30
    name_x = box_x + 100
    score_x = box_x + 250
    level_x = box_x + 350
    date_x = box_x + 420

    # Draw headers
    screen.blit(rank_text, (rank_x, box_y + 70))
    screen.blit(name_text, (name_x, box_y + 70))
    screen.blit(score_text, (score_x, box_y + 70))
    screen.blit(level_text, (level_x, box_y + 70))
    screen.blit(date_text, (date_x, box_y + 70))

    # Draw separator line
    pygame.draw.line(screen, (0, 0, 0), (box_x + 20, box_y + 95), (box_x + box_width - 20, box_y + 95), 2)

    # Sort high scores
    sorted_scores = sorted(high_scores, key=lambda x: x["score"], reverse=True)

    # Draw scores
    score_font = pygame.font.SysFont('Arial', 16)
    y_offset = box_y + 120
    for i, score in enumerate(sorted_scores[:10]):  # Show top 10
        # Highlight current player's score
        if i < len(sorted_scores) and "is_current" in score and score["is_current"]:
            pygame.draw.rect(screen, (255, 255, 200), (box_x + 20, y_offset - 5, box_width - 40, 30))

        # Draw rank
        rank_text = score_font.render(f"{i+1}", True, (0, 0, 0))
        screen.blit(rank_text, (rank_x, y_offset))

        # Draw name (truncate if too long)
        name = score["name"]
        if len(name) > 12:
            name = name[:10] + "..."
        name_text = score_font.render(name, True, (0, 0, 0))
        screen.blit(name_text, (name_x, y_offset))

        # Draw score
        score_text = score_font.render(f"{score['score']:.1f}", True, (0, 0, 0))
        screen.blit(score_text, (score_x, y_offset))

        # Draw level
        level_text = score_font.render(f"{score['level']}", True, (0, 0, 0))
        screen.blit(level_text, (level_x, y_offset))

        # Draw date
        date_text = score_font.render(f"{score['date']}", True, (0, 0, 0))
        screen.blit(date_text, (date_x, y_offset))

        y_offset += 30

    # Draw back instruction
    back_font = pygame.font.SysFont('Arial', 18)
    back_text = back_font.render("Press ESCAPE to exit", True, (0, 0, 0))
    screen.blit(back_text, (box_x + box_width // 2 - back_text.get_width() // 2, box_y + box_height - 40))

def create_particle_effect(x, y, color, count=20, speed=3, size_range=(2, 6), duration=30):
    """Create a particle effect at the given position"""
    particles = []
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed_val = random.uniform(1, speed)
        size = random.randint(size_range[0], size_range[1])
        life = random.randint(duration // 2, duration)
        particles.append({
            'x': x,
            'y': y,
            'dx': math.cos(angle) * speed_val,
            'dy': math.sin(angle) * speed_val,
            'size': size,
            'color': color,
            'life': life,
            'max_life': life
        })
    return particles

def update_particles(particles):
    """Update particle positions and lifetimes"""
    active_particles = []
    for p in particles:
        p['x'] += p['dx']
        p['y'] += p['dy']
        p['life'] -= 1

        # Keep particle if still alive
        if p['life'] > 0:
            active_particles.append(p)

    return active_particles

def draw_particles(surface, particles):
    """Draw particles on the surface"""
    for p in particles:
        # Calculate alpha based on remaining life
        alpha = int(255 * (p['life'] / p['max_life']))

        # Create a surface with per-pixel alpha
        s = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)

        # Draw the particle with alpha
        color_with_alpha = p['color'] + (alpha,)
        pygame.draw.circle(s, color_with_alpha, (p['size'], p['size']), p['size'])

        # Blit to main surface
        surface.blit(s, (int(p['x'] - p['size']), int(p['y'] - p['size'])))
def create_next_level():
    global elements, fractal, player_score, particles

    # Create a more comprehensive structure pattern that captures all properties
    structure_pattern = {
        'positions': [(e.x, e.y) for e in elements],
        'connections': [(elements.index(e),
                        [elements.index(c) for c in e.connections])
                        for e in elements],
        'colors': [e.color for e in elements],
        'shapes': [e.shape for e in elements],
        'levels': [e.level for e in elements],
        'love_logic_ratios': [e.love_logic_ratio for e in elements]
    }

    # Save the current level's image before advancing
    saved_file = fractal.save_image()
    print(f"Saved fractal image: {saved_file}")

    # Create level completion particles
    for e in elements:
        particles.extend(create_particle_effect(e.x, e.y, e.color, count=15, speed=2, size_range=(3, 8), duration=60))

    # Play level complete sound
    sounds['level_complete'].play()

    # Advance to the next level
    new_level = fractal.advance_level()
    
    # Load music for the new level
    load_level_music(new_level)

    # Clear elements list
    elements.clear()

    # Calculate the average size of elements in the previous level
    avg_size = sum(e.size for e in fractal.previous_structure['elements']) / len(fractal.previous_structure['elements'])

    # Find the maximum distance between any two elements in the previous level
    max_distance = 0
    for i, e1 in enumerate(fractal.previous_structure['elements']):
        for j, e2 in enumerate(fractal.previous_structure['elements']):
            if i != j:
                dist = math.sqrt((e1.x - e2.x)**2 + (e1.y - e2.y)**2)
                max_distance = max(max_distance, dist)

    # If there were no elements or just one, use a default distance
    if max_distance == 0:
        max_distance = 120

    # For level 2, create two elements with the previous level's structure
    if new_level == 2:
        # Use a fixed distance between elements
        fixed_distance = 120

        # Create two elements with the previous level's structure
        element1 = Element(WIDTH//2 - fixed_distance/2, HEIGHT//2, size=100,
                           love_logic_ratio=0.6, level=2, structure_pattern=structure_pattern)  # More love (greener)
        element2 = Element(WIDTH//2 + fixed_distance/2, HEIGHT//2, size=100,
                           love_logic_ratio=0.4, level=2, structure_pattern=structure_pattern)  # More logic (bluer)

        # Copy shapes from previous level if available
        if fractal.previous_structure and 'elements' in fractal.previous_structure and fractal.previous_structure['elements']:
            if len(fractal.previous_structure['elements']) >= 1:
                element1.shape = fractal.previous_structure['elements'][0].shape
            if len(fractal.previous_structure['elements']) >= 2:
                element2.shape = fractal.previous_structure['elements'][1].shape
            else:
                element2.shape = element1.shape  # Use the same shape if only one previous element

        # Add to elements list
        elements.append(element1)
        elements.append(element2)

        # Add to fractal structure
        fractal.add_element(element1)
        fractal.add_element(element2)

        # No initial connection between elements
        # Players will need to create their own connections
    else:
        # For higher levels, create elements with positioning influenced by love/logic spectrum

        # Get the average love/logic ratio from previous level
        love_logic_ratios = fractal.previous_structure.get('love_logic_ratios', [0.5])
        avg_love_logic = sum(love_logic_ratios) / len(love_logic_ratios)

        # Use fixed radius as base
        fixed_radius = 120

        # Calculate how "organic" the placement should be (0 = fully geometric, 1 = fully organic)
        if avg_love_logic < 0.333:
            organic_factor = 0  # Fully geometric
        elif avg_love_logic > 0.666:
            organic_factor = 1  # Fully organic
        else:
            # Linear interpolation between 33.3% and 66.6%
            organic_factor = (avg_love_logic - 0.333) / (0.666 - 0.333)

        # Get previous level positions
        prev_positions = [(e.x, e.y) for e in fractal.previous_structure['elements']]

        # Calculate center of previous positions
        if prev_positions:
            prev_center_x = sum(pos[0] for pos in prev_positions) / len(prev_positions)
            prev_center_y = sum(pos[1] for pos in prev_positions) / len(prev_positions)
        else:
            prev_center_x, prev_center_y = WIDTH // 2, HEIGHT // 2

        # Create elements based on the organic factor
        for i in range(new_level):
            # Geometric position (circular arrangement)
            geo_angle = 2 * math.pi * i / new_level
            geo_x = WIDTH // 2 + fixed_radius * math.cos(geo_angle)
            geo_y = HEIGHT // 2 + fixed_radius * math.sin(geo_angle)

            # Organic position (based on previous level's positions)
            if prev_positions:
                # Use modulo to cycle through previous positions if needed
                prev_idx = i % len(prev_positions)
                prev_pos = prev_positions[prev_idx]

                # Calculate vector from previous center to this position
                vector_x = prev_pos[0] - prev_center_x
                vector_y = prev_pos[1] - prev_center_y

                # Scale vector to maintain reasonable distances
                vector_length = math.sqrt(vector_x**2 + vector_y**2)
                if vector_length > 0:
                    scale_factor = fixed_radius / vector_length
                    vector_x *= scale_factor
                    vector_y *= scale_factor

                # Apply vector to new center
                org_x = WIDTH // 2 + vector_x
                org_y = HEIGHT // 2 + vector_y
            else:
                # Fallback if no previous positions
                org_x, org_y = geo_x, geo_y

            # Blend between geometric and organic positions based on organic factor
            x = geo_x * (1 - organic_factor) + org_x * organic_factor
            y = geo_y * (1 - organic_factor) + org_y * organic_factor

            # Create element with the previous structure pattern
            element_size = 100  # Consistent size for better visibility
            element = Element(x, y, size=element_size, level=new_level,
                             love_logic_ratio=0.5 + (i % 2) * 0.1 - (i % 2 == 0) * 0.1,
                             structure_pattern=structure_pattern)

            # Copy the shape from one of the previous level's elements if available
            # This ensures shape consistency across levels
            if fractal.previous_structure and 'elements' in fractal.previous_structure and fractal.previous_structure['elements']:
                # Use modulo to cycle through previous elements if there are fewer than current level
                prev_idx = i % len(fractal.previous_structure['elements'])
                element.shape = fractal.previous_structure['elements'][prev_idx].shape

            elements.append(element)
            fractal.add_element(element)

        # Print information about the placement approach
        print(f"Level {new_level} - Love/Logic Ratio: {avg_love_logic:.2f} - Organic Factor: {organic_factor:.2f}")

        # No initial connections between elements
        # Players will need to create their own connections

    return new_level

# Create complete button (moved to top right)
complete_button = Button(WIDTH - 150, 40, 120, 40, "COMPLETE", GREEN, (100, 200, 100))

# Create initial element for level 1 (just one element)
elements = [
    Element(WIDTH // 2, HEIGHT // 2, size=40, love_logic_ratio=0.5)
]

for element in elements:
    fractal.add_element(element)

# Initialize particles list
particles = []
def draw_dotted_line(surface, start_pos, end_pos, color, width=1, dash_length=10):
    """Draw a dotted line between two points"""
    x1, y1 = start_pos
    x2, y2 = end_pos

    # Calculate line length and angle
    dx = x2 - x1
    dy = y2 - y1
    distance = max(1, math.sqrt(dx*dx + dy*dy))

    # Normalize direction vector
    dx /= distance
    dy /= distance

    # Draw the dotted line
    pos = [x1, y1]
    dash_on = True
    drawn = 0

    while drawn < distance:
        # Calculate how much to draw in this segment
        segment_length = min(dash_length, distance - drawn)

        # Calculate end point of this segment
        end = [pos[0] + dx * segment_length, pos[1] + dy * segment_length]

        # Draw the segment if dash is on
        if dash_on:
            pygame.draw.line(surface, color, pos, end, width)

        # Update position and toggle dash state
        pos = end
        dash_on = not dash_on
        drawn += segment_length

# Function to adjust music based on harmony score
def adjust_music_to_harmony(harmony_score):
    """Adjust music volume based on harmony score"""
    # Scale volume between 0.3 (30%) and 1.0 (100%) based on harmony
    volume = 0.3 + (harmony_score / 100) * 0.7
    pygame.mixer.music.set_volume(volume)

# Main game loop
def main():
    global elements, fractal, player_score, level_bonuses, game_state, tutorial_step, particles, current_difficulty

    selected_element = None
    running = True
    clock = pygame.time.Clock()

    # Music control variables
    music_playing = True

    # Connection mode variables
    connection_mode = False
    connection_source = None

    # Restart confirmation
    restart_confirmation = False

    # Tutorial state
    tutorial_step = 0
    show_tutorial_mode = True  # Show tutorial on first run

    # High score entry
    high_score_name = ""

    # Game over reason
    game_over_reason = ""

    # Difficulty knob (moved below tutorial button)
    difficulty_knob = KnobControl(40, 430, 1, 10, 6, "Difficulty", size=60)

    # Tutorial button (moved below high scores button)
    tutorial_button = Button(10, 370, 120, 30, "TUTORIAL", (200, 200, 200), (150, 150, 150))

    # High scores button (moved below winning balance image)
    high_scores_button = Button(10, 320, 120, 40, "HIGH SCORES", (100, 100, 255), (150, 150, 255))

    # Undo history
    undo_history = []
    max_undo_history = 10  # Maximum number of states to remember

    # Start with tutorial if it's the first run
    if show_tutorial_mode:
        game_state = STATE_TUTORIAL

    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        mouse_clicked_processed = False  # Track if a click was processed

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state == STATE_HIGH_SCORE_DISPLAY or game_state == STATE_TUTORIAL:
                        game_state = STATE_PLAYING
                    else:
                        running = False

                # Handle high score name entry
                elif game_state == STATE_HIGH_SCORE_ENTRY:
                    if event.key == pygame.K_RETURN:
                        # Submit high score
                        if high_score_name.strip():
                            add_high_score(high_score_name, player_score, fractal.level)
                            game_state = STATE_HIGH_SCORE_DISPLAY
                        else:
                            # Don't allow empty names
                            pass
                    elif event.key == pygame.K_BACKSPACE:
                        high_score_name = high_score_name[:-1]
                    elif len(high_score_name) < 10:  # Limit name length
                        if event.unicode.isalnum() or event.unicode in [' ', '_', '-']:
                            high_score_name += event.unicode

                # Tutorial navigation
                elif game_state == STATE_TUTORIAL:
                    if event.key == pygame.K_SPACE:
                        tutorial_step += 1
                        sounds['button_click'].play()
                        if tutorial_step >= 5:  # Last step
                            game_state = STATE_PLAYING
                            tutorial_step = 0

                # Game over - restart on any key
                elif game_state == STATE_GAME_OVER:
                    if check_high_score(player_score, fractal.level):
                        game_state = STATE_HIGH_SCORE_ENTRY
                        high_score_name = ""
                    else:
                        restart_game()

                # Adjust love/logic ratio with up/down arrows
                elif game_state == STATE_PLAYING and selected_element:
                    if event.key == pygame.K_UP:
                        # Save state before making changes for undo
                        undo_history.append(save_game_state())
                        if len(undo_history) > max_undo_history:
                            undo_history.pop(0)  # Remove oldest state if we exceed max

                        selected_element.adjust_love_logic(0.05)  # More love
                        print(f"Adjusted love/logic ratio: {selected_element.love_logic_ratio:.2f}")
                        fractal.calculate_harmony()

                    elif event.key == pygame.K_DOWN:
                        # Save state before making changes for undo
                        undo_history.append(save_game_state())
                        if len(undo_history) > max_undo_history:
                            undo_history.pop(0)  # Remove oldest state if we exceed max

                        selected_element.adjust_love_logic(-0.05)  # More logic
                        print(f"Adjusted love/logic ratio: {selected_element.love_logic_ratio:.2f}")
                        fractal.calculate_harmony()

                    # Evolve element with space
                    elif event.key == pygame.K_SPACE:
                        # Save state before making changes for undo
                        undo_history.append(save_game_state())
                        if len(undo_history) > max_undo_history:
                            undo_history.pop(0)  # Remove oldest state if we exceed max

                        if selected_element.evolve():
                            fractal.calculate_harmony()
                            sounds['evolve'].play()
                            # Create particle effect for evolution
                            particles.extend(create_particle_effect(
                                selected_element.x, selected_element.y,
                                selected_element.color, count=10, speed=1.5,
                                size_range=(2, 5), duration=20
                            ))
                        else:
                            print(f"Element cannot evolve further (level {selected_element.level})")
                            sounds['error'].play()

                    # Change shape with S key
                    elif event.key == pygame.K_s:
                        # Save state before making changes for undo
                        undo_history.append(save_game_state())
                        if len(undo_history) > max_undo_history:
                            undo_history.pop(0)  # Remove oldest state if we exceed max

                        new_shape = selected_element.change_shape()
                        shape_names = ["Circle", "Square", "Star", "Hexagon", "Pentagon",
                                      "Triangle", "Diamond", "Cross", "Heart", "Crescent"]
                        print(f"Shape changed to {shape_names[new_shape]}")
                        sounds['button_click'].play()

                    # Create child element with C key
                    elif event.key == pygame.K_c:
                        # Save state before making changes for undo
                        undo_history.append(save_game_state())
                        if len(undo_history) > max_undo_history:
                            undo_history.pop(0)  # Remove oldest state if we exceed max

                        child = selected_element.create_child(elements)
                        fractal.add_element(child)
                        sounds['connect'].play()
                        # Create particle effect for child creation
                        particles.extend(create_particle_effect(
                            child.x, child.y,
                            child.color, count=8, speed=1,
                            size_range=(1, 3), duration=15
                        ))

                # Toggle music with M key
                elif event.key == pygame.K_m:
                    if music_playing:
                        pygame.mixer.music.pause()
                        music_playing = False
                        print("Music paused")
                    else:
                        pygame.mixer.music.unpause()
                        music_playing = True
                        print("Music resumed")
                        # If music was stopped (not just paused), reload the current level's music
                        if not pygame.mixer.music.get_busy():
                            load_level_music(fractal.level)

                # Restart game with R key
                elif event.key == pygame.K_r and game_state == STATE_PLAYING:
                    if not restart_confirmation:
                        restart_confirmation = True
                        print("Press R again to confirm restart. Any other key to cancel.")
                    else:
                        restart_game()
                        restart_confirmation = False
                        selected_element = None
                        # Clear undo history when restarting
                        undo_history = []

                # Undo last action with Z key
                elif event.key == pygame.K_z and game_state == STATE_PLAYING:
                    if undo_history:
                        restore_game_state(undo_history.pop())
                        print("Undo: Restored previous state")
                        sounds['button_click'].play()
                    else:
                        print("Nothing to undo")
                        sounds['error'].play()

                # Any other key cancels restart confirmation
                elif restart_confirmation:
                    restart_confirmation = False
                    print("Restart cancelled")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True

                # Don't process clicks if not in playing state
                if game_state != STATE_PLAYING:
                    continue

                # Update difficulty slider
                if game_state == STATE_PLAYING:
                    if difficulty_knob.update(mouse_pos, mouse_clicked):
                        # Play a sound effect when the knob is turned
                        sounds['button_click'].play()
                        print(f"Difficulty set to: {difficulty_knob.value:.1f}")

                        # Update target based on new difficulty
                        target = calculate_target_from_slider(fractal.level, difficulty_knob.value)
                        print(f"New target: {target:.1f}%")

                        # Create particles around the knob when turned
                        knob_center_x = difficulty_knob.x + difficulty_knob.size // 2
                        knob_center_y = difficulty_knob.y + difficulty_knob.size // 2

                        # Different particle effects based on difficulty level
                        if difficulty_knob.value <= 2:
                            # No Target mode - subtle gray particles
                            particles.extend(create_particle_effect(
                                knob_center_x, knob_center_y,
                                (150, 150, 150), count=5, speed=1,
                                size_range=(1, 3), duration=15
                            ))
                        elif difficulty_knob.value <= 4:
                            # Easy mode - green particles
                            particles.extend(create_particle_effect(
                                knob_center_x, knob_center_y,
                                (0, 150, 0), count=8, speed=1.5,
                                size_range=(2, 4), duration=20
                            ))
                        elif difficulty_knob.value <= 8:
                            # Normal mode - blue particles
                            particles.extend(create_particle_effect(
                                knob_center_x, knob_center_y,
                                (0, 0, 150), count=12, speed=2,
                                size_range=(2, 5), duration=25
                            ))
                        else:
                            # Hard mode - red particles
                            particles.extend(create_particle_effect(
                                knob_center_x, knob_center_y,
                                (150, 0, 0), count=15, speed=2.5,
                                size_range=(3, 6), duration=30
                            ))

                        # Play different sounds based on difficulty thresholds
                        if difficulty_knob.value <= 2:
                            # No Target mode - play a soft sound
                            sounds['button_click'].set_volume(0.3)
                            sounds['button_click'].play()
                        elif difficulty_knob.value <= 4:
                            # Easy mode - play a medium sound
                            sounds['button_click'].set_volume(0.5)
                            sounds['button_click'].play()
                        elif difficulty_knob.value <= 8:
                            # Normal mode - play a standard sound
                            sounds['button_click'].set_volume(0.7)
                            sounds['button_click'].play()
                        else:
                            # Hard mode - play an intense sound
                            sounds['button_click'].set_volume(1.0)
                            sounds['button_click'].play()

                        # Reset volume for future uses
                        sounds['button_click'].set_volume(0.7)

                # Check if tutorial button was clicked
                if tutorial_button.is_clicked(mouse_pos, mouse_clicked):
                    game_state = STATE_TUTORIAL
                    tutorial_step = 0
                    sounds['button_click'].play()
                    continue

                # Check if high scores button was clicked
                if high_scores_button.is_clicked(mouse_pos, mouse_clicked):
                    game_state = STATE_HIGH_SCORE_DISPLAY
                    sounds['button_click'].play()
                    continue

                # Check if an element was clicked
                clicked_on_element = False
                for element in elements:
                    if element.is_over(mouse_pos):
                        clicked_on_element = True

                        # If we already have a selected element and it's different from this one,
                        # create a connection between them
                        if selected_element and selected_element != element:
                            # Save state before making changes for undo
                            undo_history.append(save_game_state())
                            if len(undo_history) > max_undo_history:
                                undo_history.pop(0)  # Remove oldest state if we exceed max

                            # Check if they're already connected
                            if element not in selected_element.connections:
                                selected_element.connect_to(element)
                                print(f"Connected elements")
                                fractal.calculate_harmony()
                                sounds['connect'].play()
                                # Create particle effect for connection
                                mid_x = (selected_element.x + element.x) / 2
                                mid_y = (selected_element.y + element.y) / 2
                                particles.extend(create_particle_effect(
                                    mid_x, mid_y,
                                    PURPLE, count=5, speed=1,
                                    size_range=(2, 4), duration=15
                                ))
                            else:
                                # Remove connection if it already exists
                                selected_element.connections.remove(element)
                                element.connections.remove(selected_element)
                                print(f"Disconnected elements")
                                fractal.calculate_harmony()
                                sounds['disconnect'].play()

                        # Set this as the selected element
                        selected_element = element
                        element.start_drag()
                        break

                # If clicked on empty space, deselect current element
                if not clicked_on_element:
                    selected_element = None

            elif event.type == pygame.MOUSEBUTTONUP:
                # End dragging for all elements
                for element in elements:
                    element.end_drag()

        # Update particles
        particles = update_particles(particles)

        # Update elements if in playing state
        if game_state == STATE_PLAYING:
            for element in elements:
                element.update_position(mouse_pos)

        # Update buttons
        if game_state == STATE_PLAYING:
            difficulty_knob.update(mouse_pos, mouse_clicked and not mouse_clicked_processed)
        tutorial_button.update(mouse_pos)
        high_scores_button.update(mouse_pos)
        complete_button.update(mouse_pos)

        # Check if complete button was clicked
        if game_state == STATE_PLAYING and complete_button.is_clicked(mouse_pos, mouse_clicked):
            # Check if target has been reached or if there is no target
            target = calculate_target_from_slider(fractal.level, difficulty_knob.value)
            if fractal.level == 1 or difficulty_knob.value <= 1 or fractal.harmony_score >= target:
                # Save image of current level
                saved_file = fractal.save_image()
                print(f"Saved fractal image: {saved_file}")

                # Add bonus points or rewards for exceeding target
                # No bonus if there's no target
                if fractal.level == 1 or difficulty_knob.value <= 1:
                    bonus = 0
                # Higher bonus multiplier for levels greater than 7
                elif fractal.level > 7:
                    bonus = (fractal.harmony_score - target) / 2.5  # 1 point for every 2.5% above target for higher levels
                else:
                    bonus = (fractal.harmony_score - target) / 5  # 1 point for every 5% above target for lower levels

                player_score += bonus
                level_bonuses.append(bonus)
                
                if fractal.level == 1 or difficulty_knob.value <= 1:
                    print(f"Level {fractal.level} complete! No target required. Achieved: {fractal.harmony_score:.1f}%, Total Score: {player_score:.1f}")
                else:
                    print(f"Level {fractal.level} complete! Target: {target:.1f}%, Achieved: {fractal.harmony_score:.1f}%, Bonus: {bonus:.1f}, Total Score: {player_score:.1f}")

                # Advance to next level
                create_next_level()
                selected_element = None
            else:
                # Game over when target hasn't been reached
                game_state = STATE_GAME_OVER
                game_over_reason = f"Target harmony of {target:.1f}% not reached. Current: {fractal.harmony_score:.1f}%"
                print(f"Game Over: {game_over_reason}")
                sounds['game_over'].play()

        # Adjust music volume based on harmony score
        adjust_music_to_harmony(fractal.harmony_score)

        # Draw everything
        screen.fill(BACKGROUND)  # Fill with base white background

        # Create a semi-transparent orange overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(BACKGROUND_OVERLAY)  # Orange with 10% opacity
        screen.blit(overlay, (0, 0))

        # Draw winning balance image in the upper left corner
        screen.blit(winning_balance_img, (10, 10))

        # Draw elements
        for element in elements:
            element.draw(screen)

        # Draw particles
        draw_particles(screen, particles)

        # Draw selection indicator and show love/logic ratio if an element is selected
        if selected_element and game_state == STATE_PLAYING:
            # Draw a thicker purple circle around the selected element
            pygame.draw.circle(screen, PURPLE, (selected_element.x, selected_element.y),
                              selected_element.size//2 + 5, 2)

            # Display the love/logic ratio of the selected element
            love_percent = int(selected_element.love_logic_ratio * 100)
            logic_percent = 100 - love_percent
            ratio_text = font.render(f"Love: {love_percent}% | Logic: {logic_percent}%", True, BLACK)
            screen.blit(ratio_text, (WIDTH // 2, 30))

            # Draw connection hint for all other elements
            for element in elements:
                if element != selected_element:
                    # Draw a dotted line to show potential connection
                    if element not in selected_element.connections:
                        # Draw dotted line to show potential connection
                        draw_dotted_line(screen, (selected_element.x, selected_element.y),
                                        (element.x, element.y), (100, 100, 100), 2, 5)

                    # Draw a small indicator around elements that can be connected to
                    pygame.draw.circle(screen, (100, 100, 100), (element.x, element.y),
                                      element.size//2 + 3, 1)

        # Calculate target based on difficulty knob
        target = calculate_target_from_slider(fractal.level, difficulty_knob.value)
        
        # Always set target to 0 for level 1
        if fractal.level == 1:
            target = 0

        # Draw a more prominent target box at the top
        target_box_width = 300
        target_box_height = 70
        target_box_x = WIDTH // 2 - target_box_width // 2
        target_box_y = 20

        # Draw target box background
        pygame.draw.rect(screen, (240, 240, 240), (target_box_x, target_box_y, target_box_width, target_box_height))
        pygame.draw.rect(screen, BLACK, (target_box_x, target_box_y, target_box_width, target_box_height), 2)

        # Draw level and target information
        level_font = pygame.font.SysFont('Arial', 18, bold=True)
        level_text = level_font.render(
            f"Level {fractal.level}", True, BLACK)
        screen.blit(level_text, (target_box_x + 10, target_box_y + 10))

        # Draw target percentage
        target_font = pygame.font.SysFont('Arial', 12)
        if fractal.level == 1 or difficulty_knob.value <= 1:
            target_text = target_font.render("No Target", True, (100, 100, 100))
        else:
            target_text = target_font.render(f"Target: {target:.1f}%", True, (255, 0, 0))
        screen.blit(target_text, (target_box_x + target_box_width - 100, target_box_y + 10))

        # Draw current harmony
        harmony_text = target_font.render(f"Current: {fractal.harmony_score:.1f}%", True, (0, 0, 255))
        screen.blit(harmony_text, (target_box_x +
                    target_box_width - 100, target_box_y + 30))

        # Draw progress bar inside the target box
        progress_width = target_box_width - 20
        progress_height = 10
        progress_x = target_box_x + 10
        progress_y = target_box_y + target_box_height - 23

        # Draw background bar
        pygame.draw.rect(screen, GRAY, (progress_x, progress_y, progress_width, progress_height))

        # Draw filled portion based on harmony score
        fill_width = int(progress_width * (fractal.harmony_score / 100))
        fill_width = max(0, min(progress_width, fill_width))

        # Calculate target marker position (only if there is a target)
        if (fractal.level > 1 and difficulty_knob.value > 1) and target > 0:
            target_marker_x = progress_x + int(progress_width * (target / 100))
            target_marker_x = max(progress_x, min(progress_x + progress_width, target_marker_x))
        else:
            # No target, set marker off-screen
            target_marker_x = -10

        # Color gradient based on harmony score
        if fractal.harmony_score < 33:
            color = (255, int(fractal.harmony_score / 33 * 165), 0)
        elif fractal.harmony_score < 66:
            color = (int(255 - (fractal.harmony_score - 33) / 33 * 155),
                    int(165 + (fractal.harmony_score - 33) / 33 * 90),
                    int((fractal.harmony_score - 33) / 33 * 167))
        else:
            color = (int(100 + (fractal.harmony_score - 66) / 34 * 55),
                    int(255 - (fractal.harmony_score - 66) / 34 * 55),
                    int(167 + (fractal.harmony_score - 66) / 34 * 88))

        # Draw filled portion if there's any harmony
        if fill_width > 0:
            pygame.draw.rect(screen, color, (progress_x, progress_y, fill_width, progress_height))

        # Draw target marker (only if there is a target)
        if fractal.level > 1 and difficulty_knob.value > 1:
            pygame.draw.line(screen, (255, 0, 0), (target_marker_x, progress_y - 2),
                            (target_marker_x, progress_y + progress_height + 2), 2)

        # Draw complete button next to target box
        complete_button.draw(screen)

        # Draw hint box at the bottom with hint and score
        hint = fractal.get_strategic_hint()
        draw_hint_box(screen, hint, player_score)

        # Draw high scores button
        high_scores_button.draw(screen)

        # Draw tutorial button
        tutorial_button.draw(screen)

        # Draw difficulty knob
        difficulty_knob.draw(screen)

        # Remove instructions section (as requested)
        # Draw score
        score_text = title_font.render(f"Score: {player_score:.1f}", True, PURPLE)
        # Score is now displayed in the hint box
        # screen.blit(score_text, (WIDTH - 150, HEIGHT - 100))

        # Draw game over screen if game is over
        if game_state == STATE_GAME_OVER:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
            screen.blit(overlay, (0, 0))

            # Draw game over message
            game_over_font = pygame.font.SysFont('Arial', 48, bold=True)
            game_over_text = game_over_font.render("GAME OVER", True, (255, 0, 0))
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 100))

            # Draw reason
            reason_font = pygame.font.SysFont('Arial', 24)
            reason_text = reason_font.render(game_over_reason, True, WHITE)
            screen.blit(reason_text, (WIDTH//2 - reason_text.get_width()//2, HEIGHT//2 - 40))

            # Draw final score
            final_score_font = pygame.font.SysFont('Arial', 36)
            final_score_text = final_score_font.render(f"Final Score: {player_score:.1f}", True, (255, 255, 0))
            screen.blit(final_score_text, (WIDTH//2 - final_score_text.get_width()//2, HEIGHT//2 + 20))

            # Draw level reached
            level_font = pygame.font.SysFont('Arial', 24)
            level_text = level_font.render(f"Level Reached: {fractal.level}", True, WHITE)
            screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, HEIGHT//2 + 70))

            # Draw continue message
            continue_font = pygame.font.SysFont('Arial', 18)
            continue_text = continue_font.render("Press any key to continue", True, WHITE)
            screen.blit(continue_text, (WIDTH//2 - continue_text.get_width()//2, HEIGHT//2 + 120))

        # Draw high score entry screen
        elif game_state == STATE_HIGH_SCORE_ENTRY:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
            screen.blit(overlay, (0, 0))

            # Draw high score message
            hs_font = pygame.font.SysFont('Arial', 36, bold=True)
            hs_text = hs_font.render("NEW HIGH SCORE!", True, (255, 215, 0))  # Gold color
            screen.blit(hs_text, (WIDTH//2 - hs_text.get_width()//2, HEIGHT//2 - 100))

            # Draw score
            score_font = pygame.font.SysFont('Arial', 24)
            score_text = score_font.render(f"Score: {player_score:.1f}", True, WHITE)
            screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 - 50))

            # Draw name entry field
            name_font = pygame.font.SysFont('Arial', 24)
            name_prompt = name_font.render("Enter your name:", True, WHITE)
            screen.blit(name_prompt, (WIDTH//2 - name_prompt.get_width()//2, HEIGHT//2))

            # Draw name input box
            name_box_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 40, 300, 40)
            pygame.draw.rect(screen, WHITE, name_box_rect)
            pygame.draw.rect(screen, BLACK, name_box_rect, 2)

            # Draw entered name
            name_text = name_font.render(high_score_name + "|", True, BLACK)
            screen.blit(name_text, (name_box_rect.x + 10, name_box_rect.y + 5))

            # Draw submit instruction
            submit_font = pygame.font.SysFont('Arial', 18)
            submit_text = submit_font.render("Press ENTER to submit", True, WHITE)
            screen.blit(submit_text, (WIDTH//2 - submit_text.get_width()//2, HEIGHT//2 + 100))

        # Draw high scores screen
        elif game_state == STATE_HIGH_SCORE_DISPLAY:
            show_high_scores(screen)

        # Draw tutorial screen
        elif game_state == STATE_TUTORIAL:
            tutorial_step = show_tutorial(screen, tutorial_step)

        # Draw restart confirmation if active
        if restart_confirmation and game_state == STATE_PLAYING:
            # Draw confirmation dialog
            dialog_width, dialog_height = 300, 100
            dialog_x = WIDTH // 2 - dialog_width // 2
            dialog_y = HEIGHT // 2 - dialog_height // 2

            # Draw background
            pygame.draw.rect(screen, (240, 240, 240), (dialog_x, dialog_y, dialog_width, dialog_height))
            pygame.draw.rect(screen, BLACK, (dialog_x, dialog_y, dialog_width, dialog_height), 2)

            # Draw text
            confirm_font = pygame.font.SysFont('Arial', 16)
            confirm_text1 = confirm_font.render("Are you sure you want to restart?", True, BLACK)
            confirm_text2 = confirm_font.render("Press R again to confirm, any other key to cancel", True, BLACK)

            screen.blit(confirm_text1, (dialog_x + dialog_width//2 - confirm_text1.get_width()//2, dialog_y + 30))
            screen.blit(confirm_text2, (dialog_x + dialog_width//2 - confirm_text2.get_width()//2, dialog_y + 60))

        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

# Run the game
if __name__ == "__main__":
    main()
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.active = False
        self.handle_radius = height * 1.5
        self.handle_color = (100, 100, 255)
        self.handle_hover_color = (150, 150, 255)
        self.track_color = (200, 200, 200)
        self.track_active_color = (150, 150, 200)
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', 12)

        # Calculate handle position
        self.handle_pos = self.get_handle_pos()

    def get_handle_pos(self):
        # Convert value to position
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + int(ratio * self.rect.width)

    def get_value_at_pos(self, x_pos):
        # Convert position to value
        ratio = max(0, min(1, (x_pos - self.rect.x) / self.rect.width))
        return self.min_val + ratio * (self.max_val - self.min_val)

    def update(self, mouse_pos, mouse_pressed):
        x, y = mouse_pos

        # Check if mouse is over handle
        handle_rect = pygame.Rect(
            self.handle_pos - self.handle_radius,
            self.rect.centery - self.handle_radius,
            self.handle_radius * 2,
            self.handle_radius * 2
        )
        self.is_hovered = handle_rect.collidepoint(x, y)

        # Update active state
        if mouse_pressed and self.is_hovered:
            self.active = True
        elif not mouse_pressed:
            self.active = False

        # Update value if active
        if self.active:
            self.value = self.get_value_at_pos(x)
            self.value = max(self.min_val, min(self.max_val, self.value))
            self.handle_pos = self.get_handle_pos()
            return True  # Value changed

        return False  # Value unchanged

    def draw(self, surface):
        # Draw track
        track_color = self.track_active_color if self.active else self.track_color
        pygame.draw.rect(surface, track_color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 1)  # Border

        # Draw handle
        handle_color = self.handle_hover_color if self.is_hovered or self.active else self.handle_color
        pygame.draw.circle(surface, handle_color, (self.handle_pos, self.rect.centery), self.handle_radius)
        pygame.draw.circle(surface, (0, 0, 0), (self.handle_pos, self.rect.centery), self.handle_radius, 1)  # Border

        # Draw label
        if self.label:
            label_text = self.font.render(self.label, True, (0, 0, 0))
            surface.blit(label_text, (self.rect.x, self.rect.y - 20))

        # Draw value
        value_text = self.font.render(f"{int(self.value)}", True, (0, 0, 0))
        surface.blit(value_text, (self.handle_pos - value_text.get_width() // 2, self.rect.centery + self.handle_radius + 5))

        # Draw difficulty labels
        if self.min_val == 1 and self.max_val == 10:  # Only for difficulty slider
            # No target
            if self.value <= 2:
                diff_text = self.font.render("No Target", True, (100, 100, 100))
            # Easy
            elif self.value <= 4:
                diff_text = self.font.render("Easy", True, (0, 150, 0))
            # Normal
            elif self.value <= 8:
                diff_text = self.font.render("Normal", True, (0, 0, 150))
            # Hard
            else:
                diff_text = self.font.render("Hard", True, (150, 0, 0))

            surface.blit(diff_text, (self.rect.x + self.rect.width + 10, self.rect.centery - diff_text.get_height() // 2))

def calculate_target_from_slider(level, difficulty_value):
    """Calculate target harmony based on difficulty slider value (1-10)"""
    # At difficulty 1, no target (0%)
    if difficulty_value <= 1:
        return 0

    # At difficulty 2-4 (easy): 30-40% base
    elif difficulty_value <= 4:
        # Map 2-4 to 0-1
        t = (difficulty_value - 2) / 2
        base_target = 30 + t * 10
        variation = (level % 3) * 2  # 0, 2, or 4 percent variation
        return min(75, base_target + variation + (level - 1) * 3)

    # At difficulty 5-8 (normal): 40-50% base
    elif difficulty_value <= 8:
        # Map 5-8 to 0-1
        t = (difficulty_value - 5) / 3
        base_target = 40 + t * 10
        variation = (level % 3) * 3  # 0, 3, or 6 percent variation
        return min(85, base_target + variation + (level - 1) * 4)

    # At difficulty 9-10 (hard): 50-60% base
    else:
        # Map 9-10 to 0-1
        t = (difficulty_value - 9)
        base_target = 50 + t * 10
        variation = (level % 3) * 5  # 0, 5, or 10 percent variation
        return min(95, base_target + variation + (level - 1) * 5)
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.active = False
        self.handle_radius = height * 1.5
        self.handle_color = (100, 100, 255)
        self.handle_hover_color = (150, 150, 255)
        self.track_color = (200, 200, 200)
        self.track_active_color = (150, 150, 200)
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', 12)

        # Calculate handle position
        self.handle_pos = self.get_handle_pos()

    def get_handle_pos(self):
        # Convert value to position
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + int(ratio * self.rect.width)

    def get_value_at_pos(self, x_pos):
        # Convert position to value
        ratio = max(0, min(1, (x_pos - self.rect.x) / self.rect.width))
        return self.min_val + ratio * (self.max_val - self.min_val)

    def update(self, mouse_pos, mouse_pressed):
        x, y = mouse_pos

        # Check if mouse is over handle
        handle_rect = pygame.Rect(
            self.handle_pos - self.handle_radius,
            self.rect.centery - self.handle_radius,
            self.handle_radius * 2,
            self.handle_radius * 2
        )
        self.is_hovered = handle_rect.collidepoint(x, y)

        # Update active state
        if mouse_pressed and self.is_hovered:
            self.active = True
        elif not mouse_pressed:
            self.active = False

        # Update value if active
        if self.active:
            self.value = self.get_value_at_pos(x)
            self.value = max(self.min_val, min(self.max_val, self.value))
            self.handle_pos = self.get_handle_pos()
            return True  # Value changed

        return False  # Value unchanged

    def draw(self, surface):
        # Draw track
        track_color = self.track_active_color if self.active else self.track_color
        pygame.draw.rect(surface, track_color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 1)  # Border

        # Draw handle
        handle_color = self.handle_hover_color if self.is_hovered or self.active else self.handle_color
        pygame.draw.circle(surface, handle_color, (self.handle_pos, self.rect.centery), self.handle_radius)
        pygame.draw.circle(surface, (0, 0, 0), (self.handle_pos, self.rect.centery), self.handle_radius, 1)  # Border

        # Draw label
        if self.label:
            label_text = self.font.render(self.label, True, (0, 0, 0))
            surface.blit(label_text, (self.rect.x, self.rect.y - 20))

        # Draw value
        value_text = self.font.render(f"{int(self.value)}", True, (0, 0, 0))
        surface.blit(value_text, (self.handle_pos - value_text.get_width() // 2, self.rect.centery + self.handle_radius + 5))

        # Draw difficulty labels
        if self.min_val == 1 and self.max_val == 10:  # Only for difficulty slider
            # No target
            if self.value <= 2:
                diff_text = self.font.render("No Target", True, (100, 100, 100))
            # Easy
            elif self.value <= 4:
                diff_text = self.font.render("Easy", True, (0, 150, 0))
            # Normal
            elif self.value <= 8:
                diff_text = self.font.render("Normal", True, (0, 0, 150))
            # Hard
            else:
                diff_text = self.font.render("Hard", True, (150, 0, 0))

            surface.blit(diff_text, (self.rect.x + self.rect.width + 10, self.rect.centery - diff_text.get_height() // 2))

def calculate_target_from_slider(level, difficulty_value):
    """Calculate target harmony based on difficulty slider value (1-10)"""
    # At difficulty 1, no target (0%)
    if difficulty_value <= 1:
        return 0

    # At difficulty 2-4 (easy): 30-40% base
    elif difficulty_value <= 4:
        # Map 2-4 to 0-1
        t = (difficulty_value - 2) / 2
        base_target = 30 + t * 10
        variation = (level % 3) * 2  # 0, 2, or 4 percent variation
        return min(75, base_target + variation + (level - 1) * 3)

    # At difficulty 5-8 (normal): 40-50% base
    elif difficulty_value <= 8:
        # Map 5-8 to 0-1
        t = (difficulty_value - 5) / 3
        base_target = 40 + t * 10
        variation = (level % 3) * 3  # 0, 3, or 6 percent variation
        return min(85, base_target + variation + (level - 1) * 4)

    # At difficulty 9-10 (hard): 50-60% base
    else:
        # Map 9-10 to 0-1
        t = (difficulty_value - 9)
        base_target = 50 + t * 10
        variation = (level % 3) * 5  # 0, 5, or 10 percent variation
        return min(95, base_target + variation + (level - 1) * 5)
