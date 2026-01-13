Perfetto — hai fornito la documentazione completa della Trackball Arcade Engine – Developer Manual v1.0 (Gennaio 2026) e vuoi integrarla chiarendo in modo esplicito:

La firma corretta di __init__ per ogni ROM.

La spiegazione di *args, **kwargs e del parametro sound.

Ecco la documentazione completa, aggiornata senza rimuovere nulla dell’originale, con le integrazioni chiaramente strutturate ed in tono coerente con lo stile tecnico e sintetico del manuale.

Trackball Arcade Engine - COMPLETE PROFESSIONAL DEVELOPER MANUAL
Version 1.0 | January 2026 | Self-contained ROM development — no engine source required

1. ROM Creation (5-Minute Setup)
Place file roms/MyGame.py:

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
Engine auto-scans roms/*.py on startup, injects dependencies, and adds games to the carousel menu.
Optional menu image: place menuimages/MyGame.png (a placeholder is auto-generated otherwise).

ATTENZIONE!!!!!
La firma del costruttore __init__ è obbligatoriamente identica per tutte le ROM (vedi 2.1).

2. Core Methods (MANDATORY IMPLEMENTATION)
2.1 __init__(self, *args, sound=None, **kwargs)
Esempio corretto e completo:

python
def __init__(self, *args, sound=None, **kwargs):
    super().__init__("Asteroids", "Dodge & shoot comic asteroids!", *args, **kwargs)
    self.sound = sound  # REQUIRED: SoundSynthesizer instance
    self.reset()
self → riferimento all’istanza del gioco (standard Python).

*args → argomenti posizionali che il motore passa automaticamente (es. riferimenti interni, configurazioni). Non specificarli esplicitamente.

sound=None → SoundSynthesizer fornito dal motore. Devi salvarlo in self.sound per generare effetti audio.

**kwargs → dizionario di argomenti con nome. Permette compatibilità futura con nuove versioni del motore senza modificare la ROM.

La combinazione (*args, sound=None, **kwargs) è obbligatoria e non modificabile. Garantisce che la ROM rimanga compatibile con tutte le versioni del Trackball Arcade Engine.

python
super().__init__("EXACT_TITLE", "Menu description (50 chars max)", *args, **kwargs)
self.sound = sound
self.reset()
Il nome passato a super().__init__() definisce sia il titolo nel menu che il file degli highscore (scores/<TITLE>_scores.json).

Chiamato una sola volta all’avvio del gioco.

2.2 reset(self)
python
def reset(self):
    self.score = 0  # REQUIRED: Your points accumulator
    self.is_game_over = False  # REQUIRED: Set True on win/lose
    self.is_paused = False  # Engine-managed, don't touch
    # Init positions, lives, velocities, lists...
    self.sound.create_game_start().play()  # Round start sound
Called at: game start + after EVERY score/point.
Resets all variables to their initial state.

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
Never handle:
button_middle_pressed (pause) or button_right_pressed (menu) — managed by engine.

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
Engine: 60 FPS fixed, scaling with FPS counter (toggle: F key).

2.5 getscore(self)
python
def getscore(self):
    return self.score  # int only
Called automatically post-is_game_over=True for highscore comparison.

3. Input - TrackballInput (Full API)
Inside update():

python
dx, dy = trackball.get_smooth_delta()  # SMOOTHED (deadzone/cap/sensitivity)
dx, dy = trackball.get_delta()         # RAW deltas
Edge-triggered buttons (True only on new press):

python
if trackball.button_left_pressed:     # Fire/Select
if trackball.button_middle_pressed:   # PAUSE (engine handles)
if trackball.button_right_pressed:    # MENU (engine handles ONLY when paused)
Sensitivity: 10–200 (changeable in settings menu).
Mouse is hidden/captured for authentic trackball feel.

4. Audio - SoundSynthesizer (COMPLETE REFERENCE)
Each MiniGame receives a SoundSynthesizer instance via sound parameter.
Every sound is synthesized procedurally (no audio files).

Call .play() immediately after creation:

Sound	Code	Trigger Example	Notes
Game Start	self.sound.create_game_start().play()	reset()	Fanfare (262–523 Hz)
Pause	self.sound.create_pause().play()	Auto-engine	523 Hz sine
Hit	self.sound.create_target_hit().play()	Bullet collision	880+1320 Hz triangle
Miss	self.sound.create_target_miss().play()	Enemy escape	200 Hz sawtooth
Combo	self.sound.create_combo(1).play()	Point streak	Pitch scales with level
Shoot	self.sound.create_shoot().play()	Fire	FM sweep 1200→900 Hz
Powerup	self.sound.create_powerup().play()	Item collect	Arpeggio + harmonics
Blip	self.sound.create_blip(0).play()	Menu navigation	Variable pitch
Select	self.sound.create_select().play()	Confirm	440+660 Hz square
Back	self.sound.create_back().play()	Engine auto	330 Hz sine
RULE:
Never create create_gameover() or create_highscore() — the engine reserves them.
Preload calls in __init__ if latency-sensitive.

5. Game Lifecycle & States (FULL FLOW)
text
MENU (carousel) ── LEFT ── PLAYING ── MIDDLE ── PAUSED ── RIGHT ── MENU
                  │              │                │
                  │         is_game_over=True    │
                  └──── GAMEOVER ── HS INPUT ── HIGHSCORES ── LEFT/RIGHT ── MENU
State	Trigger	Developer Action
MENU	Start / Right-from-pause	None — handled automatically
PLAYING	Left button	reset() → normal loop (update()/draw())
PAUSED	Middle button	Draw pause overlay + resume instructions
GAMEOVER	is_game_over=True	Engine overlays score + checks highscores
HIGHSCORES	Right/Left from GAMEOVER	Engine handles list and initials input
Global keys:
ESC = Exit / F = FPS toggle.

6. Pause/Exit Mechanic (MANDATORY IMPLEMENTATION)
Right button = Exit only when paused (safety).

Engine invisible logic:

python
if trackball.button_right_pressed and self.currentgame.is_paused:
    state = MENU
    music.play_menu_music()
    sound.create_back()
    currentgame=None
Your draw() must include:

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
Test flow:
Play → Middle (pause overlay) → Right (clean menu return).

7. High Scores (Automatic)
File: scores/MyGame_scores.json (top 10):

json
[{"score":15000,"player":"PRO","date":"2026-01-13 16:02"}, ...]
Flow:
GAMEOVER → engine checks score → if in top 10 → prompts 3-char input.

Engine’s name entry system:

Trackball X → scroll characters (A–Z, 0–9)

Trackball Y → move box selector

Left button → next box

Right button → cancel

Auto-save and sorted on completion.

Developer task: just increment self.score (+5000 bonus at end recommended).

8. Rendering Best Practices (1280x720)
Fonts: pygame.font.Font(None, size) (92 = score, 48 = UI).

Shake: self.shake += 10; sx = sin(ticks)*self.shake.

Trails: keep list: trail.append({'x':x,'life':0.5}) → fade in draw().

Clamp colors: (max(0, min(255, int(r))), ...).

For complex backgrounds: use a temporary Surface (like PongAI).

9. Persistence & Config
Config file: trackballarcadeconfig.json (handles sensitivity, fullscreen, volume).

Music: music/*.mp3/ogg auto-play in menu.

Highscores: per-game JSON stored automatically.
