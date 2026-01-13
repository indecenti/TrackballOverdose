🎮 Trackball Arcade System – ROM Development Guide

Professional arcade game engine with dynamic ROM loading
Build playable arcade games in minutes with Python + Pygame

📑 Table of Contents

Quick Start

MiniGame API Reference

TrackballInput API

SoundSynthesizer API

Engine Lifecycle

Drawing Guidelines

Best Practices

Testing & Debugging

🚀 Quick Start
Minimal ROM Template

Create roms/YourGame.py:

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


✅ That’s it.
The engine automatically handles:

Menus

High scores

Pause & game over

Music

Display scaling

🧩 MiniGame API Reference
Required Methods
__init__(self, *args, sound=None, **kwargs)

Purpose: Initialize your game instance

Parameters:

*args, **kwargs: Must be passed to parent

sound: SoundSynthesizer instance

def __init__(self, *args, sound=None, **kwargs):
    super().__init__("Pong", "First to 5 wins!", *args, **kwargs)
    self.sound = sound
    self.paddle_speed = 480
    self.reset()

reset(self)

Purpose: Reset game state
Called: Game start, retry after game over

Must initialize:

self.score

self.is_game_over

self.is_paused

All game variables

def reset(self):
    self.score = 0
    self.is_game_over = False
    self.is_paused = False
    
    self.ball_x = 640
    self.ball_y = 360
    self.ball_vx = 300 * random.choice([-1, 1])
    
    if self.sound:
        self.sound.create_game_start().play()

update(self, dt, trackball)

Purpose: Game logic (60 FPS)

Rules:

Always exit if paused or game over

Use dt for movement

Set self.is_game_over = True to finish

def update(self, dt, trackball):
    if self.is_paused or self.is_game_over:
        return
    
    dx, dy = trackball.get_smooth_delta()
    self.player_x += dx * 500 * dt
    
    if trackball.button_left_pressed:
        self.bullets.append({'x': self.player_x, 'y': 650})
        self.sound.create_shoot().play()
    
    for b in self.bullets[:]:
        b['y'] -= 400 * dt
        if b['y'] < 0:
            self.bullets.remove(b)
    
    if self.score >= 5000:
        self.is_game_over = True
        self.score += 10000

draw(self, surface)

Purpose: Render frame to 1280×720 virtual screen

Rules:

❌ Never call pygame.display.flip()

❌ Do NOT draw game over screen

✅ Engine handles scaling & overlays

def draw(self, surface):
    surface.fill((10, 10, 30))
    
    pygame.draw.circle(
        surface, (0, 255, 120),
        (int(self.player_x), 650), 20
    )
    
    for b in self.bullets:
        pygame.draw.rect(
            surface, (255, 255, 0),
            (b['x']-2, b['y']-8, 4, 16)
        )
    
    font = pygame.font.Font(None, 64)
    score_text = font.render(str(self.score), True, (255, 255, 255))
    surface.blit(score_text, (50, 50))

Engine-Controlled Flags
Variable	Type	You Set	Engine Reads	Purpose
self.score	int	✅	✅	High score
self.is_game_over	bool	✅	✅	Triggers end
self.is_paused	bool	✅	✅	Skip update

⚠️ Once self.is_game_over = True, engine takes control.

🕹 TrackballInput API

Available in update(self, dt, trackball).

Movement
dx, dy = trackball.get_smooth_delta()   # Recommended
dx, dy = trackball.get_delta()          # Raw
vx, vy = trackball.get_velocity()       # Velocity vector

Buttons – Edge Triggered
trackball.button_left_pressed
trackball.button_middle_pressed
trackball.button_right_pressed

Buttons – Held
trackball.button_left
trackball.button_middle
trackball.button_right

Advanced
trackball.speed
trackball.angle
trackball.sensitivity

🔊 SoundSynthesizer API

Access via self.sound.

Lifecycle Sounds
self.sound.create_game_start().play()


(Game over & high score handled by engine)

Gameplay Sounds
self.sound.create_shoot().play()
self.sound.create_target_hit().play()
self.sound.create_target_miss().play()
self.sound.create_powerup().play()

Combo System
self.sound.create_combo(level).play()  # level 1–9

🔁 Engine Lifecycle
[MENU] → [PLAYING] → [GAME OVER]
   ↑         ↓           ↓
   └── ESC ──┴── Retry ──┘

What Engine Handles

Menus & navigation

High scores

Pause menu

Scaling

Music

Settings persistence

What You Handle

Game logic

Rendering

Score & end condition

Gameplay sounds

🎨 Drawing Guidelines
Canvas

Resolution: 1280×720

Origin: top-left

Safe UI margin: 100 px

Temp Surfaces
temp = pygame.Surface((1280, 720))
surface.blit(temp, (offset_x, 0))

Particle Limit

Keep under 200 particles.

Safe Color Helper
def _safe_color(self, r, g, b, a=255):
    return (
        max(0, min(255, int(r))),
        max(0, min(255, int(g))),
        max(0, min(255, int(b))),
        max(0, min(255, int(a)))
    )

✅ Best Practices
Frame-Rate Independence
self.x += 300 * dt

Collision Detection

AABB

if abs(x1-x2) < (w1+w2)/2 and abs(y1-y2) < (h1+h2)/2:
    pass


Circle

dist = math.hypot(x1-x2, y1-y2)

List Cleanup
for bullet in self.bullets[:]:
    if bullet['y'] < 0:
        self.bullets.remove(bullet)

🧪 Testing & Debugging
ROM Load Output
[ROMS] ✓ Loaded: YourGame (Your Game)


❌ Error:

[ROMS] ✗ Invalid: YourGame.py


➡ Fix class name & inheritance.

Debug Print
print(f"Delta: {dx:.2f}, Score: {self.score}")

FPS Counter

➡ Press F during gameplay
