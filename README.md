Trackball Arcade Engine - COMPLETE PROFESSIONAL DEVELOPER MANUAL
Version 1.0 | January 2026 | Self-contained ROM development—no engine source required.

1. ROM Creation (5-Minute Setup)
Place roms/MyGame.py:

python
import pygame
import math
import random  # Engine auto-injects these + TrackballInput

class MyGame(MiniGame):  # SINGLE class inheriting ONLY MiniGame
    def __init__(self, *args, sound=None, **kwargs):
        super().__init__("MyGame", "Arcade shooter with powerups!", *args, **kwargs)
        self.sound = sound  # REQUIRED: Store SoundSynthesizer instance
        self.reset()

    # OBBLIGATORI: Implement these EXACTLY (see sections below)
Engine auto-scans roms/*.py on startup, injects deps, adds to carousel menu. PNG menuimages/MyGame.png optional (auto-placeholder).
​

2. Core Methods (MANDATORY IMPLEMENTATION)
2.1 __init__(self, *args, sound=None, **kwargs)
python
super().__init__("EXACT_TITLE", "Menu description (50 chars max)", *args, **kwargs)
self.sound = sound  # Save for SFX
self.reset()  # Init state
name: Carousel title + highscore file (scores/MyGame_scores.json).

Called once per game load.
​

2.2 reset(self)
python
def reset(self):
    self.score = 0  # REQUIRED: Your points accumulator
    self.is_game_over = False  # REQUIRED: Set True on win/lose
    self.is_paused = False  # Engine-managed, don't touch
    # Init positions, lives, velocities, lists...
    self.sound.create_game_start().play()  # Round start sound
Called: Game start + after EVERY score/point. Full reset.
​

2.3 update(self, dt: float, trackball: TrackballInput)
python
def update(self, dt, trackball):  # dt ≈ 1/60 @ 60 FPS fixed
    if self.is_paused or self.is_game_over:
        return  # Engine auto-skips
    
    # INPUT
    dx, dy = trackball.get_smooth_delta()  # Preferred: smoothed/sensitivity-scaled
    # dx, dy = trackball.get_delta()      # Raw alternative
    
    if trackball.button_left_pressed:      # NEW left press only
        # Fire/shoot/confirm
        pass
    
    # PHYSICS/COLLISIONS (dt-multiplied)
    self.player_x += dx * 400 * dt  # pixels/sec speed
    
    # SCORING: self.score += points EVERYWHERE
    self.score += 10  # ex: time survived
    
    # GAMEOVER: Set ONLY when complete (first-to-5, lives=0...)
    if self.lives <= 0:
        self.is_game_over = True
        self.score += 5000  # RECOMMENDED end bonus
NEVER handle button_middle_pressed (pause) or button_right_pressed (menu)—engine owns them.
​

2.4 draw(self, surface: pygame.Surface)
python
def draw(self, surface):  # 1280x720 virtual - engine scales/letterbox
    # 1. Background/effects
    surface.fill((0,0,20))  # Or gradient like PongAI
    
    # 2. Shake example (optional)
    sx = math.sin(pygame.time.get_ticks()*0.03) * self.shake
    self.shake *= 0.85
    
    # 3. Sprites/UI with offsets
    pygame.draw.circle(surface, (255,255,255), (int(self.x+sx), int(self.y+sy)), 10)
    
    # 4. SCORE DISPLAY (RECOMMENDED top-right)
    font = pygame.font.Font(None, 72)
    score_txt = font.render(str(self.score), True, (255,240,200))
    surface.blit(score_txt, (1100 - score_txt.get_width(), 50))
    
    # 5. PAUSE OVERLAY (MANDATORY - see UX section)
    if self.is_paused:
        self._draw_pause_overlay(surface)
Engine: 60 FPS, scaling, FPS counter (F toggle).
​

2.5 getscore(self)
python
def getscore(self):
    return self.score  # int only
Engine calls post-gameover for highscore check.
​

3. Input - TrackballInput (Full API)
In update() param:

python
dx, dy = trackball.get_smooth_delta()  # SMOOTHED (deadzone/cap/sensitivity)
dx, dy = trackball.get_delta()         # RAW deltas

# EDGE-TRIGGERED BUTTONS (True ONLY on NEW press)
if trackball.button_left_pressed:     # Fire/Select
if trackball.button_middle_pressed:   # PAUSE (engine handles)
if trackball.button_right_pressed:    # MENU (engine handles ONLY when paused)
Sensitivity: 10-200 (settings menu).

Mouse captured/invisible for true trackball feel.
​

4. Audio - SoundSynthesizer (COMPLETE REFERENCE)
self.sound = procedural synth (no files, cached). Call .play() immediately:

Sound	Code	Trigger Examples	Notes
Game Start	self.sound.create_game_start().play()	reset()	Fanfare (262-523Hz)
Pause	self.sound.create_pause().play()	Engine auto	523Hz sine
Hit	self.sound.create_target_hit().play()	Bullet collision	880+1320Hz triangle
Miss	self.sound.create_target_miss().play()	Enemy escape	200Hz sawtooth
Combo	self.sound.create_combo(1).play()	Point streak	Pitch scales with level
Shoot	self.sound.create_shoot().play()	Fire	FM sweep 1200→900Hz
Powerup	self.sound.create_powerup().play()	Item collect	Arpeggio + harmonics
Blip	self.sound.create_blip(0).play()	Menu nav	Pitch 0-?
Select	self.sound.create_select().play()	Confirm	440+660Hz square
Back	self.sound.create_back().play()	Engine auto	330Hz sine
RULE: Never create_gameover()/create_highscore()—engine exclusive. Precache in __init__ if latency-critical.
​

5. Game Lifecycle & States (FULL FLOW)
text
MENU (carousel) ── LEFT ── PLAYING ── MIDDLE ── PAUSED ── RIGHT ── MENU
                  │              │                │
                  │         is_game_over=True    │
                  └──── GAMEOVER ── HS INPUT ── HIGHSCORES ── LEFT/RIGHT ── MENU
State	Trigger	Dev Action
MENU	Start/Right-from-pause	None—carousel auto
PLAYING	Left on game	reset() → update()/draw() loop
PAUSED	Middle button	draw() overlay + instructions
GAMEOVER	YOUR is_game_over=True	Engine overlay + score check
HIGHSCORES	Right/Left from GAMEOVER	Auto-list + input if qualified
ESC: Global back/exit. F: FPS toggle.
​

6. Pause/Exit Mechanic (MANDATORY IMPLEMENTATION)
Right button = EXIT ONLY when PAUSED (safety—no accidental quits).

Engine code (invisible to you):

python
if trackball.button_right_pressed and self.currentgame.is_paused:
    state = MENU; music.play_menu_music(); sound.create_back(); currentgame=None
YOUR draw() MUST include:

python
def _draw_pause_overlay(self, surface):
    ov = pygame.Surface((1280,720), pygame.SRCALPHA)
    ov.fill((20,30,60,220))
    surface.blit(ov, (0,0))
    
    font_big = pygame.font.Font(None, 140)
    pause = font_big.render("PAUSED", True, (255,255,255))
    surface.blit(pause, (640-pause.get_width()//2, 280))
    
    font_small = pygame.font.Font(None, 52)
    resume = font_small.render("MIDDLE BUTTON: RESUME", True, (100,255,100))
    menu = font_small.render("RIGHT BUTTON: MENU EXIT", True, (255,200,100))
    surface.blit(resume, (640-resume.get_width()//2, 420))
    surface.blit(menu, (640-menu.get_width()//2, 480))
Test: Play → Middle (pause overlay) → Right (clean menu return).
​

7. High Scores (Automatic)
File: scores/MyGame_scores.json (top 10):

json
[{"score":15000,"player":"PRO","date":"2026-01-13 16:02"},...]
Flow:

Gameover → engine: if score beats top10: Prompt 3-char input.

Input UI (engine): Trackball-X = scroll A-Z0-9, Y=box select, Left=next box, Right=cancel.

Auto-save/sort.

Your job: self.score += points constantly (+5000 end bonus).
​

8. Rendering Best Practices (1280x720)
Fonts: pygame.font.Font(None, size) (92=score, 48=UI).

Shake: self.shake += 10; sx=sin(ticks)*shake (PongAI).

Trails: List append({'x':x,'life':0.5}); fade in draw().

Safe Colors: (max(0,min(255,int(r))),...) clamp.

Temp Surface: For complex comps (PongAI BG).
​

9. Persistence & Config
Config: trackballarcadeconfig.json (sensitivity, fullscreen, volumes)—engine handles.

Music: music/*.mp3/ogg auto-play in MENU.

Scores: Per-game JSON auto.
​

10. Complete Example ROM - "Shooter"
python
class Shooter(MiniGame):
    def __init__(self, *args, sound=None, **kwargs):
        super().__init__("Shooter", "Dodge + shoot asteroids!", *args, **kwargs)
        self.sound = sound
        self.reset()

    def reset(self):
        self.score = 0
        self.is_game_over = False
        self.player_x = 640
        self.bullets = []
        self.enemies = []
        self.lives = 5
        self.shake = 0
        self.sound.create_game_start().play()

    def update(self, dt, trackball):
        if self.is_paused or self.is_game_over: return
        
        dx, _ = trackball.get_smooth_delta()
        self.player_x += dx * 500 * dt
        self.player_x = max(30, min(1250, self.player_x))
        
        if trackball.button_left_pressed:
            self.bullets.append({'x':self.player_x, 'y':550, 'vy':-600})
            self.sound.create_shoot().play()
        
        # Bullet/enemy update, collisions...
        self.score += 1  # Survival tick
        
        if self.lives <= 0:
            self.is_game_over = True
            self.score += 5000

    def draw(self, surface):
        surface.fill((3,5,15))
        
        sx = math.sin(pygame.time.get_ticks()*0.04)*self.shake
        self.shake *= 0.88
        
        # Player
        pygame.draw.rect(surface, (100,200,255), (self.player_x-15,530,30,40))
        
        # Bullets/Enemies...
        
        # Score
        font = pygame.font.Font(None, 88)
        s_txt = font.render(str(self.score), True, (255,220,150))
        surface.blit(s_txt, (1180-s_txt.get_width(), 40))
        
        # PAUSE OVERLAY (MANDATORY)
        if self.is_paused:
            ov = pygame.Surface((1280,720), pygame.SRCALPHA)
            ov.fill((15,25,50,200))
            surface.blit(ov, (0,0))
            p_txt = pygame.font.Font(None, 130).render("PAUSED", True, (255,255,255))
            surface.blit(p_txt, (640-p_txt.get_width()//2, 320))
            r_txt = pygame.font.Font(None, 55).render("RIGHT: MENU  |  MIDDLE: RESUME", True, (255,220,100))
            surface.blit(r_txt, (640-r_txt.get_width()//2, 450))

    def getscore(self):
        return self.score
Ready-to-run. Follows ALL rules.
​
