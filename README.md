Trackball Arcade System - ROM Development Guide
Professional arcade game engine with dynamic ROM loading
Build playable arcade games in minutes with Python + Pygame

Table of Contents
Quick Start

MiniGame API Reference

TrackballInput API

SoundSynthesizer API

Engine Lifecycle

Drawing Guidelines

Best Practices

Testing & Debugging

Quick Start
Minimal ROM Template
Create roms/YourGame.py:

python
import pygame
import math
import random

class YourGame(MiniGame):
    def __init__(self, *args, sound=None, **kwargs):
        super().__init__("Your Game", "Game description", *args, **kwargs)
        self.sound = sound
        self.reset()

    def reset(self):
        self.score = 0
        self.is_game_over = False
        self.is_paused = False

    def update(self, dt, trackball):
        if self.is_paused or self.is_game_over:
            return

    def draw(self, surface):
        surface.fill((0, 0, 0))
That's it. The engine handles menus, high scores, pause, game over, music, and display scaling.

MiniGame API Reference
Required Methods
__init__(self, *args, sound=None, **kwargs)
Purpose: Initialize your game instance
Parameters:

*args, **kwargs: Pass to parent (required)

sound: SoundSynthesizer instance (save to self.sound)

Example:

python
def __init__(self, *args, sound=None, **kwargs):
    super().__init__("Pong", "First to 5 wins!", *args, **kwargs)
    self.sound = sound
    self.paddle_speed = 480
    self.reset()
reset(self)
Purpose: Reset game state for new game/retry
Called: On game start, after game over retry
Must initialize:

self.score = 0

self.is_game_over = False

self.is_paused = False

All game-specific variables

Example:

python
def reset(self):
    self.score = 0
    self.is_game_over = False
    self.is_paused = False
    
    self.ball_x = 640
    self.ball_y = 360
    self.ball_vx = 300 * random.choice([-1, 1])
    
    if self.sound:
        self.sound.create_game_start().play()
update(self, dt: float, trackball: TrackballInput)
Purpose: Game logic at 60 FPS
Parameters:

dt: Delta time in seconds (≈ 0.016 at 60 FPS)

trackball: Input state object

Rules:

Always check if self.is_paused or self.is_game_over: return first

Update self.score continuously

Set self.is_game_over = True when game finishes

Use dt for frame-rate independent movement: position += velocity * dt

Example:

python
def update(self, dt, trackball):
    if self.is_paused or self.is_game_over:
        return
    
    # Player movement
    dx, dy = trackball.get_smooth_delta()
    self.player_x += dx * 500 * dt  # 500 pixels/sec max
    
    # Fire on button press (edge-triggered)
    if trackball.button_left_pressed:
        self.bullets.append({'x': self.player_x, 'y': 650})
        self.sound.create_shoot().play()
    
    # Update bullets
    for b in self.bullets[:]:
        b['y'] -= 400 * dt
        if b['y'] < 0:
            self.bullets.remove(b)
    
    # Win condition
    if self.score >= 5000:
        self.is_game_over = True
        self.score += 10000  # Completion bonus
draw(self, surface: pygame.Surface)
Purpose: Render frame to 1280x720 virtual display
Parameters:

surface: Target pygame.Surface(1280, 720) - write only, engine scales automatically

Rules:

Never call pygame.display.flip() or .update()

Use temp surfaces for effects: temp = pygame.Surface((1280, 720))

Draw pause overlay if self.is_paused (optional)

Do NOT draw game over screen (engine handles)

Example:

python
def draw(self, surface):
    surface.fill((10, 10, 30))  # Background
    
    # Player
    pygame.draw.circle(surface, (0, 255, 120), 
                      (int(self.player_x), 650), 20)
    
    # Bullets
    for b in self.bullets:
        pygame.draw.rect(surface, (255, 255, 0), 
                        (b['x']-2, b['y']-8, 4, 16))
    
    # Score
    font = pygame.font.Font(None, 64)
    score_text = font.render(str(self.score), True, (255, 255, 255))
    surface.blit(score_text, (50, 50))
    
    # Optional pause overlay
    if self.is_paused:
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        pause_text = font.render("PAUSED", True, (255, 255, 255))
        surface.blit(pause_text, (540, 340))
Engine-Controlled Flags
Variable	Type	You Set	Engine Reads	Purpose
self.score	int	✅ Continuously	✅ On game over	High score comparison
self.is_game_over	bool	✅ Once (True)	✅ Every frame	Triggers game over screen
self.is_paused	bool	✅ Optional	✅ Skips update	Local pause overlay
Critical: Once self.is_game_over = True, engine takes control. Do NOT draw game over screens.

TrackballInput API
Access via trackball parameter in update().

Movement Methods
python
# Smoothed trackball delta (RECOMMENDED for gameplay)
dx, dy = trackball.get_smooth_delta()
# Returns: (float, float) pixels moved since last frame
# Smoothed with exponential filter (smooth_factor = 0.3)

# Raw delta (for instant response)
dx, dy = trackball.get_delta()
# Returns: (float, float) raw mouse relative motion

# Velocity vector
vx, vy = trackball.get_velocity()
# Returns: (float, float) speed with direction
# Returns (0, 0) if speed < dead_zone
Example - Paddle Control:

python
dx, dy = trackball.get_smooth_delta()
self.paddle_y += dy * 400 * dt  # 400 px/sec sensitivity
self.paddle_y = max(50, min(670, self.paddle_y))  # Clamp
Button States
Edge-Triggered (Single Click)
python
trackball.button_left_pressed    # bool: True on press frame only
trackball.button_middle_pressed  # bool: Middle button press
trackball.button_right_pressed   # bool: Right button press
Example - Shooting:

python
if trackball.button_left_pressed:
    self.spawn_bullet()
    self.sound.create_shoot().play()
Continuous States
python
trackball.button_left      # bool: True while held down
trackball.button_middle    # bool: Middle button held
trackball.button_right     # bool: Right button held
Example - Auto-Fire:

python
if trackball.button_left:  # Held
    self.fire_timer += dt
    if self.fire_timer > 0.2:  # 5 shots/sec
        self.spawn_bullet()
        self.fire_timer = 0
Advanced Properties
python
trackball.speed           # float: Current movement magnitude
trackball.angle          # float: Movement direction in radians
trackball.sensitivity    # float: 10-200 (user configured)
Example - Aim Direction:

python
vx, vy = trackball.get_velocity()
if vx != 0 or vy != 0:
    aim_angle = math.atan2(vy, vx)
    self.turret_rotation = aim_angle
SoundSynthesizer API
Access via self.sound (set in __init__).

Available Sounds
python
# Game lifecycle (play once per event)
self.sound.create_game_start().play()   # Startup fanfare (C-E-G-C)
self.sound.create_game_over().play()    # NOT NEEDED - engine plays automatically

# Gameplay events
self.sound.create_shoot().play()        # Laser shot (1200→300 Hz sweep)
self.sound.create_target_hit().play()   # Impact/collision (880 Hz + harmonics)
self.sound.create_target_miss().play()  # Miss/error (200 Hz sawtooth)

# UI/Menu (engine uses these, optional for gameplay)
self.sound.create_pause().play()        # Pause menu toggle
self.sound.create_blip(pitch).play()    # UI beep (pitch: -12 to +12 semitones)

# Score feedback
self.sound.create_combo(level).play()   # Combo/streak (level: 1-9, higher = higher pitch)
self.sound.create_powerup().play()      # Bonus item collected
self.sound.create_high_score().play()   # NOT NEEDED - engine plays automatically
Usage Patterns
On Collision:

python
if player_hit_enemy():
    self.score += 100
    self.sound.create_target_hit().play()
On Miss:

python
if bullet_missed():
    self.sound.create_target_miss().play()
Combo System:

python
self.combo_count += 1
if self.combo_count % 5 == 0:
    self.sound.create_combo(min(self.combo_count // 5, 9)).play()
Engine Lifecycle
Game Flow
text
[MENU] → Select ROM → [PLAYING] → Game Over → [GAME_OVER SCREEN]
   ↑                       ↓                          ↓
   └─────────── ESC ←──────┴──── Retry/Back ←────────┘
Your ROM's Lifecycle
Load: __init__() called once when ROM detected

Start: User selects game → reset() called

Loop: update(dt, trackball) + draw(surface) at 60 FPS

Pause: Middle button → update() skipped, draw() still called

End: self.is_game_over = True → engine shows game over screen

Retry: User presses retry → reset() called again

What Engine Handles
✅ Main menu carousel navigation

✅ High score detection and entry (initials input)

✅ Game over screen rendering

✅ Pause menu (settings/exit)

✅ Display scaling (1280x720 → any resolution)

✅ Music playback (MP3/OGG in music/ folder)

✅ Config persistence (sensitivity, volumes)

What You Handle
✅ Game logic in update()

✅ Graphics in draw()

✅ Setting self.score and self.is_game_over

✅ Sound effects during gameplay

✅ Optional pause overlay rendering

Drawing Guidelines
Canvas Specifications
Resolution: 1280 × 720 pixels (virtual, engine scales to actual screen)

Coordinate system: (0,0) = top-left, (1280, 720) = bottom-right

Safe area: 100px margin recommended for UI elements

Performance Tips
Use Temp Surfaces for Effects:

python
def draw(self, surface):
    temp = pygame.Surface((1280, 720))
    
    # Draw to temp with effects
    # ... render background, sprites, etc.
    
    # Apply shake
    offset_x = math.sin(time * 0.03) * self.shake
    surface.blit(temp, (offset_x, 0))
Procedural Backgrounds (low overhead):

python
for y in range(720):
    intensity = 20 + y // 10
    pygame.draw.line(surface, (5, 8, intensity), (0, y), (1280, y))
Particle Systems (keep < 200 particles):

python
for p in self.particles:
    alpha = p['life'] / p['max_life']
    size = int(4 * alpha)
    color = (255, int(200 * alpha), 100)
    pygame.draw.circle(surface, color, (int(p['x']), int(p['y'])), size)
Color Safety Helper
python
def _safe_color(self, r, g, b, a=255):
    """Clamps RGB values to 0-255 range"""
    return (max(0, min(255, int(r))), 
            max(0, min(255, int(g))), 
            max(0, min(255, int(b))), 
            max(0, min(255, int(a))))
Use when calculating dynamic colors:

python
pulse = math.sin(time) * 50
color = self._safe_color(200 + pulse, 100, 150)
Best Practices
Frame-Rate Independence
Always use dt for movement:

python
# ❌ WRONG - speed depends on frame rate
self.x += 5

# ✅ CORRECT - consistent at any FPS
self.x += 300 * dt  # 300 pixels per second
Collision Detection
AABB (Axis-Aligned Bounding Box):

python
if (abs(obj1_x - obj2_x) < (obj1_w + obj2_w) / 2 and
    abs(obj1_y - obj2_y) < (obj1_h + obj2_h) / 2):
    # Collision occurred
Circle Collision:

python
dist = math.sqrt((obj1_x - obj2_x)**2 + (obj1_y - obj2_y)**2)
if dist < obj1_radius + obj2_radius:
    # Collision occurred
Score Design
python
# Small incremental scoring
self.score += 10   # Per frame survived
self.score += 100  # Per enemy hit

# Big bonuses
self.score += 5000   # Level complete
self.score += 10000  # Game complete
Memory Management
Clean up lists properly:

python
# ❌ WRONG - modifies list during iteration
for bullet in self.bullets:
    if bullet['y'] < 0:
        self.bullets.remove(bullet)

# ✅ CORRECT - iterate over copy
for bullet in self.bullets[:]:
    if bullet['y'] < 0:
        self.bullets.remove(bullet)
Testing & Debugging
Verify ROM Loads
Run engine and check console output:

text
[ROMS] Scanning roms/ directory...
[ROMS] ✓ Loaded: YourGame (Your Game)
[ROMS] Loaded 1 games (+2 built-in)
If you see:

text
[ROMS] ✗ Invalid: YourGame.py (no MiniGame subclass found)
Fix: Ensure class inherits MiniGame and matches filename.

Common Errors
Error	Cause	Solution
NameError: name 'MiniGame' is not defined	Missing parent class	Engine injects it - check class name
ROM not appearing in menu	Class name ≠ filename	YourGame.py must contain class YourGame(MiniGame)
Trackball not responding	Using absolute position	Use get_smooth_delta() not get_pos()
Sounds not playing	self.sound is None	Check if self.sound: before .play()
Debug Output
python
def update(self, dt, trackball):
    dx, dy = trackball.get_smooth_delta()
    print(f"Delta: {dx:.2f}, {dy:.2f}, Score: {self.score}")
Watch console during gameplay.

FPS Display
Press F key during gameplay to toggle FPS counter.
