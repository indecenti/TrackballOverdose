import pygame
import json
import sys
import numpy as np
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import math
import random
import os
import pygame.gfxdraw
from dataclasses import dataclass
from enum import Enum
import importlib.util
import inspect 
romsdir = Path("roms")


def resource_path(relative_path):
    """Ottiene il path corretto sia per sviluppo che per exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# ============== SOUND SYNTHESIZER ==============
class SoundSynthesizer:
    """Sintetizzatore audio professionale per effetti arcade"""

    def __init__(self, sample_rate: int = 22050):
        pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=512)
        self.sample_rate = sample_rate
        self.sounds_cache = {}

    def _generate_wave(self, frequency: float, duration: float, wave_type: str = 'sine') -> np.ndarray:
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples, False)

        if wave_type == 'sine':
            wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * frequency * t))
        elif wave_type == 'sawtooth':
            wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
        elif wave_type == 'triangle':
            wave = 2 * np.abs(2 * (t * frequency - np.floor(0.5 + t * frequency))) - 1
        else:
            wave = np.sin(2 * np.pi * frequency * t)
        return wave

    def _apply_envelope(self, wave: np.ndarray, attack: float, decay: float,
                        sustain: float, release: float) -> np.ndarray:
        total_samples = len(wave)
        envelope = np.ones(total_samples)

        attack_samples = int(attack * self.sample_rate)
        decay_samples = int(decay * self.sample_rate)
        release_samples = int(release * self.sample_rate)

        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        if decay_samples > 0:
            decay_end = attack_samples + decay_samples
            envelope[attack_samples:decay_end] = np.linspace(1, sustain, decay_samples)

        sustain_start = attack_samples + decay_samples
        sustain_end = total_samples - release_samples
        if sustain_end > sustain_start:
            envelope[sustain_start:sustain_end] = sustain
        if release_samples > 0:
            envelope[-release_samples:] = np.linspace(sustain, 0, release_samples)
        return wave * envelope

    def _to_pygame_sound(self, wave: np.ndarray, volume: float = 0.3) -> pygame.mixer.Sound:
        wave = wave * volume
        wave = np.clip(wave, -1.0, 1.0)
        stereo_wave = np.column_stack((wave, wave))
        sound_array = (stereo_wave * 32767).astype(np.int16)
        return pygame.mixer.Sound(sound_array)

    def create_blip(self, pitch: int = 0) -> pygame.mixer.Sound:
        cache_key = f"blip_{pitch}"
        if cache_key in self.sounds_cache:
            return self.sounds_cache[cache_key]
        freq = 440 + (pitch * 100)
        wave = self._generate_wave(freq, 0.05, 'square')
        wave = self._apply_envelope(wave, 0.01, 0.01, 0.5, 0.03)
        sound = self._to_pygame_sound(wave, 0.2)
        self.sounds_cache[cache_key] = sound
        return sound

    def create_select(self) -> pygame.mixer.Sound:
        if "select" in self.sounds_cache:
            return self.sounds_cache["select"]
        wave1 = self._generate_wave(440, 0.08, 'square')
        wave2 = self._generate_wave(660, 0.08, 'square')
        wave = np.concatenate([wave1, wave2])
        wave = self._apply_envelope(wave, 0.01, 0.02, 0.7, 0.05)
        sound = self._to_pygame_sound(wave, 0.25)
        self.sounds_cache["select"] = sound
        return sound

    def create_back(self) -> pygame.mixer.Sound:
        if "back" in self.sounds_cache:
            return self.sounds_cache["back"]
        wave = self._generate_wave(330, 0.1, 'sine')
        wave = self._apply_envelope(wave, 0.01, 0.03, 0.5, 0.06)
        sound = self._to_pygame_sound(wave, 0.2)
        self.sounds_cache["back"] = sound
        return sound

    def create_pause(self) -> pygame.mixer.Sound:
        """Suono menu pausa"""
        if "pause" in self.sounds_cache:
            return self.sounds_cache["pause"]
        wave = self._generate_wave(523, 0.1, 'sine')
        wave = self._apply_envelope(wave, 0.01, 0.02, 0.6, 0.07)
        sound = self._to_pygame_sound(wave, 0.22)
        self.sounds_cache["pause"] = sound
        return sound

    def create_shoot(self) -> pygame.mixer.Sound:
        """Suono di sparo laser"""
        if "shoot" in self.sounds_cache:
            return self.sounds_cache["shoot"]
        duration = 0.15
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples, False)
        freq_sweep = 1200 - (900 * t / duration)
        wave = np.sin(2 * np.pi * freq_sweep * t)
        wave = self._apply_envelope(wave, 0.001, 0.02, 0.4, 0.127)
        sound = self._to_pygame_sound(wave, 0.22)
        self.sounds_cache["shoot"] = sound
        return sound

    def create_target_hit(self) -> pygame.mixer.Sound:
        """Suono di colpo a segno"""
        if "target_hit" in self.sounds_cache:
            return self.sounds_cache["target_hit"]
        wave = self._generate_wave(880, 0.1, 'triangle')
        harmonic = self._generate_wave(1320, 0.1, 'sine') * 0.3
        wave = wave + harmonic
        wave = self._apply_envelope(wave, 0.005, 0.02, 0.6, 0.073)
        sound = self._to_pygame_sound(wave, 0.28)
        self.sounds_cache["target_hit"] = sound
        return sound

    def create_target_miss(self) -> pygame.mixer.Sound:
        """Suono di bersaglio mancato"""
        if "target_miss" in self.sounds_cache:
            return self.sounds_cache["target_miss"]
        wave = self._generate_wave(200, 0.12, 'sawtooth')
        wave = self._apply_envelope(wave, 0.01, 0.03, 0.4, 0.08)
        sound = self._to_pygame_sound(wave, 0.18)
        self.sounds_cache["target_miss"] = sound
        return sound

    def create_combo(self, level: int = 1) -> pygame.mixer.Sound:
        """Suono di combo"""
        cache_key = f"combo_{level}"
        if cache_key in self.sounds_cache:
            return self.sounds_cache[cache_key]
        base_freq = 660 + (level * 110)
        wave = self._generate_wave(base_freq, 0.08, 'square')
        wave = self._apply_envelope(wave, 0.005, 0.015, 0.7, 0.06)
        sound = self._to_pygame_sound(wave, 0.25)
        self.sounds_cache[cache_key] = sound
        return sound

    def create_game_start(self) -> pygame.mixer.Sound:
        if "game_start" in self.sounds_cache:
            return self.sounds_cache["game_start"]
        freqs = [262, 330, 392, 523]
        waves = [self._generate_wave(freq, 0.12, 'sine') for freq in freqs]
        wave = np.concatenate(waves)
        wave = self._apply_envelope(wave, 0.01, 0.02, 0.8, 0.1)
        sound = self._to_pygame_sound(wave, 0.3)
        self.sounds_cache["game_start"] = sound
        return sound

    def create_game_over(self) -> pygame.mixer.Sound:
        if "game_over" in self.sounds_cache:
            return self.sounds_cache["game_over"]
        freqs = [440, 370, 311, 233]
        waves = [self._generate_wave(freq, 0.2, 'sawtooth') for freq in freqs]
        wave = np.concatenate(waves)
        wave = self._apply_envelope(wave, 0.02, 0.05, 0.7, 0.2)
        sound = self._to_pygame_sound(wave, 0.3)
        self.sounds_cache["game_over"] = sound
        return sound

    def create_high_score(self) -> pygame.mixer.Sound:
        if "high_score" in self.sounds_cache:
            return self.sounds_cache["high_score"]
        freqs = [523, 659, 784, 1047]
        waves = []
        for i, freq in enumerate(freqs):
            duration = 0.15 if i < 3 else 0.3
            waves.append(self._generate_wave(freq, duration, 'sine'))
        wave = np.concatenate(waves)
        wave = self._apply_envelope(wave, 0.01, 0.03, 0.8, 0.2)
        sound = self._to_pygame_sound(wave, 0.35)
        self.sounds_cache["high_score"] = sound
        return sound

    def create_powerup(self) -> pygame.mixer.Sound:
        """Suono di power-up"""
        if "powerup" in self.sounds_cache:
            return self.sounds_cache["powerup"]
        freqs = [523, 659, 784, 1047, 1319]
        waves = []
        for freq in freqs:
            wave = self._generate_wave(freq, 0.08, 'sine')
            harmonic = self._generate_wave(freq * 2, 0.08, 'sine') * 0.3
            waves.append(wave + harmonic)
        wave = np.concatenate(waves)
        wave = self._apply_envelope(wave, 0.005, 0.02, 0.8, 0.1)
        sound = self._to_pygame_sound(wave, 0.28)
        self.sounds_cache["powerup"] = sound
        return sound


# ============== TRACKBALL INPUT ==============
class TrackballInput:
    """Gestione professionale input trackball arcade"""

    def __init__(self, sensitivity: float = 50.0):
        self.sensitivity = sensitivity
        self.delta_x = 0
        self.delta_y = 0
        self.speed = 0.0
        self.angle = 0.0

        # Pulsanti (1=left, 2=middle, 3=right)
        self.button_left = False
        self.button_middle = False
        self.button_right = False
        self.button_left_pressed = False
        self.button_middle_pressed = False
        self.button_right_pressed = False
        self.button_left_released = False
        self.button_middle_released = False
        self.button_right_released = False

        # Smoothing
        self.smooth_factor = 0.3
        self._smooth_dx = 0
        self._smooth_dy = 0

        # Limiti
        self.max_speed = 100.0
        self.dead_zone = 0.1







    def update(self, events: List[pygame.event.Event]):
        """Aggiorna stato input"""
        self.button_left_pressed = False
        self.button_middle_pressed = False
        self.button_right_pressed = False
        self.button_left_released = False
        self.button_middle_released = False
        self.button_right_released = False

        # Movimento trackball
        raw_dx, raw_dy = pygame.mouse.get_rel()
        self.delta_x = raw_dx * (self.sensitivity / 50.0)
        self.delta_y = raw_dy * (self.sensitivity / 50.0)

        # Smoothing
        self._smooth_dx = self._smooth_dx * (1 - self.smooth_factor) + self.delta_x * self.smooth_factor
        self._smooth_dy = self._smooth_dy * (1 - self.smooth_factor) + self.delta_y * self.smooth_factor

        # Calcola velocità e angolo
        self.speed = math.sqrt(self._smooth_dx**2 + self._smooth_dy**2)
        if self.speed > self.dead_zone:
            self.angle = math.atan2(self._smooth_dy, self._smooth_dx)
        else:
            self.speed = 0

        # Limita velocità
        if self.speed > self.max_speed:
            self.speed = self.max_speed
            self._smooth_dx = math.cos(self.angle) * self.max_speed
            self._smooth_dy = math.sin(self.angle) * self.max_speed

        # Eventi pulsanti
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.button_left = True
                    self.button_left_pressed = True
                elif event.button == 2:  # Middle button
                    self.button_middle = True
                    self.button_middle_pressed = True
                elif event.button == 3:
                    self.button_right = True
                    self.button_right_pressed = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.button_left = False
                    self.button_left_released = True
                elif event.button == 2:
                    self.button_middle = False
                    self.button_middle_released = True
                elif event.button == 3:
                    self.button_right = False
                    self.button_right_released = True






    def get_delta(self) -> Tuple[float, float]:
        return (self.delta_x, self.delta_y)

    def get_smooth_delta(self) -> Tuple[float, float]:
        return (self._smooth_dx, self._smooth_dy)

    def get_velocity(self) -> Tuple[float, float]:
        if self.speed < self.dead_zone:
            return (0, 0)
        return (self._smooth_dx, self._smooth_dy)

    def set_sensitivity(self, sensitivity: float):
        self.sensitivity = max(10, min(200, sensitivity))

    def reset(self):
        pygame.mouse.get_rel()
        self.delta_x = 0
        self.delta_y = 0
        self.speed = 0
        self._smooth_dx = 0
        self._smooth_dy = 0



# ============== ANIMATED BACKGROUND ==============
class AnimatedBackground:
    """Sfondo animato professionale stile arcade"""

    def __init__(self):
        self.stars = []
        self.time = 0.0

        for _ in range(80):
            self.stars.append({
                'x': random.randint(0, 1280),
                'y': random.randint(0, 720),
                'speed': random.uniform(0.3, 2.0),
                'size': random.randint(1, 3),
                'brightness': random.uniform(0.4, 1.0)
            })

        self.speed_lines = []
        for _ in range(25):
            self.speed_lines.append({
                'x': random.randint(-100, 1380),
                'y': random.randint(0, 720),
                'speed': random.uniform(8, 20),
                'length': random.randint(50, 150),
                'thickness': random.randint(1, 3)
            })

    def update(self, dt: float):
        self.time += dt

        for star in self.stars:
            star['x'] -= star['speed'] * dt * 15
            if star['x'] < 0:
                star['x'] = 1280
                star['y'] = random.randint(0, 720)

        for line in self.speed_lines:
            line['x'] -= line['speed'] * dt * 100
            if line['x'] + line['length'] < 0:
                line['x'] = 1280 + random.randint(0, 100)
                line['y'] = random.randint(0, 720)

    def draw(self, surface: pygame.Surface):
        for y in range(720):
            factor = y / 720
            r = int(5 + math.sin(self.time * 0.5 + factor) * 3)
            g = int(8 + math.sin(self.time * 0.3 + factor * 1.5) * 3)
            b = int(25 + math.sin(self.time * 0.4 + factor * 2) * 5)
            pygame.draw.line(surface, (r, g, b), (0, y), (1280, y))

        for star in self.stars:
            brightness = int(star['brightness'] * 255)
            twinkle = abs(math.sin(self.time * 2 + star['x'] * 0.01)) * 0.3 + 0.7
            color_val = int(brightness * twinkle)
            color = (color_val, color_val, min(255, color_val + 50))

            if star['size'] > 1:
                pygame.draw.circle(surface, color, (int(star['x']), int(star['y'])), star['size'])
            else:
                try:
                    surface.set_at((int(star['x']), int(star['y'])), color)
                except:
                    pass

        for line in self.speed_lines:
            color = (100, 120, 200)
            start_pos = (int(line['x']), int(line['y']))
            end_pos = (int(line['x'] + line['length']), int(line['y']))
            pygame.draw.line(surface, color, start_pos, end_pos, line['thickness'])


# ============== MENU CAROUSEL ==============
class CarouselItem:
    """Elemento del carousel con animazioni"""

    def __init__(self, name: str, description: str, image_surface: pygame.Surface):
        self.name = name
        self.description = description
        self.image = image_surface
        self.font_title = pygame.font.Font(None, 75)
        self.font_desc = pygame.font.Font(None, 38)

    def draw(self, surface: pygame.Surface, x: int, y: int, alpha: float = 1.0, offset_x: float = 0):
        draw_x = int(x + offset_x)
        temp_surface = pygame.Surface((900, 550), pygame.SRCALPHA)
        temp_surface.fill((0, 0, 0, 0))

        # Immagine
        img_y = 40
        img_rect = self.image.get_rect(center=(450, img_y + 175))
        temp_surface.blit(self.image, img_rect)

        # Titolo con outline
        text_y = 390
        for offset in [(0, 4), (4, 0), (0, -4), (-4, 0), (3, 3), (-3, 3), (3, -3), (-3, -3)]:
            outline = self.font_title.render(self.name, True, (0, 0, 0))
            temp_surface.blit(outline, outline.get_rect(center=(450 + offset[0], text_y + offset[1])))

        title = self.font_title.render(self.name, True, (255, 230, 0))
        temp_surface.blit(title, title.get_rect(center=(450, text_y)))

        # Descrizione
        desc = self.font_desc.render(self.description, True, (230, 240, 255))
        temp_surface.blit(desc, desc.get_rect(center=(450, text_y + 60)))

        if alpha < 1.0:
            temp_surface.set_alpha(int(alpha * 255))
        surface.blit(temp_surface, (draw_x, y))


class MenuCarousel:
    """Carousel menu professionale - carica PNG dal nome del gioco"""

    def __init__(self, images_dir: str = "menu_images"):
        self.images_dir = Path(resource_path(images_dir))
        self.images_dir.mkdir(exist_ok=True)
        self.items: List[CarouselItem] = []
        self.current_index = 0
        self.is_transitioning = False
        self.transition_progress = 0.0
        self.transition_duration = 0.35
        self.transition_direction = 0
        self.target_index = 0

    def add_item(self, name: str, description: str):
        image = self._load_or_create_image(name)
        self.items.append(CarouselItem(name, description, image))

    def _load_or_create_image(self, item_name: str) -> pygame.Surface:
        """Carica PNG con il nome del gioco o crea placeholder"""
        safe_name = "".join(c for c in item_name if c.isalnum() or c in (' ', '_', '-')).strip()

        possible_names = [
            f"{safe_name}.png",
            f"{safe_name.replace(' ', '_')}.png",
            f"{safe_name.replace(' ', '-')}.png",
            f"{safe_name.lower().replace(' ', '_')}.png"
        ]

        target_width, target_height = 600, 300

        for filename in possible_names:
            image_path = self.images_dir / filename
            if image_path.exists():
                try:
                    print(f"[Carousel] Loading image: {filename}")
                    img = pygame.image.load(str(image_path)).convert_alpha()
                    scale = min(target_width / img.get_width(), target_height / img.get_height())
                    new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                    return pygame.transform.smoothscale(img, new_size)
                except Exception as e:
                    print(f"[Carousel] Error loading {filename}: {e}")

        print(f"[Carousel] No image found for '{item_name}', creating placeholder")
        return self._create_placeholder(item_name, target_width, target_height)

    def _create_placeholder(self, item_name: str, width: int, height: int) -> pygame.Surface:
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        center_x, center_y = width // 2, height // 2

        pygame.draw.circle(surface, (100, 100, 150, 180), (center_x, center_y), 90, 5)
        pygame.draw.circle(surface, (150, 150, 200, 120), (center_x, center_y), 70)

        for angle in [0, math.pi/2, math.pi, -math.pi/2]:
            x1 = center_x + math.cos(angle) * 75
            y1 = center_y + math.sin(angle) * 75
            x2 = center_x + math.cos(angle) * 120
            y2 = center_y + math.sin(angle) * 120

            pygame.draw.line(surface, (255, 200, 0), (x1, y1), (x2, y2), 4)

            angle_left = angle + math.pi * 0.85
            angle_right = angle - math.pi * 0.85
            pygame.draw.line(surface, (255, 200, 0), (x2, y2),
                           (x2 + math.cos(angle_left) * 18, y2 + math.sin(angle_left) * 18), 4)
            pygame.draw.line(surface, (255, 200, 0), (x2, y2),
                           (x2 + math.cos(angle_right) * 18, y2 + math.sin(angle_right) * 18), 4)

        return surface

    def navigate(self, direction: int):
        if self.is_transitioning or not self.items:
            return
        self.target_index = (self.current_index + direction) % len(self.items)
        self.transition_direction = direction
        self.is_transitioning = True
        self.transition_progress = 0.0

    def update(self, dt: float):
        if not self.is_transitioning:
            return
        self.transition_progress += dt / self.transition_duration
        if self.transition_progress >= 1.0:
            self.transition_progress = 1.0
            self.current_index = self.target_index
            self.is_transitioning = False

    def draw(self, surface: pygame.Surface, x: int, y: int):
        if not self.items:
            return
        if not self.is_transitioning:
            self.items[self.current_index].draw(surface, x, y, 1.0, 0)
        else:
            progress = 1 - pow(1 - self.transition_progress, 3)
            slide_distance = 1000
            offset = progress * slide_distance * self.transition_direction
            self.items[self.current_index].draw(surface, x, y, 1.0 - progress * 0.6, offset)
            self.items[self.target_index].draw(surface, x, y, progress,
                                              -slide_distance * self.transition_direction + offset)

    def get_current_index(self) -> int:
        return self.current_index

    def get_item_count(self) -> int:
        return len(self.items)


# ============== CONFIG ==============
class Config:
    """Configurazione persistente"""

    CONFIG_FILE = "trackball_arcade_config.json"
    VALID_RESOLUTIONS = [(1280, 720), (1920, 1080)]

    def __init__(self):
        self.trackball_sensitivity = 50
        self.resolution = (1280, 720)
        self.fullscreen = False
        self.smooth_movement = True
        self.music_volume = 0.7
        self.sfx_volume = 0.8
        self.load()

    def load(self):
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                data = json.load(f)
                self.trackball_sensitivity = max(10, min(200, data.get('trackball_sensitivity', 50)))
                res = tuple(data.get('resolution', [1280, 720]))
                self.resolution = res if res in self.VALID_RESOLUTIONS else (1280, 720)
                self.fullscreen = bool(data.get('fullscreen', False))
                self.smooth_movement = bool(data.get('smooth_movement', True))
                self.music_volume = max(0.0, min(1.0, data.get('music_volume', 0.7)))
                self.sfx_volume = max(0.0, min(1.0, data.get('sfx_volume', 0.8)))
        except (FileNotFoundError, json.JSONDecodeError):
            self.save()

    def save(self):
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump({
                'trackball_sensitivity': self.trackball_sensitivity,
                'resolution': list(self.resolution),
                'fullscreen': self.fullscreen,
                'smooth_movement': self.smooth_movement,
                'music_volume': self.music_volume,
                'sfx_volume': self.sfx_volume
            }, f, indent=2)


# ============== HIGH SCORE MANAGER ==============
class HighScoreManager:
    """Gestione classifiche persistenti"""

    def __init__(self, scores_dir: str = "scores"):
        self.scores_dir = Path(scores_dir)
        self.scores_dir.mkdir(exist_ok=True)
        self.cache = {}

    def _get_scores_file(self, game_name: str) -> Path:
        safe_name = "".join(c for c in game_name if c.isalnum() or c in (' ', '_')).rstrip()
        return self.scores_dir / f"{safe_name.replace(' ', '_')}_scores.json"

    def load_scores(self, game_name: str) -> List[Dict]:
        if game_name in self.cache:
            return self.cache[game_name]
        scores_file = self._get_scores_file(game_name)
        try:
            with open(scores_file, 'r') as f:
                scores = json.load(f).get('scores', [])[:10]
                self.cache[game_name] = scores
                return scores
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def is_high_score(self, game_name: str, score: int) -> bool:
        scores = self.load_scores(game_name)
        return len(scores) < 10 or score > scores[-1]['score']

    def save_score(self, game_name: str, score: int, player_name: str = "AAA") -> int:
        scores = self.load_scores(game_name)
        new_entry = {
            'score': score,
            'player': player_name.upper(),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        scores.append(new_entry)
        scores.sort(key=lambda x: x['score'], reverse=True)
        scores = scores[:10]
        position = next((i + 1 for i, s in enumerate(scores) if s == new_entry), 0)

        with open(self._get_scores_file(game_name), 'w') as f:
            json.dump({'scores': scores}, f, indent=2)
        self.cache[game_name] = scores
        return position

    def get_high_score(self, game_name: str) -> int:
        scores = self.load_scores(game_name)
        return scores[0]['score'] if scores else 0


# ============== DISPLAY MANAGER ==============
class DisplayManager:
    """Gestione display professionale con scaling"""

    def __init__(self, config: Config):
        self.config = config
        self.VIRTUAL_WIDTH = 1280
        self.VIRTUAL_HEIGHT = 720

        self.virtual_surface = pygame.Surface((self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT))
        self.screen = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self.show_fps = False
        self.fps_font = None

        self.update_display()

    def update_display(self):
        flags = pygame.FULLSCREEN if self.config.fullscreen else 0
        try:
            self.screen = pygame.display.set_mode(self.config.resolution, flags)
            pygame.display.set_caption("Trackball Arcade System")
        except:
            self.config.fullscreen = False
            self.screen = pygame.display.set_mode((1280, 720), 0)

        self.calculate_letterbox()
        if self.show_fps:
            self.fps_font = pygame.font.Font(None, 24)

    def calculate_letterbox(self):
        screen_w, screen_h = self.config.resolution
        scale_x = screen_w / self.VIRTUAL_WIDTH
        scale_y = screen_h / self.VIRTUAL_HEIGHT
        self.scale = min(scale_x, scale_y)

        scaled_w = int(self.VIRTUAL_WIDTH * self.scale)
        scaled_h = int(self.VIRTUAL_HEIGHT * self.scale)

        self.offset_x = (screen_w - scaled_w) // 2
        self.offset_y = (screen_h - scaled_h) // 2

    def render(self, fps: float = 0.0):
        self.screen.fill((0, 0, 0))

        scaled = pygame.transform.smoothscale(self.virtual_surface,
                                             (int(self.VIRTUAL_WIDTH * self.scale),
                                              int(self.VIRTUAL_HEIGHT * self.scale)))
        self.screen.blit(scaled, (self.offset_x, self.offset_y))

        if self.show_fps and self.fps_font and fps > 0:
            color = (0, 255, 0) if fps >= 58 else (255, 255, 0) if fps >= 45 else (255, 0, 0)
            fps_text = self.fps_font.render(f"FPS: {fps:.1f}", True, color)
            self.screen.blit(fps_text, (10, 10))

        pygame.display.flip()

    def toggle_fps_display(self):
        self.show_fps = not self.show_fps
        if self.show_fps and not self.fps_font:
            self.fps_font = pygame.font.Font(None, 24)


# ============== MUSIC MANAGER ==============
class MusicManager:
    """Gestione musica di sottofondo"""

    def __init__(self, music_dir: str = "music"):
        self.music_dir = Path(resource_path(music_dir))
        self.music_dir.mkdir(exist_ok=True)
        self.current_track = None
        self.volume = 0.7
        self.is_playing = False
        self.playlist = []
        self.current_index = 0

        pygame.mixer.music.set_volume(self.volume)
        self._scan_music_folder()

    def _scan_music_folder(self):
        supported_formats = ['.mp3', '.ogg', '.wav', '.flac']
        self.playlist = []

        if self.music_dir.exists():
            for ext in supported_formats:
                self.playlist.extend(list(self.music_dir.glob(f'*{ext}')))

        if self.playlist:
            print(f"[MusicManager] Found {len(self.playlist)} tracks")
        else:
            print("[MusicManager] No music files found - place audio in 'music' folder")

    def play_menu_music(self):
        if not self.playlist:
            return

        try:
            if not self.is_playing:
                pygame.mixer.music.load(str(self.playlist[self.current_index]))
                pygame.mixer.music.play(-1)
                self.is_playing = True
                self.current_track = self.playlist[self.current_index].name
                print(f"[MusicManager] Now playing: {self.current_track}")
        except Exception as e:
            print(f"[MusicManager] Error: {e}")

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False

    def pause(self):
        pygame.mixer.music.pause()

    def resume(self):
        pygame.mixer.music.unpause()

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)


# ============== MINIGAME BASE CLASS ==============
class MiniGame(ABC):
    """Classe base astratta per minigiochi"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.score = 0
        self.is_game_over = False
        self.is_paused = False

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def update(self, dt: float, trackball: TrackballInput):
        pass

    @abstractmethod
    def draw(self, surface: pygame.Surface):
        pass

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def get_score(self) -> int:
        return self.score

# ============== GAME STATE ==============
class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    HIGH_SCORES = "high_scores"
    SETTINGS = "settings"
    GAME_OVER = "game_over"



class TrackballArcadeSystem:
    """Sistema principale arcade professionale con caricamento dinamico ROMs"""

    def __init__(self):
        pygame.init()

        self.config = Config()
        self.display = DisplayManager(self.config)
        self.trackball = TrackballInput(self.config.trackball_sensitivity)
        self.sound = SoundSynthesizer()
        self.music = MusicManager()
        self.high_scores = HighScoreManager()
        self.background = AnimatedBackground()
        self.highscore_input_active = False
        self.highscore_boxes = ['A', 'A', 'A']
        self.highscore_current_box = 0
        self.highscore_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        self.highscore_char_index = [0, 0, 0]  # Indici per ogni box
        self._setup_mouse_capture()

        self.state = GameState.MENU
        self.carousel = MenuCarousel("roms")  # Passa cartella roms per immagini
        self.clock = pygame.time.Clock()
        self.running = True

        self.games: List[MiniGame] = []
        self.current_game: Optional[MiniGame] = None

        self.font_large = pygame.font.Font(None, 80)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.highscore_entered_this_game = False
        self.settings_selected = 0
        self.settings_options = [
            "Trackball Sensitivity",
            "Music Volume", 
            "SFX Volume",
            "Back to Menu"
        ]

        self._load_roms()  # 🔧 NUOVO: Carica giochi dinamicamente da roms/
        self._setup_sounds()

        self.music.set_volume(self.config.music_volume)
        self.music.play_menu_music()

        self._print_welcome()










    def _load_roms(self):
        roms_dir = Path("roms")
        roms_dir.mkdir(exist_ok=True)
        
        print("[ROMS] Scanning roms/ directory...")
        loaded_count = 0
        
        # 🔧 FIX: Prepara le dipendenze da iniettare
        shared_globals = {
            'MiniGame': MiniGame,
            'TrackballInput': TrackballInput,
            'pygame': pygame,
            'math': math,
            'random': random,
            'sys': sys,
            'os': os
        }
        
        for py_file in roms_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            module_name = f"roms.{py_file.stem}"
            class_name = py_file.stem  # Usa il nome originale senza .title()
            
            try:
                # Pulisci namespace precedente
                if module_name in sys.modules:
                    del sys.modules[module_name]
                
                # 🔧 FIX: Carica con namespace condiviso
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                
                # ✅ INIETTA LE DIPENDENZE nel __dict__ del modulo
                module.__dict__.update(shared_globals)
                
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Cerca la classe del gioco
                game_class = None
                for attr_name in dir(module):
                    candidate = getattr(module, attr_name)
                    if (inspect.isclass(candidate) and 
                        issubclass(candidate, MiniGame) and 
                        candidate is not MiniGame):  # Escludi la classe base
                        game_class = candidate
                        break
                
                if game_class:
                    try:
                        # 🔧 ULTRA-FIX: Crea istanza con parametri flessibili/compatibili
                        # Prova prima con solo sound (per ROM vecchi)
                        try:
                            game_instance = game_class(sound=self.sound)
                        except TypeError as te:
                            if "missing" in str(te).lower() or "args" in str(te).lower():
                                # Fallback: passa args=None + sound + kwargs vuoti
                                game_instance = game_class(args=None, sound=self.sound)
                            else:
                                raise  # Altro errore TypeError
                        
                        # Verifica istanza valida post-init
                        if not hasattr(game_instance, 'name') or not hasattr(game_instance, 'description'):
                            raise ValueError("MiniGame mancante name/description dopo __init__")
                        if not hasattr(game_instance, 'reset') or not callable(game_instance.reset):
                            raise ValueError("MiniGame mancante metodo reset()")
                        
                        self.games.append(game_instance)
                        self.carousel.add_item(game_instance.name, game_instance.description)
                        loaded_count += 1
                        print(f"[ROMS] ✓ Loaded: {game_class.__name__} ({game_instance.name})")
                    
                    except (TypeError, ValueError) as init_error:
                        print(f"[ROMS] ✗ Init failed {game_class.__name__}: {str(init_error)}")
                        print("   💡 Fix ROM: def __init__(self, args, sound=None, **kwargs)")
                    except Exception as e:
                        print(f"[ROMS] ✗ Unexpected error {game_class.__name__}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"[ROMS] ✗ Invalid: {py_file.name} (no MiniGame subclass found)")

                    
            except Exception as e:
                print(f"[ROMS] ✗ Error loading {py_file.name}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Aggiungi opzioni sistema
        self.carousel.add_item("Settings", "Configura trackball, audio e video")
        self.carousel.add_item("Exit", "Chiudi Trackball Arcade System")
        
        print(f"[ROMS] Loaded {loaded_count} games (+2 built-in)")
        if loaded_count == 0:
            print("[ROMS] ⚠️ No ROMs! Place .py files in roms/ with class inheriting MiniGame")




    def _setup_mouse_capture(self):
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        center_x = self.config.resolution[0] // 2
        center_y = self.config.resolution[1] // 2
        pygame.mouse.set_pos(center_x, center_y)
        pygame.mouse.get_rel()
        print("[MouseCapture] Mouse captured for trackball control")

    def _print_welcome(self):
        print("\n" + "="*60)
        print("  TRACKBALL ARCADE SYSTEM - Professional ROM Edition")
        print("="*60)
        print("\nROMs loaded:", len(self.games))
        print("\nControls:")
        print("  🎯 Trackball (Mouse): Aim / Navigate")
        print("  🔴 Left Button: Fire / Select / Start ROM")
        print("  🟡 Middle Button: Pause / Settings")
        print("  🔵 Right Button: High Scores / Back / Exit Menu")
        print("  ⌨️  ESC: Exit / Return to Menu")
        print("  ⌨️  F: Toggle FPS Display")
        print("\n📁 ROMs in 'roms/' folder (*.py files)")
        print("\n" + "="*60 + "\n")

    def _setup_sounds(self):
        self.sound.create_select()
        self.sound.create_back()
        self.sound.create_blip()
        self.sound.create_pause()
        self.sound.create_shoot()
        self.sound.create_target_hit()
        self.sound.create_target_miss()
        self.sound.create_game_start()
        self.sound.create_game_over()
        self.sound.create_powerup()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            fps = self.clock.get_fps()

            events = pygame.event.get()
            self.trackball.update(events)

            self._handle_global_events(events)

            if self.state == GameState.MENU:
                self._update_menu(dt)
                self._draw_menu()
            elif self.state == GameState.PLAYING:
                self._update_game(dt)
                self._draw_game()
            elif self.state == GameState.HIGH_SCORES:
                self._update_high_scores(dt)
                self._draw_high_scores()
            elif self.state == GameState.SETTINGS:
                self._update_settings(dt)
                self._draw_settings()
            elif self.state == GameState.GAME_OVER:
                self._update_game_over(dt)
                self._draw_game_over()

            self.display.render(fps)

        self._cleanup()

    def _handle_global_events(self, events):
        """Eventi globali (chiamato PRIMA di trackball.update per catturare pressed)"""
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.MENU
                        self.music.play_menu_music()
                        self.sound.create_back().play()
                    elif self.state in [GameState.HIGH_SCORES, GameState.SETTINGS]:
                        self.state = GameState.MENU
                        self.sound.create_back().play()
                    else:
                        self.running = False
                elif event.key == pygame.K_f:
                    self.display.toggle_fps_display()


    def _update_menu(self, dt: float):
        self.background.update(dt)
        self.carousel.update(dt)

        dx, dy = self.trackball.get_delta()
        if abs(dx) > 5:
            if dx > 0:
                self.carousel.navigate(1)
                self.sound.create_blip(1).play()
            else:
                self.carousel.navigate(-1)
                self.sound.create_blip(-1).play()

        idx = self.carousel.get_current_index()
        num_games = len(self.games)

        if self.trackball.button_left_pressed:
            if idx < num_games:
                # Avvia gioco
                self.highscore_entered_this_game = False  # <-- RESET CRITICO
                self.highscore_input_active = False       # <-- PULISCI ANCHE INPUT
                self.current_game = self.games[idx]
                self.current_game.reset()
                self.state = GameState.PLAYING
                self.sound.create_game_start().play()
                self.music.stop()

            elif idx == num_games:
                # Settings
                self.state = GameState.SETTINGS
                self.settings_selected = 0
                self.sound.create_select().play()
            elif idx == num_games + 1:
                # Exit
                self.running = False

        elif self.trackball.button_right_pressed:
            if idx < num_games:
                # High scores solo per giochi
                self.state = GameState.HIGH_SCORES
                self.sound.create_select().play()

        elif self.trackball.button_middle_pressed:
            # Middle: sempre Settings (override carousel)
            self.state = GameState.SETTINGS
            self.settings_selected = 0
            self.sound.create_select().play()




    def _draw_menu(self):
        surface = self.display.virtual_surface
        self.background.draw(surface)

        title = self.font_large.render("TRACKBALL ARCADE", True, (255, 230, 0))
        for offset in [(0, 3), (3, 0), (0, -3), (-3, 0)]:
            outline = self.font_large.render("TRACKBALL ARCADE", True, (0, 0, 0))
            surface.blit(outline, outline.get_rect(center=(640 + offset[0], 60 + offset[1])))
        surface.blit(title, title.get_rect(center=(640, 60)))

        self.carousel.draw(surface, 190, 120)

        instructions = [
            "Move trackball to navigate",
            "Left button: START GAME",
            "Right button: HIGH SCORES",
            "Middle button: SETTINGS"
        ]
        y = 605
        for instr in instructions:
            text = self.font_small.render(instr, True, (200, 220, 255))
            surface.blit(text, text.get_rect(center=(640, y)))
            y += 28


    # ✅ FIX: Right button in _update_game (già corretto precedentemente)
    def _update_game(self, dt: float):
        if self.current_game is None:
            return
        
        # Middle button: pausa/riprendi
        if self.trackball.button_middle_pressed:
            if self.current_game.is_paused:
                self.current_game.resume()
            else:
                self.current_game.pause()
            self.sound.create_pause().play()
            return
        
        # Right button: ESCE SOLO SE PAUSATO (pressed per click pulito)
        if (self.trackball.button_right_pressed and 
            self.current_game.is_paused):
            self.state = GameState.MENU
            self.music.play_menu_music()
            self.sound.create_back().play()
            self.current_game = None
            return
        
        # Aggiorna solo se non pausato
        if not self.current_game.is_paused:
            self.current_game.update(dt, self.trackball)
        
        # Game over
        if self.current_game.is_game_over:
            self.state = GameState.GAME_OVER
            self.sound.create_game_over().play()



    def _draw_game(self):
        if self.current_game:
            self.current_game.draw(self.display.virtual_surface)

    def _update_high_scores(self, dt: float):
        if self.trackball.button_right_pressed or self.trackball.button_left_pressed:
            self.state = GameState.MENU
            self.sound.create_back().play()

    def _draw_high_scores(self):
        surface = self.display.virtual_surface
        self.background.draw(surface)

        title = self.font_large.render("HIGH SCORES", True, (255, 230, 0))
        surface.blit(title, title.get_rect(center=(640, 60)))

        if self.current_game or len(self.games) > 0:
            game_name = self.current_game.name if self.current_game else self.games[0].name
            scores = self.high_scores.load_scores(game_name)

            game_title = self.font_medium.render(game_name, True, (200, 220, 255))
            surface.blit(game_title, game_title.get_rect(center=(640, 140)))

            y = 210
            if scores:
                for i, entry in enumerate(scores):
                    rank_text = f"{i+1}."
                    name_text = entry['player']
                    score_text = str(entry['score'])

                    if i == 0:
                        color = (255, 215, 0)
                    elif i == 1:
                        color = (192, 192, 192)
                    elif i == 2:
                        color = (205, 127, 50)
                    else:
                        color = (200, 220, 255)

                    rank = self.font_medium.render(rank_text, True, color)
                    name = self.font_medium.render(name_text, True, color)
                    score = self.font_medium.render(score_text, True, color)

                    surface.blit(rank, (220, y))
                    surface.blit(name, (320, y))
                    surface.blit(score, (880, y))

                    y += 48
            else:
                no_scores = self.font_medium.render("No scores yet!", True, (150, 150, 150))
                surface.blit(no_scores, no_scores.get_rect(center=(640, 360)))

        back_text = self.font_small.render("Press any button to return", True, (180, 200, 220))
        surface.blit(back_text, back_text.get_rect(center=(640, 680)))









    def _update_settings(self, dt: float):
        dy = self.trackball.get_delta()[1]
        if abs(dy) > 3:
            if dy > 0:
                self.settings_selected = (self.settings_selected + 1) % len(self.settings_options)
                self.sound.create_blip(1).play()
            else:
                self.settings_selected = (self.settings_selected - 1) % len(self.settings_options)
                self.sound.create_blip(-1).play()

        dx = self.trackball.get_delta()[0]
        if abs(dx) > 3:
            if self.settings_selected == 0:
                self.config.trackball_sensitivity += 2 if dx > 0 else -2
                self.config.trackball_sensitivity = max(10, min(200, self.config.trackball_sensitivity))
                self.trackball.set_sensitivity(self.config.trackball_sensitivity)
            elif self.settings_selected == 1:
                self.config.music_volume += 0.05 if dx > 0 else -0.05
                self.config.music_volume = max(0.0, min(1.0, self.config.music_volume))
                self.music.set_volume(self.config.music_volume)
            elif self.settings_selected == 2:
                self.config.sfx_volume += 0.05 if dx > 0 else -0.05
                self.config.sfx_volume = max(0.0, min(1.0, self.config.sfx_volume))

        if self.trackball.button_left_pressed or self.trackball.button_right_pressed:
            if self.settings_selected == 3 or self.trackball.button_right_pressed:
                self.config.save()
                self.state = GameState.MENU
                self.sound.create_back().play()

    def _draw_settings(self):
        surface = self.display.virtual_surface
        self.background.draw(surface)

        title = self.font_large.render("SETTINGS", True, (255, 230, 0))
        surface.blit(title, title.get_rect(center=(640, 80)))

        y = 200
        for i, option in enumerate(self.settings_options):
            is_selected = i == self.settings_selected
            color = (255, 255, 0) if is_selected else (200, 220, 255)

            text = self.font_medium.render(option, True, color)
            text_rect = text.get_rect(center=(400, y))
            surface.blit(text, text_rect)

            if i == 0:
                value_text = f"< {int(self.config.trackball_sensitivity)} >"
            elif i == 1:
                value_text = f"< {int(self.config.music_volume * 100)}% >"
            elif i == 2:
                value_text = f"< {int(self.config.sfx_volume * 100)}% >"
            else:
                value_text = ""

            if value_text:
                value = self.font_medium.render(value_text, True, color)
                surface.blit(value, value.get_rect(center=(880, y)))

            if is_selected:
                arrow_left = self.font_medium.render("►", True, (255, 255, 0))
                surface.blit(arrow_left, (180, y - 10))

            y += 80

        help_text = self.font_small.render("Move trackball to adjust values", True, (180, 200, 220))
        surface.blit(help_text, help_text.get_rect(center=(640, 640)))

    def _update_game_over(self, dt: float):
        dx, dy = self.trackball.get_smooth_delta()
        
        if self.highscore_input_active:
            # Trackball ORIZZONTALE: dx scorre caratteri in box corrente
            if abs(dx) > 5:
                step = 1 if dx > 0 else -1
                self.highscore_char_index[self.highscore_current_box] = (
                    self.highscore_char_index[self.highscore_current_box] + step
                ) % len(self.highscore_chars)
                self.highscore_boxes[self.highscore_current_box] = self.highscore_chars[
                    self.highscore_char_index[self.highscore_current_box]
                ]
                self.sound.create_blip(self.highscore_char_index[self.highscore_current_box] % 5).play()
            
            # Trackball VERT: dy seleziona box
            if abs(dy) > 5:
                step = 1 if dy > 0 else -1
                self.highscore_current_box = (self.highscore_current_box + step) % 3
            
            if self.trackball.button_left_pressed:
                if self.highscore_current_box == 2:  # Ultimo box: salva
                    player_name = ''.join(self.highscore_boxes)
                    self.high_scores.save_score(self.current_game.name, 
                                            self.current_game.get_score(), 
                                            player_name)
                    self.sound.create_high_score().play()
                    self.highscore_input_active = False
                    self.highscore_entered_this_game = False

                    self.state = GameState.HIGH_SCORES 
                else:
                    self.highscore_current_box += 1
                    self.sound.create_select().play()
            
            if self.trackball.button_right_pressed:
                self.highscore_input_active = False
                self.sound.create_back().play()
            return  # Blocca altri input
        
        # Logica normale game over (no input attivo)
        if self.trackball.button_left_pressed:
            self.state = GameState.MENU
            self.music.play_menu_music()
        if self.trackball.button_right_pressed:
            self.highscore_entered_this_game = False
            self.highscore_input_active = False
            if self.current_game:
                self.current_game.reset()
                self.state = GameState.PLAYING
                self.sound.create_game_start().play()


    def _draw_game_over(self):
        surface = self.display.virtual_surface

        if self.current_game:
            self.current_game.draw(surface)

            overlay = pygame.Surface((1280, 720))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            surface.blit(overlay, (0, 0))

            game_over = self.font_large.render("GAME OVER", True, (255, 100, 100))
            surface.blit(game_over, game_over.get_rect(center=(640, 250)))

            score_text = self.font_medium.render(f"Final Score: {self.current_game.get_score()}",
                                                True, (255, 255, 255))
            surface.blit(score_text, score_text.get_rect(center=(640, 340)))

            score = self.current_game.get_score()
            is_new_hs = self.high_scores.is_high_score(self.current_game.name, score)

            if is_new_hs and not self.highscore_input_active and not self.highscore_entered_this_game:
                self.highscore_input_active = True
                self.highscore_entered_this_game = True
                self.highscore_boxes = ['A', 'A', 'A']
                self.highscore_current_box = 0
                self.highscore_char_index = [0, 0, 0]
                self.sound.create_high_score().play()


            if self.highscore_input_active:
                # Disegna input high score
                input_title = self.font_medium.render("ENTER YOUR INITIALS", True, (255, 215, 0))
                surface.blit(input_title, input_title.get_rect(center=(640, 410)))

                box_centers = [(480, 480), (640, 480), (800, 480)]
                for i in range(3):
                    color = (255, 255, 0) if i == self.highscore_current_box else (200, 200, 200)
                    box_surf = self.font_medium.render(self.highscore_boxes[i], True, color)
                    rect = box_surf.get_rect(center=box_centers[i])
                    pygame.draw.rect(surface, color, rect.inflate(20, 20), 3)
                    surface.blit(box_surf, rect)

                # Istruzioni
                instr1 = self.font_small.render("Trackball: Move between boxes & scroll chars", True, (200, 255, 200))
                instr2 = self.font_small.render("Left: Confirm/Next | Right: Retry Game", True, (200, 220, 255))
                surface.blit(instr1, instr1.get_rect(center=(640, 550)))
                surface.blit(instr2, instr2.get_rect(center=(640, 580)))
            else:
                if is_new_hs:
                    hs_text = self.font_medium.render("★ NEW HIGH SCORE! ★", True, (255, 215, 0))
                    surface.blit(hs_text, hs_text.get_rect(center=(640, 410)))

                retry = self.font_small.render("Right Button: RETRY", True, (200, 255, 200))
                menu = self.font_small.render("Left Button: MENU", True, (200, 220, 255))
                surface.blit(retry, retry.get_rect(center=(640, 520)))
                surface.blit(menu, menu.get_rect(center=(640, 560)))





    def _cleanup(self):
        self.config.save()
        self.music.stop()
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        pygame.quit()
        print("\nArcade system shutdown. Thanks for playing!\n")











def main():
    try:
        system = TrackballArcadeSystem()
        system.run()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()
