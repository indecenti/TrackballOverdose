import pygame
import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

class CharacterType(Enum):
    POE = 0      # AOE garlic
    THOR = 1     # Lightning from sky
    AXE_MASTER = 2  # Throwing axe
    ARCHER = 3   # Ranged attacks
    NECROMANCER = 4 # Summon minions
    PALADIN = 5  # Holy damage

class GameState(Enum):
    CHARACTER_SELECT = "character_select"
    PLAYING = "playing"
    LEVEL_UP = "level_up"
    GAME_OVER = "game_over"
    PAUSED = "paused"
    UPGRADE_SHOP = "upgrade_shop"





@dataclass
class Character:
    name: str
    description: str
    base_weapon: str
    color: Tuple[int, int, int]
    max_hp: int
    move_speed: float
    special_cooldown: float
    special_description: str
    unlock_cost: int = 0
    unlocked: bool = True

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    size: float
    shape: str = "circle"
    gravity: float = 0
    trail: bool = False
    fade_out: bool = True
    glow: bool = False
    rotation: float = 0
    rotate_speed: float = 0

@dataclass 
class DamageNumber:
    x: float
    y: float
    value: int
    life: float
    vy: float
    color: Tuple[int, int, int]
    is_critical: bool = False
    size: int = 20

@dataclass
class FloatingText:
    x: float
    y: float
    text: str
    life: float
    color: Tuple[int, int, int]
    size: int
    velocity_x: float = 0
    velocity_y: float = -40

class Projectile:
    def __init__(self, x: float, y: float, vx: float, vy: float, damage: int,
                 color: Tuple[int, int, int], size: float = 6, lifetime: float = 1.5,
                 piercing: int = 1, homing: bool = False, area: float = 1.0,
                 crit_chance: float = 0.0, owner: str = "player", shape: str = "circle",
                 rotate_speed: float = 0, glow_intensity: float = 0.5, bounce: int = 0,
                 chain_count: int = 0, slow_effect: float = 0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.base_damage = damage
        self.color = color
        self.size = max(3, size * area)
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.piercing = piercing
        self.homing = homing
        self.active = True
        self.hits = 0
        self.trail: List[Tuple[float, float, float]] = []
        self.crit_chance = crit_chance
        self.owner = owner
        self.rotation = random.uniform(0, math.pi*2)
        self.shape = shape
        self.rotate_speed = rotate_speed
        self.glow_intensity = glow_intensity
        self.glow_pulse = 0
        self.trail_enabled = shape != "circle"
        self.bounce_count = bounce
        self.max_bounce = bounce
        self.chain_count = chain_count
        self.max_chain = chain_count
        self.slow_effect = slow_effect
        self.last_hit_enemy = None
        self.spawn_time = 0
        
    def get_damage(self) -> Tuple[int, bool]:
        is_crit = random.random() < self.crit_chance
        damage = int(self.base_damage * (2.0 if is_crit else 1.0))
        return damage, is_crit
        
    def update(self, dt: float, enemies: List['Enemy'] = None):
        self.spawn_time += dt
        
        if self.homing and enemies and self.spawn_time > 0.1:
            closest = self.find_closest_enemy(enemies)
            if closest:
                dx = closest.x - self.x
                dy = closest.y - self.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    homing_force = 800 * dt
                    angle = math.atan2(dy, dx)
                    current_angle = math.atan2(self.vy, self.vx)
                    angle_diff = (angle - current_angle + math.pi) % (2*math.pi) - math.pi
                    
                    max_turn = 0.3
                    turn_amount = max(-max_turn, min(max_turn, angle_diff))
                    new_angle = current_angle + turn_amount * homing_force
                    
                    speed = math.sqrt(self.vx*self.vx + self.vy*self.vy)
                    self.vx = math.cos(new_angle) * speed
                    self.vy = math.sin(new_angle) * speed
        
        self.rotation += dt * self.rotate_speed
        self.glow_pulse = math.sin(self.lifetime * 15) * 0.3 + 0.7
        
        if self.trail_enabled:
            self.trail.append((self.x, self.y, 1.0))
            for i in range(len(self.trail)):
                self.trail[i] = (self.trail[i][0], self.trail[i][1], self.trail[i][2] - dt * 3)
            self.trail = [(x, y, life) for x, y, life in self.trail if life > 0.1]
            if len(self.trail) > 6:
                self.trail = self.trail[-6:]
            
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        
        if self.lifetime <= 0 or (self.hits >= self.piercing and self.chain_count == 0):
            self.active = False
            
        if abs(self.x - 5000) > 6000 or abs(self.y - 5000) > 6000:
            self.active = False
    
    def find_closest_enemy(self, enemies: List['Enemy']) -> Optional['Enemy']:
        closest = None
        min_dist = float('inf')
        for enemy in enemies:
            if enemy.alive and enemy != self.last_hit_enemy:
                dx = enemy.x - self.x
                dy = enemy.y - self.y
                dist = dx*dx + dy*dy
                if dist < min_dist and dist < 600*600:
                    min_dist = dist
                    closest = enemy
        return closest
    
    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float, shake_x: float, shake_y: float):
        screen_x = self.x - camera_x + shake_x
        screen_y = self.y - camera_y + shake_y
        
        # Solo disegnare se visibile
        if not (-100 <= screen_x <= 1380 and -100 <= screen_y <= 820):
            return
            
        if self.trail_enabled:
            for i, (tx, ty, life) in enumerate(self.trail):
                alpha = life * 0.7
                size = max(1, self.size * alpha * 0.5)
                trail_color = tuple(min(255, max(0, int(c * alpha))) for c in self.color)
                trail_screen_x = tx - camera_x + shake_x
                trail_screen_y = ty - camera_y + shake_y
                
                if -50 <= trail_screen_x <= 1330 and -50 <= trail_screen_y <= 770:
                    trail_surf = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
                    pygame.draw.circle(trail_surf, (*trail_color, int(alpha * 200)), 
                                     (int(size), int(size)), int(size))
                    surface.blit(trail_surf, (int(trail_screen_x - size), int(trail_screen_y - size)))
        
        glow_size = self.size * (2.0 + self.glow_pulse * 0.6)
        if glow_size > 0 and self.glow_intensity > 0:
            glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
            for i in range(3, 0, -1):
                alpha = int(80 * self.glow_intensity * (self.glow_pulse + 0.5) * (i/3))
                if alpha > 0:
                    pygame.draw.circle(glow_surf, (*self.color, alpha), 
                                     (int(glow_size), int(glow_size)), int(glow_size * (i/3)))
            surface.blit(glow_surf, (int(screen_x - glow_size), int(screen_y - glow_size)))
        
        draw_color = tuple(min(255, max(0, int(c * (1 + self.glow_pulse*0.3)))) for c in self.color)
        
        if self.shape == "circle":
            pygame.draw.circle(surface, draw_color, (int(screen_x), int(screen_y)), int(self.size))
            pygame.draw.circle(surface, (255, 255, 255), (int(screen_x), int(screen_y)), 
                             int(self.size), max(1, int(self.size*0.3)))
            
        elif self.shape == "axe":
            angle = self.rotation
            handle_length = self.size * 1.8
            handle_end_x = screen_x + math.cos(angle) * handle_length
            handle_end_y = screen_y + math.sin(angle) * handle_length
            
            pygame.draw.line(surface, (150, 100, 50), 
                           (screen_x, screen_y), (handle_end_x, handle_end_y), 
                           max(2, int(self.size*0.5)))
            
            blade_size = self.size * 1.5
            for side in [-1, 1]:
                blade_angle = angle + side * math.pi/3
                blade_tip_x = handle_end_x + math.cos(blade_angle) * blade_size
                blade_tip_y = handle_end_y + math.sin(blade_angle) * blade_size
                
                blade_points = [
                    (handle_end_x, handle_end_y),
                    (blade_tip_x, blade_tip_y),
                    (handle_end_x + math.cos(angle) * blade_size * 0.7, 
                     handle_end_y + math.sin(angle) * blade_size * 0.7)
                ]
                
                blade_color = (min(255, draw_color[0]+50), min(255, draw_color[1]+30), min(255, draw_color[2]))
                pygame.draw.polygon(surface, blade_color, blade_points)
                pygame.draw.polygon(surface, (255, 255, 200), blade_points, 1)
            
        elif self.shape == "lightning":
            for i in range(3):
                offset = (i-1) * self.size * 0.4
                lightning_color = (min(255, draw_color[0]+150), min(255, draw_color[1]+100), draw_color[2])
                
                segments = 5
                points = []
                base_x = screen_x + offset
                base_y = screen_y - self.size*1.5
                
                for seg in range(segments+1):
                    t = seg / segments
                    seg_x = base_x + math.sin(t * math.pi * 4 + self.rotation) * self.size*0.8
                    seg_y = base_y + t * self.size*3
                    points.append((seg_x, seg_y))
                
                if len(points) > 1:
                    pygame.draw.lines(surface, lightning_color, False, points, max(2, int(self.size*0.7)))
                    pygame.draw.lines(surface, (255, 255, 200), False, points, max(1, int(self.size*0.3)))
                    
        elif self.shape == "fire":
            fire_size = self.size * (1 + math.sin(self.lifetime * 15) * 0.3)
            
            pygame.draw.circle(surface, (255, 255, 180), (int(screen_x), int(screen_y)), int(fire_size*0.8))
            
            for i in range(8):
                angle = self.rotation + i * math.pi/4
                flame_length = fire_size * (0.8 + math.sin(self.lifetime * 20 + i) * 0.4)
                flame_x = screen_x + math.cos(angle) * flame_length
                flame_y = screen_y + math.sin(angle) * flame_length
                
                flame_points = [
                    (screen_x, screen_y),
                    (flame_x, flame_y),
                    (screen_x + math.cos(angle + 0.3) * flame_length*0.7, 
                     screen_y + math.sin(angle + 0.3) * flame_length*0.7)
                ]
                
                flame_color = (255, 150 + i*10, 50)
                pygame.draw.polygon(surface, flame_color, flame_points)
                
        elif self.shape == "holy":
            ring_count = 3
            for i in range(ring_count):
                ring_size = self.size * (1 - i*0.2)
                ring_alpha = 150 + int(100 * math.sin(self.lifetime * 10 + i))
                ring_color = (*draw_color, ring_alpha)
                
                ring_surf = pygame.Surface((int(ring_size*2), int(ring_size*2)), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, ring_color, 
                                 (int(ring_size), int(ring_size)), int(ring_size))
                surface.blit(ring_surf, (int(screen_x - ring_size), int(screen_y - ring_size)))
            
            cross_size = self.size * 0.8
            pygame.draw.line(surface, (255, 255, 200), 
                           (screen_x - cross_size, screen_y),
                           (screen_x + cross_size, screen_y), 3)
            pygame.draw.line(surface, (255, 255, 200), 
                           (screen_x, screen_y - cross_size),
                           (screen_x, screen_y + cross_size), 3)
            
        elif self.shape == "arrow":
            angle = math.atan2(self.vy, self.vx)
            length = self.size * 2.5
            
            tip_x = screen_x + math.cos(angle) * length
            tip_y = screen_y + math.sin(angle) * length
            
            pygame.draw.line(surface, draw_color, (screen_x, screen_y), (tip_x, tip_y), 
                           max(2, int(self.size*0.6)))
            
            # Punta della freccia
            arrow_size = self.size * 1.2
            left_angle = angle + math.pi * 0.75
            right_angle = angle - math.pi * 0.75
            
            left_x = tip_x + math.cos(left_angle) * arrow_size
            left_y = tip_y + math.sin(left_angle) * arrow_size
            right_x = tip_x + math.cos(right_angle) * arrow_size
            right_y = tip_y + math.sin(right_angle) * arrow_size
            
            pygame.draw.polygon(surface, draw_color, [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)])
            
        elif self.shape == "skull":
            # Corpo teschio
            pygame.draw.circle(surface, (200, 200, 200), (int(screen_x), int(screen_y)), int(self.size))
            
            # Occhi
            eye_size = self.size * 0.3
            pygame.draw.circle(surface, (30, 30, 30), 
                             (int(screen_x - self.size*0.4), int(screen_y - self.size*0.2)), 
                             int(eye_size))
            pygame.draw.circle(surface, (30, 30, 30), 
                             (int(screen_x + self.size*0.4), int(screen_y - self.size*0.2)), 
                             int(eye_size))
            
            # Bocca
            mouth_width = self.size * 0.6
            mouth_height = self.size * 0.4
            pygame.draw.arc(surface, (30, 30, 30), 
                          (screen_x - mouth_width/2, screen_y, mouth_width, mouth_height),
                          math.pi, 2*math.pi, 2)












class Enemy:
    def __init__(self, x: float, y: float, enemy_type: int, difficulty: float, 
                 is_boss: bool = False, game_time: float = 0):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.alive = True
        self.difficulty = difficulty
        self.is_boss = is_boss
        self.wave_number = 0
        self.wave_enemies_left = 0
        self.boss_spawned_this_wave = False
        self.last_wave_time = 0  # Inizializza a 0 invece di self.game_time
        self.pending_boss = None
        self.boss_spawn_timer = 0.0
        self.spawn_intensity = 0.0

        multiplier = 5.0 if is_boss else 1.0
        
        # Nuovi tipi di nemici
        if enemy_type == 0:  # Zombie
            self.max_hp = int(25 * difficulty * multiplier)
            self.speed = 65 + (difficulty * 6)
            self.damage = 6
            self.xp_value = 1 if not is_boss else 12
            self.color = (60, 140, 60)
            self.highlight = (100, 200, 100)
            self.size = 10 if is_boss else 8
            self.coin_drop_chance = 0.25
            self.name = "Zombie"
            
        elif enemy_type == 1:  # Bat
            self.max_hp = int(15 * difficulty * multiplier)
            self.speed = 140 + (difficulty * 10)
            self.damage = 4
            self.xp_value = 1 if not is_boss else 10
            self.color = (140, 80, 180)
            self.highlight = (180, 120, 220)
            self.size = 7 if is_boss else 5
            self.coin_drop_chance = 0.35
            self.name = "Bat"
            
        elif enemy_type == 2:  # Skeleton
            self.max_hp = int(35 * difficulty * multiplier)
            self.speed = 55 + (difficulty * 4)
            self.damage = 9
            self.xp_value = 2 if not is_boss else 18
            self.color = (200, 200, 200)
            self.highlight = (230, 230, 230)
            self.size = 12 if is_boss else 10
            self.coin_drop_chance = 0.45
            self.name = "Skeleton"
            
        elif enemy_type == 3:  # Ghost
            self.max_hp = int(30 * difficulty * multiplier)
            self.speed = 80 + (difficulty * 6)
            self.damage = 7
            self.xp_value = 2 if not is_boss else 15
            self.color = (140, 180, 255)
            self.highlight = (180, 220, 255)
            self.size = 11 if is_boss else 9
            self.coin_drop_chance = 0.35
            self.name = "Ghost"
            
        elif enemy_type == 4:  # Demon
            self.max_hp = int(60 * difficulty * multiplier)
            self.speed = 45 + difficulty * 2
            self.damage = 18
            self.xp_value = 3 if not is_boss else 25
            self.color = (180, 50, 50)
            self.highlight = (220, 80, 80)
            self.size = 15 if is_boss else 13
            self.coin_drop_chance = 0.6
            self.name = "Demon"
            
        elif enemy_type == 5:  # Slime
            self.max_hp = int(20 * difficulty * multiplier)
            self.speed = 40 + (difficulty * 3)
            self.damage = 5
            self.xp_value = 1 if not is_boss else 8
            self.color = (50, 180, 80)
            self.highlight = (80, 220, 100)
            self.size = 12 if is_boss else 10
            self.coin_drop_chance = 0.3
            self.name = "Slime"
            
        elif enemy_type == 6:  # Goblin
            self.max_hp = int(18 * difficulty * multiplier)
            self.speed = 120 + (difficulty * 8)
            self.damage = 8
            self.xp_value = 2 if not is_boss else 12
            self.color = (100, 180, 80)
            self.highlight = (140, 220, 100)
            self.size = 8 if is_boss else 6
            self.coin_drop_chance = 0.5
            self.name = "Goblin"
            
        elif enemy_type == 7:  # Mage
            self.max_hp = int(25 * difficulty * multiplier)
            self.speed = 50 + (difficulty * 3)
            self.damage = 12
            self.xp_value = 3 if not is_boss else 20
            self.color = (180, 100, 220)
            self.highlight = (220, 140, 255)
            self.size = 10 if is_boss else 8
            self.coin_drop_chance = 0.4
            self.name = "Mage"
            self.can_shoot = True
            self.shoot_cooldown = random.uniform(2, 4)
            self.shoot_timer = 0
            
        elif enemy_type == 8:  # Golem
            self.max_hp = int(80 * difficulty * multiplier)
            self.speed = 30 + (difficulty * 1)
            self.damage = 15
            self.xp_value = 4 if not is_boss else 30
            self.color = (120, 120, 140)
            self.highlight = (160, 160, 180)
            self.size = 18 if is_boss else 16
            self.coin_drop_chance = 0.7
            self.name = "Golem"
            
        elif enemy_type == 9:  # Dragon
            self.max_hp = int(100 * difficulty * multiplier)
            self.speed = 70 + (difficulty * 4)
            self.damage = 25
            self.xp_value = 5 if not is_boss else 40
            self.color = (220, 100, 50)
            self.highlight = (255, 140, 80)
            self.size = 22 if is_boss else 20
            self.coin_drop_chance = 0.8
            self.name = "Dragon"
            
        self.hp = self.max_hp
        self.hit_flash = 0
        self.knockback_vx = 0
        self.knockback_vy = 0
        self.slow_factor = 1.0
        self.attack_cooldown = 0
        self.attack_range = 35
        self.animation_time = random.uniform(0, math.pi*2)
        self.wave_time = 0
        self.pulse = 0
        self.has_died_effect = False
        
        if enemy_type == 5:  # Slime si muove a onde
            self.wave_amplitude = random.uniform(10, 20)
            self.wave_frequency = random.uniform(2, 4)
            
    def update(self, dt: float, player_x: float, player_y: float, game_time: float = 0):
        if not self.alive:
            return
            
        self.animation_time += dt * 3
        self.hit_flash = max(0, self.hit_flash - dt * 5)
        self.knockback_vx *= 0.9
        self.knockback_vy *= 0.9
        self.slow_factor = min(1.0, self.slow_factor + dt * 4)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        
        if hasattr(self, 'shoot_timer'):
            self.shoot_timer -= dt
        
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0:
            effective_speed = self.speed * self.slow_factor
            
            # Movimento speciale per alcuni nemici
            if self.type == 5:  # Slime
                self.wave_time += dt
                wave_offset = math.sin(self.wave_time * self.wave_frequency) * self.wave_amplitude * dt
                move_x = (dx/dist) * effective_speed * dt
                move_y = (dy/dist) * effective_speed * dt
                # Aggiunge movimento ondulatorio
                perp_dx = -dy
                perp_dy = dx
                perp_dist = math.sqrt(perp_dx*perp_dx + perp_dy*perp_dy)
                if perp_dist > 0:
                    move_x += (perp_dx/perp_dist) * wave_offset
                    move_y += (perp_dy/perp_dist) * wave_offset
            else:
                move_x = (dx/dist) * effective_speed * dt
                move_y = (dy/dist) * effective_speed * dt
                
            self.x += move_x + self.knockback_vx * dt
            self.y += move_y + self.knockback_vy * dt
            
        self.pulse = math.sin(self.animation_time * 2) * 0.1 + 0.9
            
    def take_damage(self, damage: int, is_crit: bool = False) -> bool:
        self.hp -= damage
        self.hit_flash = 1.2 if is_crit else 0.8
        if self.hp <= 0:
            self.alive = False
            return True
        return False
        
    def apply_slow(self, factor: float):
        self.slow_factor = min(self.slow_factor, factor)
        
    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float, shake_x: float, shake_y: float):
        if not self.alive:
            return
            
        screen_x = self.x - camera_x + shake_x
        screen_y = self.y - camera_y + shake_y
        
        # Solo disegnare se visibile
        if not (-self.size*2 <= screen_x <= 1280 + self.size*2 and 
                -self.size*2 <= screen_y <= 720 + self.size*2):
            return
            
        current_size = self.size * self.pulse
        
        # Effetto hit flash
        body_color = self.color
        if self.hit_flash > 0:
            flash_amt = int(self.hit_flash * 100)
            body_color = tuple(min(255, c + flash_amt) for c in self.color)
        
        # Disegno specifico per tipo
        if self.type == 5:  # Slime
            # Corpo slime
            pygame.draw.circle(surface, body_color, (int(screen_x), int(screen_y)), int(current_size))
            
            # Effetto bordo
            pygame.draw.circle(surface, self.highlight, (int(screen_x), int(screen_y)), 
                             int(current_size), max(2, int(current_size*0.2)))
            
            # Occhi
            eye_size = current_size * 0.25
            eye_offset = current_size * 0.4
            pygame.draw.circle(surface, (30, 30, 30), 
                             (int(screen_x - eye_offset), int(screen_y - eye_offset*0.5)), 
                             int(eye_size))
            pygame.draw.circle(surface, (30, 30, 30), 
                             (int(screen_x + eye_offset), int(screen_y - eye_offset*0.5)), 
                             int(eye_size))
            
        elif self.type == 6:  # Goblin
            # Corpo
            pygame.draw.circle(surface, body_color, (int(screen_x), int(screen_y)), int(current_size))
            
            # Cappello
            hat_height = current_size * 0.8
            hat_points = [
                (screen_x - current_size*0.7, screen_y - current_size*0.5),
                (screen_x + current_size*0.7, screen_y - current_size*0.5),
                (screen_x, screen_y - current_size*0.5 - hat_height)
            ]
            pygame.draw.polygon(surface, (100, 60, 30), hat_points)
            
        elif self.type == 7:  # Mage
            # Veste
            pygame.draw.circle(surface, body_color, (int(screen_x), int(screen_y)), int(current_size))
            
            # Cappuccio
            hood_size = current_size * 1.1
            pygame.draw.circle(surface, (40, 40, 60), (int(screen_x), int(screen_y - current_size*0.3)), 
                             int(hood_size*0.6))
            
            # Bastone
            staff_length = current_size * 1.5
            staff_angle = self.animation_time * 0.5
            staff_end_x = screen_x + math.cos(staff_angle) * staff_length
            staff_end_y = screen_y + math.sin(staff_angle) * staff_length
            pygame.draw.line(surface, (120, 80, 40), (screen_x, screen_y), 
                           (staff_end_x, staff_end_y), max(2, int(current_size*0.3)))
            
        elif self.type == 8:  # Golem
            # Corpo di pietra
            pygame.draw.circle(surface, body_color, (int(screen_x), int(screen_y)), int(current_size))
            
            # Fessure
            crack_color = (80, 80, 100)
            for i in range(3):
                crack_length = current_size * (0.6 + i*0.2)
                crack_angle = i * math.pi/1.5 + self.animation_time
                crack_x = screen_x + math.cos(crack_angle) * crack_length
                crack_y = screen_y + math.sin(crack_angle) * crack_length
                pygame.draw.line(surface, crack_color, (screen_x, screen_y), 
                               (crack_x, crack_y), 2)
                
        elif self.type == 9:  # Dragon
            # Corpo
            pygame.draw.circle(surface, body_color, (int(screen_x), int(screen_y)), int(current_size))
            
            # Ali
            wing_size = current_size * 1.5
            wing_angle = math.sin(self.animation_time * 3) * 0.5
            left_wing = [
                (screen_x, screen_y),
                (screen_x - wing_size, screen_y - wing_size*0.3),
                (screen_x - wing_size*0.7, screen_y - wing_size*0.7)
            ]
            right_wing = [
                (screen_x, screen_y),
                (screen_x + wing_size, screen_y - wing_size*0.3),
                (screen_x + wing_size*0.7, screen_y - wing_size*0.7)
            ]
            wing_color = (self.color[0]*0.7, self.color[1]*0.7, self.color[2]*0.7)
            pygame.draw.polygon(surface, wing_color, left_wing)
            pygame.draw.polygon(surface, wing_color, right_wing)
            
        else:  # Nemici base
            pygame.draw.circle(surface, body_color, (int(screen_x), int(screen_y)), int(current_size))
            
            # Occhi per alcuni tipi
            if self.type in [0, 2, 4]:
                pygame.draw.circle(surface, (40, 40, 40), 
                                 (int(screen_x - current_size*0.4), int(screen_y - current_size*0.3)), 
                                 max(1, current_size//3))
                pygame.draw.circle(surface, (40, 40, 40), 
                                 (int(screen_x + current_size*0.4), int(screen_y - current_size*0.3)), 
                                 max(1, current_size//3))
        
        # Aura per boss
        if self.is_boss:
            aura_size = current_size * 1.8
            for i in range(3):
                ring_size = aura_size * (1 - i*0.2)
                ring_width = max(2, ring_size * 0.1)
                pygame.draw.circle(surface, self.highlight, (int(screen_x), int(screen_y)), 
                                 int(ring_size), int(ring_width))
            
            # Barra HP boss
            bar_width = current_size * 4
            bar_height = 12
            bar_x = screen_x - bar_width/2
            bar_y = screen_y - current_size - 30
            
            # Background barra
            pygame.draw.rect(surface, (40, 20, 30), (bar_x, bar_y, bar_width, bar_height), 0, 6)
            
            hp_ratio = max(0, self.hp / self.max_hp)
            hp_width = bar_width * hp_ratio
            
            # Colore barra in base alla vita
            if hp_ratio > 0.6:
                hp_color = (100, 255, 120)
            elif hp_ratio > 0.3:
                hp_color = (255, 200, 80)
            else:
                hp_color = (255, 80, 80)
            
            pygame.draw.rect(surface, hp_color, (bar_x, bar_y, hp_width, bar_height), 0, 6)
            pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2, 6)
            
            # Nome boss
            font = pygame.font.Font(None, 24)
            name_text = font.render(f"{self.name} BOSS", True, (255, 200, 100))
            name_rect = name_text.get_rect(center=(screen_x, bar_y - 15))
            surface.blit(name_text, name_rect)












class AuraEffect:
    def __init__(self, x: float, y: float, radius: float, damage: int, color: Tuple[int, int, int], 
                 duration: float = 0.1, owner: str = "player", heal: bool = False, slow: float = 0):
        self.x = x
        self.y = y
        self.radius = radius
        self.damage = damage
        self.color = color
        self.duration = duration
        self.max_duration = duration
        self.active = True
        self.owner = owner
        self.animation_time = random.uniform(0, math.pi*2)
        self.heal = heal
        self.slow = slow
        self.pulse_speed = 3  # Molto lento e delicato
        
    def update(self, dt: float):
        self.duration -= dt
        self.animation_time += dt * self.pulse_speed
        if self.duration <= 0:
            self.active = False
            
    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float, shake_x: float, shake_y: float):
        screen_x = self.x - camera_x + shake_x
        screen_y = self.y - camera_y + shake_y
        
        # Solo disegnare se visibile
        if not (-self.radius*2 <= screen_x <= 1280 + self.radius*2 and 
                -self.radius*2 <= screen_y <= 720 + self.radius*2):
            return
            
        # Pulse molto leggero
        pulse = (math.sin(self.animation_time) * 0.15 + 0.85) * (self.duration / self.max_duration)
        current_radius = self.radius * pulse
        
        # Crea una superficie per l'aura
        aura_size = int(current_radius * 2)
        aura_surf = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
        
        # CENTRO: Solo un punto minimale (opzionale, commenta per rimuovere completamente)
        # center_alpha = int(30 * pulse)
        # if center_alpha > 5:
        #     pygame.draw.circle(aura_surf, (*self.color, center_alpha), 
        #                      (aura_size//2, aura_size//2), int(current_radius * 0.05))
        
        # CERCHIO ESTERNO SFUMATO - l'unico elemento visibile principale
        for i in range(6):  # Pochi passi per la sfumatura
            # Calcola raggio e alpha per ogni anello
            ring_radius = current_radius - (i * 2)  # Anelli distanziati di 2px
            ring_alpha = int(25 * (1 - i/6) * pulse)  # Trasparenza massima 25
            
            if ring_alpha > 3 and ring_radius > 0:  # Solo se visibile
                # Linea molto sottile per ogni anello
                pygame.draw.circle(aura_surf, (*self.color, ring_alpha), 
                                 (aura_size//2, aura_size//2), 
                                 int(ring_radius), 1)  # width=1 pixel
        
        # Effetto di pulso leggero sul bordo (opzionale)
        edge_pulse = abs(math.sin(self.animation_time * 1.5)) * 0.3 + 0.7
        edge_alpha = int(40 * edge_pulse * pulse)
        if edge_alpha > 5:
            pygame.draw.circle(aura_surf, (*self.color, edge_alpha), 
                             (aura_size//2, aura_size//2), 
                             int(current_radius), 1)
        
        # Disegna l'aura sulla superficie principale
        surface.blit(aura_surf, (screen_x - aura_size//2, screen_y - aura_size//2))










class XPGem:
    def __init__(self, x: float, y: float, value: int, is_big: bool = False):
        self.x = x
        self.y = y
        self.value = value
        self.collected = False
        self.vx = random.uniform(-40, 40)
        self.vy = random.uniform(-40, 40)
        
        # Colori oro brillante per l'effetto moneta
        self.color = (255, 215, 0)  # Oro
        self.highlight = (255, 255, 150)  # Giallo molto chiaro
        self.shadow = (180, 150, 30)  # Ombra per profondità
        self.glow_color = (255, 240, 100)  # Glow giallo dorato
        
        self.size = 10 + value * 4 if is_big else 8 + value * 3
        self.lifetime = 0
        self.magnetic = False
        self.rotation = random.uniform(0, math.pi*2)
        self.rotate_speed = random.uniform(3, 6)  # Rotazione più veloce
        self.is_big = is_big
        self.bob_phase = random.uniform(0, math.pi*2)  # Per l'animazione di galleggiamento
        self.bob_speed = random.uniform(2, 3)  # Velocità di galleggiamento
        self.bob_height = 3 if is_big else 2  # Altezza di galleggiamento
        self.pulse_phase = random.uniform(0, math.pi*2)
        self.pulse_speed = 4  # Velocità pulsazione
        self.original_y = y  # Posizione Y originale per il galleggiamento
        
    def update(self, dt: float, player_x: float, player_y: float, magnet_range: float):
        self.lifetime += dt
        self.rotation += dt * self.rotate_speed
        self.bob_phase += dt * self.bob_speed
        self.pulse_phase += dt * self.pulse_speed
        
        # Effetto di galleggiamento
        self.y = self.original_y + math.sin(self.bob_phase) * self.bob_height
        
        dx = player_x - self.x
        dy = player_y - self.y
        dist_sq = dx*dx + dy*dy
        
        if dist_sq < magnet_range * magnet_range:
            self.magnetic = True
            
        if self.magnetic:
            dist = math.sqrt(dist_sq)
            if dist > 0:
                pull_speed = 500 if self.is_big else 450
                self.vx = (dx/dist) * pull_speed
                self.vy = (dy/dist) * pull_speed
                
        self.x += self.vx * dt
        self.original_y += self.vy * dt  # Aggiorna anche la Y originale
        self.vx *= 0.94
        self.vy *= 0.94
        
        if dist_sq < 300:
            self.collected = True
            
    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float, shake_x: float, shake_y: float):
        screen_x = self.x - camera_x + shake_x
        screen_y = self.y - camera_y + shake_y
        
        # Solo disegnare se visibile
        if not (-self.size*2 <= screen_x <= 1280 + self.size*2 and 
                -self.size*2 <= screen_y <= 720 + self.size*2):
            return
            
        # Calcoli per le animazioni
        bob_offset = math.sin(self.bob_phase) * self.bob_height
        pulse = math.sin(self.pulse_phase) * 0.15 + 1.0  # Pulsazione leggera
        size = int(self.size * pulse)
        current_y = screen_y + bob_offset  # Applica galleggiamento
        
        # GLOW/ALONE (effetto di bagliore continuo)
        glow_pulse = (math.sin(self.lifetime * 6) * 0.5 + 0.5) * 0.4 + 0.6
        glow_size = size * 2.2
        glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
        
        # Doppio layer di glow per effetto più morbido
        for i in range(2):
            layer_size = glow_size * (1 - i * 0.2)
            layer_alpha = int(120 * glow_pulse * (1 - i * 0.5))
            pygame.draw.circle(glow_surf, (*self.glow_color[:3], layer_alpha), 
                             (int(glow_size), int(glow_size)), int(layer_size))
        
        surface.blit(glow_surf, (screen_x - glow_size, current_y - glow_size))
        
        # FORMA DELLA MONETA/GIMMA (ottagono come diamante/medaglia)
        points = []
        num_points = 8  # Forma ottagonale tipo gemma/moneta
        for i in range(num_points):
            angle = self.rotation + i * (2 * math.pi / num_points)
            # Alterna raggi per effetto a stella
            radius = size * (0.85 if i % 2 == 0 else 1.0)
            points.append((
                screen_x + math.cos(angle) * radius,
                current_y + math.sin(angle) * radius
            ))
        
        # OMBRA per profondità (lato inferiore)
        shadow_points = []
        shadow_offset = size * 0.1
        for point in points:
            shadow_points.append((point[0], point[1] + shadow_offset))
        pygame.draw.polygon(surface, self.shadow, shadow_points)
        
        # CORPO PRINCIPALE della gemma
        pygame.draw.polygon(surface, self.color, points)
        
        # BORDO ILLUMINATO
        border_width = max(1, size // 6)
        pygame.draw.polygon(surface, self.highlight, points, border_width)
        
        # RIFLESSI INTERNI (effetto metallico/lucido)
        # Riflesso principale
        inner_size = size * 0.5
        inner_offset = size * 0.2
        pygame.draw.circle(surface, (255, 255, 200, 180), 
                          (int(screen_x - inner_offset), int(current_y - inner_offset)), 
                          int(inner_size))
        
        # Punto di luce centrale
        highlight_size = size * 0.3
        pygame.draw.circle(surface, (255, 255, 255), 
                          (int(screen_x - highlight_size * 0.3), int(current_y - highlight_size * 0.3)), 
                          int(highlight_size))
        
        # EFFETTO SCINTILLIO RANDOMICO
        sparkle_chance = 0.2  # 20% di chance di scintillio
        if random.random() < sparkle_chance:
            sparkle_size = size * 0.8
            sparkle_surf = pygame.Surface((int(sparkle_size*2), int(sparkle_size*2)), pygame.SRCALPHA)
            
            # Stella a 4 punte
            for i in range(4):
                angle = i * math.pi/2
                pygame.draw.line(
                    sparkle_surf, 
                    (255, 255, 255, 220),
                    (sparkle_size + math.cos(angle) * sparkle_size * 0.3, 
                     sparkle_size + math.sin(angle) * sparkle_size * 0.3),
                    (sparkle_size + math.cos(angle) * sparkle_size, 
                     sparkle_size + math.sin(angle) * sparkle_size),
                    max(1, size // 8)
                )
            
            surface.blit(sparkle_surf, (screen_x - sparkle_size, current_y - sparkle_size))
        
        # NUMERO DEL VALORE (solo per gemme grandi)
        if self.is_big and size > 15:
            font = pygame.font.Font(None, max(16, size // 2))
            text = font.render(str(self.value), True, (255, 255, 200))
            text_rect = text.get_rect(center=(int(screen_x), int(current_y)))
            
            # Ombra del testo
            shadow_text = font.render(str(self.value), True, (100, 80, 0))
            surface.blit(shadow_text, (text_rect.x + 1, text_rect.y + 1))
            surface.blit(text, text_rect)
class Coin:
    def __init__(self, x: float, y: float, value: int, is_big: bool = False):
        self.x = x
        self.y = y
        self.value = value
        self.collected = False
        self.vx = random.uniform(-60, 60)
        self.vy = random.uniform(-100, -40)
        self.gravity = 300
        self.color = (255, 215, 0)  # Oro
        self.highlight = (255, 255, 180)  # Luce
        self.glow_color = (255, 255, 100)  # Glow giallo
        self.size = 10 if is_big else 8
        self.lifetime = 0
        self.magnetic = False
        self.bounce_count = 0
        self.rotation = random.uniform(0, math.pi*2)
        self.rotate_speed = random.uniform(5, 10)  # Rotazione veloce
        self.sparkle_time = random.uniform(0, math.pi*2)
        self.pulse_time = random.uniform(0, math.pi*2)
        self.is_big = is_big
        self.glow_intensity = 1.5 if is_big else 1.0
        
    def update(self, dt: float, player_x: float, player_y: float, magnet_range: float):
        self.lifetime += dt
        self.rotation += dt * self.rotate_speed
        self.sparkle_time += dt * 12
        self.pulse_time += dt * 4
        
        dx = player_x - self.x
        dy = player_y - self.y
        dist_sq = dx*dx + dy*dy
        
        if dist_sq < magnet_range * magnet_range:
            self.magnetic = True
            
        if self.magnetic:
            dist = math.sqrt(dist_sq)
            if dist > 0:
                pull_speed = 600 if self.is_big else 550
                self.vx = (dx/dist) * pull_speed
                self.vy = (dy/dist) * pull_speed
                self.gravity = 0
        else:
            self.vy += self.gravity * dt
            
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Rimbalzo
        if self.y > 700 and not self.magnetic and self.bounce_count < 3:
            self.y = 700
            self.vy = -self.vy * 0.6
            self.vx *= 0.85
            self.bounce_count += 1
            
        self.vx *= 0.97
        
        if dist_sq < 300:
            self.collected = True
            
    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float, shake_x: float, shake_y: float):
        screen_x = self.x - camera_x + shake_x
        screen_y = self.y - camera_y + shake_y
        
        # Solo disegnare se visibile
        if not (-self.size*4 <= screen_x <= 1280 + self.size*4 and 
                -self.size*4 <= screen_y <= 720 + self.size*4):
            return
            
        pulse = math.sin(self.pulse_time) * 0.2 + 1.0
        size = int(self.size * pulse)
        
        # Aura dorata intensa
        aura_size = size * 2.2
        aura_pulse = math.sin(self.lifetime * 6) * 0.3 + 0.7
        aura_alpha = int(120 * aura_pulse * self.glow_intensity)
        aura_surf = pygame.Surface((int(aura_size*2), int(aura_size*2)), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (*self.glow_color, aura_alpha), 
                         (int(aura_size), int(aura_size)), int(aura_size))
        surface.blit(aura_surf, (screen_x - aura_size, screen_y - aura_size))
        
        # Effetto scintillio
        if math.sin(self.sparkle_time) > 0.7:
            sparkle_size = size * 1.5
            sparkle_alpha = int(200 * math.sin(self.sparkle_time))
            sparkle_surf = pygame.Surface((int(sparkle_size*2), int(sparkle_size*2)), pygame.SRCALPHA)
            pygame.draw.circle(sparkle_surf, (255, 255, 200, sparkle_alpha), 
                             (int(sparkle_size), int(sparkle_size)), int(sparkle_size))
            surface.blit(sparkle_surf, (screen_x - sparkle_size, screen_y - sparkle_size))
        
        # Moneta rotante
        coin_radius = size
        pygame.draw.circle(surface, self.color, (int(screen_x), int(screen_y)), coin_radius)
        
        # Bordo spesso con effetto 3D
        border_width = max(3, size // 3)
        pygame.draw.circle(surface, (180, 150, 0), (int(screen_x), int(screen_y)), 
                          coin_radius, border_width)
        
        # Rilievo interno
        inner_radius = coin_radius * 0.7
        highlight_angle = self.rotation
        highlight_x = screen_x + math.cos(highlight_angle) * inner_radius * 0.3
        highlight_y = screen_y + math.sin(highlight_angle) * inner_radius * 0.3
        
        # Disegna simbolo del dollaro o cerchio interno
        pygame.draw.circle(surface, (255, 230, 100), (int(highlight_x), int(highlight_y)), 
                          int(inner_radius))
        
        # Disegna "$" stilizzato ruotato con la moneta
        font_size = int(inner_radius * 1.5)
        try:
            font = pygame.font.Font(None, font_size)
            text = font.render("$", True, (180, 150, 0))
            text_rect = text.get_rect(center=(int(screen_x), int(screen_y)))
            
            # Ruota la superficie del testo
            rotated_text = pygame.transform.rotate(text, -self.rotation * 180/math.pi)
            rotated_rect = rotated_text.get_rect(center=(int(screen_x), int(screen_y)))
            surface.blit(rotated_text, rotated_rect)
        except:
            # Fallback: disegna un cerchio con un punto
            pygame.draw.circle(surface, (180, 150, 0), (int(screen_x), int(screen_y)), 
                              int(inner_radius * 0.4))
        
        # Riflesso
        reflection_size = coin_radius * 0.4
        reflection_x = screen_x - coin_radius * 0.3
        reflection_y = screen_y - coin_radius * 0.3
        pygame.draw.circle(surface, (255, 255, 255, 150), 
                         (int(reflection_x), int(reflection_y)), int(reflection_size))

class PowerUpDrop:
    def __init__(self, x: float, y: float, powerup_type: str, level: int = 1):
        self.x = x
        self.y = y
        self.powerup_type = powerup_type
        self.level = level
        self.collected = False
        self.vx = random.uniform(-30, 30)
        self.vy = random.uniform(-50, -20)
        self.gravity = 200
        self.rotation = random.uniform(0, math.pi*2)
        self.rotate_speed = random.uniform(2, 4)
        self.lifetime = 0
        self.magnetic = False
        self.bounce_count = 0
        self.pulse_time = random.uniform(0, math.pi*2)
        
        # Colori in base al tipo
        if powerup_type == "damage":
            self.color = (255, 100, 100)
            self.symbol = "⚔"
        elif powerup_type == "fire_rate":
            self.color = (255, 180, 100)
            self.symbol = "⚡"
        elif powerup_type == "max_hp":
            self.color = (100, 255, 100)
            self.symbol = "❤"
        elif powerup_type == "move_speed":
            self.color = (220, 160, 255)
            self.symbol = "🏃"
        elif powerup_type == "crit_chance":
            self.color = (255, 255, 180)
            self.symbol = "★"
        else:
            self.color = (150, 200, 255)
            self.symbol = "?"
            
    def update(self, dt: float, player_x: float, player_y: float, magnet_range: float):
        self.lifetime += dt
        self.rotation += dt * self.rotate_speed
        self.pulse_time += dt * 5
        
        dx = player_x - self.x
        dy = player_y - self.y
        dist_sq = dx*dx + dy*dy
        
        if dist_sq < magnet_range * magnet_range:
            self.magnetic = True
            
        if self.magnetic:
            dist = math.sqrt(dist_sq)
            if dist > 0:
                pull_speed = 400
                self.vx = (dx/dist) * pull_speed
                self.vy = (dy/dist) * pull_speed
                self.gravity = 0
        else:
            self.vy += self.gravity * dt
            
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        if self.y > 700 and not self.magnetic and self.bounce_count < 2:
            self.y = 700
            self.vy = -self.vy * 0.5
            self.vx *= 0.8
            self.bounce_count += 1
            
        if dist_sq < 250:
            self.collected = True
            
    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float, shake_x: float, shake_y: float):
        screen_x = self.x - camera_x + shake_x
        screen_y = self.y - camera_y + shake_y
        
        if not (-50 <= screen_x <= 1330 and -50 <= screen_y <= 770):
            return
            
        pulse = math.sin(self.pulse_time) * 0.2 + 1.0
        size = 15 * pulse
        
        # Glow
        glow_size = size * 2.5
        glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 80), 
                         (int(glow_size), int(glow_size)), int(glow_size))
        surface.blit(glow_surf, (screen_x - glow_size, screen_y - glow_size))
        
        # Icona
        pygame.draw.circle(surface, self.color, (int(screen_x), int(screen_y)), int(size))
        pygame.draw.circle(surface, (255, 255, 255), (int(screen_x), int(screen_y)), int(size), 2)
        
        # Simbolo
        font = pygame.font.Font(None, int(size * 1.5))
        symbol = font.render(self.symbol, True, (255, 255, 255))
        symbol_rect = symbol.get_rect(center=(int(screen_x), int(screen_y)))
        surface.blit(symbol, symbol_rect)

class Weapon:
    def __init__(self, name: str, base_damage: int, fire_rate: float,
                 color: Tuple[int, int, int], projectile_count: int = 1,
                 can_evolve: bool = False, evolution_name: str = "", 
                 shape: str = "circle", is_passive: bool = False, 
                 area: float = 1.0, piercing: int = 1, homing: bool = False,
                 special_effect: str = ""):
        self.name = name
        self.base_damage = base_damage
        self.base_fire_rate = fire_rate
        self.fire_rate = fire_rate
        self.color = color
        self.projectile_count = projectile_count
        self.level = 1
        self.max_level = 8
        self.cooldown = 0
        self.piercing = piercing
        self.homing = homing
        self.area = area
        self.duration = 1.0
        self.speed = 1.0
        self.can_evolve = can_evolve
        self.evolution_name = evolution_name
        self.evolved = False
        self.shape = shape
        self.is_passive = is_passive
        self.passive_timer = 0
        self.rotate_speed = 0
        self.glow_intensity = 0.7
        self.special_effect = special_effect
        self.chain_count = 0
        self.bounce_count = 0
        self.crit_chance_bonus = 0
        self.slow_effect = 0
        
    def get_effective_fire_rate(self, stats_fire_rate_mult: float) -> float:
        return self.fire_rate / stats_fire_rate_mult

class VampireBall(MiniGame):
    def __init__(self, *args, sound=None, **kwargs):
        super().__init__("Vampire Ball",
                        "Survive endless hordes of monsters",
                        *args, **kwargs)
        self.sound = sound
        self.reset()
        
    def reset(self):
        # Reset completo di TUTTO lo stato
        self.score = 0
        self.is_game_over = False
        
        self.game_state = GameState.CHARACTER_SELECT
        self.selected_character_index = 0
        self.menu_scroll_cooldown = 0
        self.character_unlock_points = 0
                
        self.characters_data = [
            Character("POE - Garlic Aura", "Area damage around player + Expand aura",
                    "Garlic Aura", (200, 120, 80), 130, 220, 14.0,
                    "Expands garlic radius and damage for 3.5s", 0, True),  # Già True
            Character("THOR - Sky Lightning", "Lightning strikes + Storm",
                    "Lightning Bolt", (120, 200, 255), 95, 230, 14.0,
                    "Creates a storm that strikes random enemies", 100, True),  # Cambiato da False a True
            Character("AXE MASTER - Whirling Axe", "Throwing axe + Fire circle",
                    "Whirling Axe", (255, 160, 80), 105, 220, 14.0,
                    "Creates a circle of fire around player", 150, True),  # Cambiato da False a True
            Character("ARCHER - Ranged Precision", "Arrow barrage + Multishot",
                    "Bow", (120, 200, 120), 90, 240, 12.0,
                    "Fires a barrage of homing arrows", 200, True),  # Cambiato da False a True
            Character("NECROMANCER - Soul Harvest", "Summon minions + Life drain",
                    "Skull Projectile", (180, 100, 220), 85, 210, 16.0,
                    "Summons powerful minions to fight for you", 250, True),  # Cambiato da False a True
            Character("PALADIN - Holy Warrior", "Holy damage + Healing aura",
                    "Holy Water", (100, 220, 255), 140, 200, 15.0,
                    "Creates a healing and damaging holy field", 300, True)  # Cambiato da False a True
        ]
        
        self.player_x = 5000
        self.player_y = 5000
        self.player_vx = 0
        self.player_vy = 0
        self.player_target_vx = 0
        self.player_target_vy = 0
        self.max_hp = 100
        self.hp = self.max_hp
        self.invulnerable_time = 0
        self.recovery_timer = 0
        self.hp_recovery = 0
        self.shield_hp = 0
        self.max_shield = 0
        
        self.xp = 0
        self.level = 1
        self.xp_to_next_level = 30
        self.total_xp = 0
        self.xp_multiplier = 1.0
        
        self.coins = 0
        self.total_coins = 0
        self.prestige_points = 0
        
        # Reset di TUTTE le liste
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.aura_effects: List[AuraEffect] = []
        self.xp_gems: List[XPGem] = []
        self.coins_drops: List[Coin] = []
        self.powerup_drops: List[PowerUpDrop] = []
        self.particles: List[Particle] = []
        self.damage_numbers: List[DamageNumber] = []
        self.floating_texts: List[FloatingText] = []
        
        self.weapons: List[Weapon] = []
        self.powerups: Dict[str, Any] = {}
        
        self.special_charge = 0
        self.special_max = 15.0
        self.special_active = False
        self.special_duration = 0
        self.special_radius = 0
        
        self.enemy_spawn_timer = 0
        self.enemies_per_minute = 60
        self.wave_number = 1
        self.difficulty = 1.0
        self.curse_level = 0
        self.game_time = 0
        self.total_game_time = 0
        
        self.last_wave_time = 0
        self.next_boss_time = 120.0
        self.boss_spawned_this_wave = False
        
        self.level_up_choices: List[Any] = []
        self.level_up_selected = 0
        
        self.stats = {
            'damage_mult': 1.0,
            'fire_rate_mult': 1.0,
            'area_mult': 1.0,
            'speed_mult': 1.0,
            'duration_mult': 1.0,
            'amount_bonus': 0,
            'move_speed': 250,
            'magnet_range': 180,
            'crit_chance': 0.05,
            'crit_damage': 2.0,
            'luck': 0,
            'greed': 0,
            'revival_available': False,
            'armor': 0,
            'life_steal': 0.0,
            'shield_regen': 0.0,
            'exp_gain': 1.0,
            'coin_gain': 1.0,
            'projectile_speed': 1.0,
            'cooldown_reduction': 0.0
        }
        
        self.kill_count = 0
        self.combo = 0
        self.combo_timer = 0
        self.combo_max_time = 3.0
        self.max_combo = 0
        
        self.camera_shake = 0
        self.flash_effect = 0
        self.screen_flash_color = (255, 255, 255)
        
        self.reroll_count = 0
        self.max_rerolls = 1
        self.skip_count = 0
        self.max_skips = 1
        
        self.animation_time = 0
        self.background_offset_x = 0
        self.background_offset_y = 0
        self.parallax_layers = []
        self.init_parallax()
        
        self.wave_enemies_left = 0
        self.wave_total_enemies = 0
        
        self.camera_x = 0
        self.camera_y = 0
        self.camera_target_x = 0
        self.camera_target_y = 0
        self.camera_smoothness = 0.15
        
        self.trackball_sensitivity = 0.2
        self.movement_smoothing = 0.85
        
        self.garlic_damage = 6
        self.garlic_radius = 90
        self.garlic_heal = 0
        
        self.minions: List[Any] = []
        self.minion_limit = 0
        self.minion_spawn_timer = 0
        
        self.initialize_powerups_database()
        self.initialize_upgrade_shop()
        
    def init_parallax(self):
        self.parallax_layers = []
        # 3 livelli di parallasse
        for i in range(3):
            layer = {
                'speed': 0.1 + i * 0.3,
                'offset_x': random.uniform(0, 1000),
                'offset_y': random.uniform(0, 1000),
                'stars': []
            }
            # Crea stelle per questo layer
            for _ in range(50 + i * 30):
                layer['stars'].append({
                    'x': random.uniform(0, 1280),
                    'y': random.uniform(0, 720),
                    'size': random.uniform(0.5, 2.0 - i * 0.5),
                    'brightness': random.uniform(0.3, 1.0),
                    'twinkle_speed': random.uniform(0.5, 3.0)
                })
            self.parallax_layers.append(layer)
        
    def initialize_powerups_database(self):
        self.all_powerups = {
            'garlic': {
                'name': "Garlic", 
                'description': "Damages enemies around you",
                'icon_color': (200, 120, 80), 
                'max_level': 5, 
                'type': "weapon",
                'tier': 1
            },
            'lightning': {
                'name': "Lightning", 
                'description': "Strikes random enemies",
                'icon_color': (120, 200, 255), 
                'max_level': 5, 
                'type': "weapon",
                'tier': 1
            },
            'axe': {
                'name': "Axe", 
                'description': "Throws spinning axes",
                'icon_color': (255, 160, 80), 
                'max_level': 5, 
                'type': "weapon",
                'tier': 1
            },
            'fire_wand': {
                'name': "Fire Wand", 
                'description': "Shoots fire projectiles",
                'icon_color': (255, 100, 100), 
                'max_level': 5, 
                'type': "weapon",
                'tier': 2
            },
            'holy_water': {
                'name': "Holy Water", 
                'description': "Area denial circles",
                'icon_color': (100, 220, 255), 
                'max_level': 5, 
                'type': "weapon",
                'tier': 2
            },
            'bow': {
                'name': "Magic Bow", 
                'description': "Shoots homing arrows",
                'icon_color': (120, 200, 120), 
                'max_level': 5, 
                'type': "weapon",
                'tier': 2
            },
            'skull': {
                'name': "Skull Projectile", 
                'description': "Piercing skulls that bounce",
                'icon_color': (180, 100, 220), 
                'max_level': 5, 
                'type': "weapon",
                'tier': 3
            },
            'damage': {
                'name': "Damage", 
                'description': "+20% damage to all weapons",
                'icon_color': (255, 100, 100), 
                'max_level': 6, 
                'type': "stat",
                'tier': 1
            },
            'fire_rate': {
                'name': "Fire Rate", 
                'description': "+25% faster attack speed",
                'icon_color': (255, 180, 100), 
                'max_level': 6, 
                'type': "stat",
                'tier': 1
            },
            'projectiles': {
                'name': "Amount", 
                'description': "+1 projectile to all weapons",
                'icon_color': (100, 200, 255), 
                'max_level': 4, 
                'type': "stat",
                'tier': 2
            },
            'max_hp': {
                'name': "Max HP", 
                'description': "+25 maximum health",
                'icon_color': (100, 255, 100), 
                'max_level': 6, 
                'type': "stat",
                'tier': 1
            },
            'move_speed': {
                'name': "Move Speed", 
                'description': "+20% movement speed",
                'icon_color': (220, 160, 255), 
                'max_level': 6, 
                'type': "stat",
                'tier': 1
            },
            'magnet': {
                'name': "Magnet", 
                'description': "+30% pickup range",
                'icon_color': (255, 255, 120), 
                'max_level': 5, 
                'type': "stat",
                'tier': 1
            },
            'piercing': {
                'name': "Piercing", 
                'description': "+1 enemy piercing",
                'icon_color': (255, 140, 200), 
                'max_level': 3, 
                'type': "stat",
                'tier': 2
            },
            'area': {
                'name': "Area", 
                'description': "+25% weapon area",
                'icon_color': (255, 160, 60), 
                'max_level': 6, 
                'type': "stat",
                'tier': 1
            },
            'recovery': {
                'name': "HP Recovery", 
                'description': "+0.5 HP/sec regeneration",
                'icon_color': (140, 255, 140), 
                'max_level': 5, 
                'type': "stat",
                'tier': 2
            },
            'duration': {
                'name': "Duration", 
                'description': "+25% effect duration",
                'icon_color': (180, 220, 255), 
                'max_level': 6, 
                'type': "stat",
                'tier': 2
            },
            'speed': {
                'name': "Speed", 
                'description': "+20% projectile speed",
                'icon_color': (255, 180, 180), 
                'max_level': 6, 
                'type': "stat",
                'tier': 1
            },
            'crit_chance': {
                'name': "Critical", 
                'description': "+5% critical hit chance",
                'icon_color': (255, 255, 180), 
                'max_level': 5, 
                'type': "stat",
                'tier': 2
            },
            'crit_damage': {
                'name': "Critical Power", 
                'description': "+30% critical damage",
                'icon_color': (255, 180, 180), 
                'max_level': 4, 
                'type': "stat",
                'tier': 3
            },
            'armor': {
                'name': "Armor", 
                'description': "Reduce damage taken by 15%",
                'icon_color': (200, 200, 220), 
                'max_level': 5, 
                'type': "stat",
                'tier': 2
            },
            'life_steal': {
                'name': "Life Steal", 
                'description': "Heal for 8% of damage dealt",
                'icon_color': (255, 100, 180), 
                'max_level': 3, 
                'type': "special",
                'tier': 3
            },
            'revival': {
                'name': "Revival", 
                'description': "Revive once with 50% HP",
                'icon_color': (255, 100, 255), 
                'max_level': 1, 
                'type': "special",
                'tier': 3
            },
            'reroll': {
                'name': "Reroll", 
                'description': "Reroll level-up choices",
                'icon_color': (160, 220, 220), 
                'max_level': 2, 
                'type': "special",
                'tier': 2
            },
            'shield': {
                'name': "Energy Shield", 
                'description': "Gain a shield that blocks damage",
                'icon_color': (100, 180, 255), 
                'max_level': 3, 
                'type': "special",
                'tier': 2
            },
            'chain_lightning': {
                'name': "Chain Lightning", 
                'description': "Projectiles chain to nearby enemies",
                'icon_color': (180, 220, 255), 
                'max_level': 3, 
                'type': "special",
                'tier': 3
            },
            'slow_aura': {
                'name': "Slow Aura", 
                'description': "Slow enemies near you",
                'icon_color': (180, 180, 255), 
                'max_level': 3, 
                'type': "special",
                'tier': 2
            }
        }
        
    def initialize_upgrade_shop(self):
        self.upgrade_shop = {
            'damage_upgrade': {
                'name': "Damage Upgrade",
                'description': "Permanently +5% damage",
                'cost': 100,
                'max_level': 20,
                'current_level': 0,
                'stat': 'damage_mult',
                'increment': 0.05
            },
            'hp_upgrade': {
                'name': "Max HP Upgrade",
                'description': "Permanently +10 max HP",
                'cost': 80,
                'max_level': 25,
                'current_level': 0,
                'stat': 'max_hp',
                'increment': 10
            },
            'speed_upgrade': {
                'name': "Speed Upgrade",
                'description': "Permanently +3% move speed",
                'cost': 120,
                'max_level': 15,
                'current_level': 0,
                'stat': 'move_speed',
                'increment': 7.5
            },
            'luck_upgrade': {
                'name': "Luck Upgrade",
                'description': "Permanently +2% luck",
                'cost': 150,
                'max_level': 10,
                'current_level': 0,
                'stat': 'luck',
                'increment': 0.02
            },
            'greed_upgrade': {
                'name': "Greed Upgrade",
                'description': "Permanently +5% more coins",
                'cost': 200,
                'max_level': 10,
                'current_level': 0,
                'stat': 'coin_gain',
                'increment': 0.05
            },
            'exp_upgrade': {
                'name': "XP Upgrade",
                'description': "Permanently +5% more XP",
                'cost': 180,
                'max_level': 10,
                'current_level': 0,
                'stat': 'exp_gain',
                'increment': 0.05
            }
        }
            



    # Aggiungi questa mappatura nella classe
    CHARACTER_BASE_WEAPONS = {
        0: ("Garlic", "aura"),      # POE
        1: ("Lightning", "weapon"), # THOR
        2: ("Axe", "weapon"),       # AXE MASTER
        3: ("Bow", "weapon"),       # ARCHER
        4: ("Skull", "weapon"),     # NECROMANCER
        5: ("Holy Water", "weapon") # PALADIN
    }




    def get_character_base_weapon_name(self, character_index: int) -> str:
        """Restituisce il nome pulito dell'arma base del personaggio"""
        char = self.characters_data[character_index]
        weapon_map = {
            "POE - Garlic Aura": "Garlic",
            "THOR - Sky Lightning": "Lightning",
            "AXE MASTER - Whirling Axe": "Axe", 
            "ARCHER - Ranged Precision": "Bow",
            "NECROMANCER - Soul Harvest": "Skull",
            "PALADIN - Holy Warrior": "Holy Water"
        }
        return weapon_map.get(char.name, "")


    def has_garlic(self) -> bool:
        """Verifica se il personaggio ha l'arma Garlic equipaggiata"""
        for weapon in self.weapons:
            if "Garlic" in weapon.name:
                return True
        return False

    def start_game(self):
        char = self.characters_data[self.selected_character_index]
        if not char.unlocked:
            if self.character_unlock_points >= char.unlock_cost:
                self.character_unlock_points -= char.unlock_cost
                char.unlocked = True
            else:
                return
        
        self.game_state = GameState.PLAYING
        
        self.max_hp = char.max_hp
        self.hp = self.max_hp
        self.stats['move_speed'] = char.move_speed
        self.special_max = char.special_cooldown
        
        # RESETTA tutto
        self.weapons = []
        self.garlic_damage = 0
        self.garlic_radius = 0
        
        # Aggiungi Magic Wand a tutti i personaggi
        wand = Weapon("Magic Wand", 12, 0.5, (255, 120, 220), 1, 
                    True, "Advanced Wand", "circle", False, 1.0, 1, True, "homing")
        wand.homing = True
        wand.glow_intensity = 0.9
        self.weapons.append(wand)
        
        # Aggiungi l'arma base specifica del personaggio
        base_weapon_name = self.get_character_base_weapon_name(self.selected_character_index)
        
        if base_weapon_name == "Garlic":
            # Per Poe, l'aglio è un'aura speciale
            self.garlic_damage = 6
            self.garlic_radius = 90
            
            # Aggiungi Garlic come arma passiva nella lista weapons
            garlic = Weapon("Garlic", 6, 0.0, (200, 120, 80), 1,
                        True, "Enhanced Garlic", "circle", True, 1.0, 999, False, "garlic")
            garlic.is_passive = True
            garlic.level = 1
            garlic.max_level = 8
            self.weapons.append(garlic)
            
        elif base_weapon_name == "Lightning":
            lightning = Weapon("Lightning Bolt", 18, 1.1, (120, 200, 255), 1,
                            True, "Chain Lightning", "lightning", False, 1.6, 1, False, "chain")
            lightning.chain_count = 2
            lightning.glow_intensity = 0.8
            self.weapons.append(lightning)
            
        elif base_weapon_name == "Axe":
            axe = Weapon("Whirling Axe", 24, 0.7, (255, 160, 80), 2,
                        True, "Double Axe", "axe", False, 1.0, 3, False, "bounce")
            axe.bounce_count = 1
            axe.rotate_speed = 20
            axe.glow_intensity = 0.6
            self.weapons.append(axe)
            
        elif base_weapon_name == "Bow":
            bow = Weapon("Magic Bow", 14, 0.6, (120, 200, 120), 1,
                        True, "Triple Shot", "arrow", False, 1.0, 1, True, "homing")
            bow.homing = True
            bow.crit_chance_bonus = 0.1
            bow.glow_intensity = 0.9
            self.weapons.append(bow)
            
        elif base_weapon_name == "Skull":
            skull = Weapon("Skull Projectile", 20, 0.9, (180, 100, 220), 1,
                        True, "Double Skull", "skull", False, 1.2, 2, False, "pierce")
            skull.piercing = 2
            skull.bounce_count = 2
            skull.glow_intensity = 0.7
            self.weapons.append(skull)
            
        elif base_weapon_name == "Holy Water":
            holy = Weapon("Holy Water", 16, 1.4, (100, 220, 255), 1,
                        True, "Divine Rain", "holy", False, 1.4, 1, False, "heal")
            holy.glow_intensity = 0.8
            self.weapons.append(holy)
        
        if self.sound:
            self.sound.create_game_start().play()        
    def start_new_wave(self):
        self.wave_number += 1
        self.difficulty = 1.0 + (self.wave_number * 0.15) + (self.curse_level * 0.25)
        self.enemies_per_minute = 40 + self.wave_number * 8
        self.boss_spawned_this_wave = False
        
        wave_multiplier = 1 + (self.wave_number // 10) * 0.5
        self.wave_total_enemies = int(60 + self.wave_number * 15 * wave_multiplier)
        self.wave_enemies_left = self.wave_total_enemies
        
        # Mostra testo wave
        wave_colors = [
            (255, 220, 120),  # Normale
            (255, 150, 100),  # Difficile
            (255, 100, 100),  # Molto difficile
            (255, 100, 255),  # Estremo
            (100, 220, 255)   # Leggendario
        ]
        color_index = min((self.wave_number - 1) // 10, len(wave_colors) - 1)
        
        self.floating_texts.append(
            FloatingText(self.player_x, self.player_y - 50, f"WAVE {self.wave_number}", 2.5, 
                        wave_colors[color_index], 42 + min(self.wave_number // 5, 20))
        )
        
        if self.wave_number % 10 == 0:
            self.floating_texts.append(
                FloatingText(self.player_x, self.player_y - 100, "BOSS WAVE!", 3.0, 
                           (255, 100, 100), 56)
            )
            self.next_boss_time = self.game_time + 5.0
            self.camera_shake = 1.5
            self.screen_flash_color = (255, 100, 100)
            self.flash_effect = 0.8
            
        if self.sound:
            sound_index = min(9, self.wave_number // 3)
            self.sound.create_combo(sound_index).play()
            
    def update(self, dt: float, trackball):
        if self.game_state == GameState.GAME_OVER:
            return
            
        self.animation_time += dt
        self.total_game_time += dt
        
        if self.game_state == GameState.CHARACTER_SELECT:
            self.update_character_select(dt, trackball)
        elif self.game_state == GameState.LEVEL_UP:
            self.update_level_up_menu(dt, trackball)
        elif self.game_state == GameState.PLAYING:
            self.update_gameplay(dt, trackball)
        elif self.game_state == GameState.PAUSED:
            self.update_pause_menu(dt, trackball)
        elif self.game_state == GameState.UPGRADE_SHOP:
            self.update_upgrade_shop(dt, trackball)
                
    def update_character_select(self, dt: float, trackball):
        self.menu_scroll_cooldown = max(0, self.menu_scroll_cooldown - dt)
        
        dx, dy = trackball.get_delta()
        dx *= self.trackball_sensitivity * 0.2
        
        if abs(dx) > 0.05 and self.menu_scroll_cooldown <= 0:
            if dx > 0:
                self.selected_character_index = (self.selected_character_index + 1) % len(self.characters_data)
                self.menu_scroll_cooldown = 0.4
                if self.sound:
                    self.sound.create_target_hit().play()
            elif dx < 0:
                self.selected_character_index = (self.selected_character_index - 1) % len(self.characters_data)
                self.menu_scroll_cooldown = 0.4
                if self.sound:
                    self.sound.create_target_hit().play()
                    
        if trackball.button_left_pressed:
            self.start_game()
            
    def update_level_up_menu(self, dt: float, trackball):
        self.menu_scroll_cooldown = max(0, self.menu_scroll_cooldown - dt)
        
        dx, dy = trackball.get_delta()
        dx *= self.trackball_sensitivity * 0.2
        
        if abs(dx) > 0.05 and self.menu_scroll_cooldown <= 0:
            if dx > 0:
                self.level_up_selected = (self.level_up_selected + 1) % len(self.level_up_choices)
                self.menu_scroll_cooldown = 0.3
                if self.sound:
                    self.sound.create_target_hit().play()
            elif dx < 0:
                self.level_up_selected = (self.level_up_selected - 1) % len(self.level_up_choices)
                self.menu_scroll_cooldown = 0.3
                if self.sound:
                    self.sound.create_target_hit().play()
                    
        if trackball.button_left_pressed and len(self.level_up_choices) > 0:
            selected_powerup = self.level_up_choices[self.level_up_selected]
            self.apply_powerup(selected_powerup)
            self.game_state = GameState.PLAYING
            if self.sound:
                self.sound.create_combo(min(9, selected_powerup.get('level', 1))).play()
                
        if trackball.button_right_pressed and self.reroll_count < self.max_rerolls:
            self.reroll_count += 1
            self.generate_level_up_choices()
            if self.sound:
                self.sound.create_target_hit().play()
                
        if trackball.button_middle_pressed and self.skip_count < self.max_skips:
            self.skip_count += 1
            self.game_state = GameState.PLAYING
            self.xp += self.xp_to_next_level // 3
            if self.sound:
                self.sound.create_target_hit().play()

    def update_upgrade_shop(self, dt: float, trackball):
        self.menu_scroll_cooldown = max(0, self.menu_scroll_cooldown - dt)
        
        dx, dy = trackball.get_delta()
        dx *= self.trackball_sensitivity * 0.2
        
        if abs(dx) > 0.05 and self.menu_scroll_cooldown <= 0:
            self.menu_scroll_cooldown = 0.3
            if self.sound:
                self.sound.create_target_hit().play()
                    
        if trackball.button_left_pressed:
            self.game_state = GameState.PLAYING
            
        if trackball.button_right_pressed:
            self.reset()
            self.game_state = GameState.CHARACTER_SELECT
            if self.sound:
                self.sound.create_target_hit().play()
                
    def update_pause_menu(self, dt: float, trackball):
        if trackball.button_middle_pressed:
            self.game_state = GameState.PLAYING
            if self.sound:
                self.sound.create_pause().play()
            return
                
        if trackball.button_right_pressed:
            self.reset()
            self.game_state = GameState.CHARACTER_SELECT
            if self.sound:
                self.sound.create_target_hit().play()
            return
            
    def update_gameplay(self, dt: float, trackball):
        # Pausa con middle button
        if trackball.button_middle_pressed:
            self.game_state = GameState.PAUSED
            if self.sound:
                self.sound.create_pause().play()
            return
            
        self.game_time += dt
        self.camera_shake = max(0, self.camera_shake - dt * 8)
        self.flash_effect = max(0, self.flash_effect - dt * 6)
        
        # Aggiorna parallasse
        for layer in self.parallax_layers:
            layer['offset_x'] += dt * layer['speed'] * 10
            layer['offset_y'] += dt * layer['speed'] * 5
            if layer['offset_x'] > 1000:
                layer['offset_x'] -= 1000
            if layer['offset_y'] > 1000:
                layer['offset_y'] -= 1000
        
        # Camera smoothing avanzata
        self.camera_target_x = self.player_x - 640
        self.camera_target_y = self.player_y - 360
        
        # Limita camera ai bordi della mappa
        self.camera_target_x = max(0, min(10000 - 1280, self.camera_target_x))
        self.camera_target_y = max(0, min(10000 - 720, self.camera_target_y))
        
        # Interpolazione esponenziale per movimento fluido
        self.camera_x += (self.camera_target_x - self.camera_x) * self.camera_smoothness
        self.camera_y += (self.camera_target_y - self.camera_y) * self.camera_smoothness
        
        # Movimento del personaggio con trackball - molto più fluido
        dx, dy = trackball.get_delta()
        
        # Applica sensibilità e deadzone
        deadzone = 0.1
        if abs(dx) < deadzone:
            dx = 0
        if abs(dy) < deadzone:
            dy = 0
            
        dx *= self.trackball_sensitivity
        dy *= self.trackball_sensitivity
        
        # Calcola velocità target in base all'input
        target_speed = self.stats['move_speed']
        self.player_target_vx = dx * target_speed * 1.5
        self.player_target_vy = dy * target_speed * 1.5
        
        # Interpolazione esponenziale per movimento fluido
        smoothing = self.movement_smoothing
        self.player_vx = self.player_vx * smoothing + self.player_target_vx * (1 - smoothing)
        self.player_vy = self.player_vy * smoothing + self.player_target_vy * (1 - smoothing)
        
        # Applica velocità
        self.player_x += self.player_vx * dt
        self.player_y += self.player_vy * dt
        
        # Limita al bordo della mappa con margine
        margin = 50
        self.player_x = max(margin, min(10000 - margin, self.player_x))
        self.player_y = max(margin, min(10000 - margin, self.player_y))
        
        self.invulnerable_time = max(0, self.invulnerable_time - dt)
        
        # Rigenerazione HP
        self.recovery_timer += dt
        if self.recovery_timer >= 1.0 and self.hp_recovery > 0:
            self.hp = min(self.max_hp, self.hp + self.hp_recovery)
            if self.hp_recovery > 0.5:
                self.create_heal_particles(self.player_x, self.player_y, 3)
            self.recovery_timer = 0
            
        # Rigenerazione scudo
        if self.shield_hp < self.max_shield:
            self.shield_hp = min(self.max_shield, self.shield_hp + self.stats['shield_regen'] * dt)
        
        # Abilità speciale
        if trackball.button_left_pressed and self.special_charge >= self.special_max:
            self.use_special_ability()
            
        if not self.special_active and self.special_charge < self.special_max:
            self.special_charge = min(self.special_max, self.special_charge + dt * 1.5)
            
        if self.special_active:
            self.special_duration -= dt
            if self.special_duration <= 0:
                self.special_active = False
                self.special_charge = 0
                


            if self.has_garlic():
                self.update_garlic_aura(dt)
            if self.selected_character_index == 0:
                self.update_expanded_aura(dt)
            elif self.selected_character_index == 1:
                self.update_storm(dt)
            elif self.selected_character_index == 2:
                self.update_fire_circle(dt)
            elif self.selected_character_index == 3:
                self.update_arrow_barrage(dt)
            elif self.selected_character_index == 4:
                self.update_minion_summon(dt)
            elif self.selected_character_index == 5:
                self.update_holy_field(dt)
        
        # Aggiorna armi
        for weapon in self.weapons[:8]:  # Massimo 8 armi
            if weapon.is_passive:
                weapon.passive_timer += dt
                if weapon.passive_timer >= weapon.get_effective_fire_rate(self.stats['fire_rate_mult']):
                    self.fire_weapon(weapon)  # Per Garlic, questo non farà nulla
                    weapon.passive_timer = 0
            else:
                weapon.cooldown -= dt * (1 + self.stats['cooldown_reduction'])
                if weapon.cooldown <= 0:
                    self.fire_weapon(weapon)
                    effective_rate = weapon.get_effective_fire_rate(self.stats['fire_rate_mult'])
                    weapon.cooldown = effective_rate
                
        # Verifica se il personaggio ha l'arma Garlic
        if self.has_garlic():
            self.update_garlic_aura(dt)
            # Solo POE ha l'aura espansa come abilità speciale
            if self.selected_character_index == 0 and self.special_active:
                self.update_expanded_aura(dt)
            
        if self.selected_character_index == 4:
            self.update_minions(dt)
                












                    
        # SPAWN nemici - SOSTITUISCI QUESTA PARTE
        current_minute = int(self.game_time / 60)
        max_enemies = min(250, 50 + (current_minute * 30) + (self.wave_number * 20))
        
        current_enemies = len([e for e in self.enemies if e.alive])
        
        # Sistema di spawn evoluto con intensità dinamica
        spawn_intensity = min(1.0, (current_minute * 0.1) + (self.wave_number * 0.05))
        
        # Determina se è il momento di spawnare
        if current_enemies < max_enemies and self.wave_enemies_left > 0:
            self.enemy_spawn_timer += dt
            
            # Frequenza di spawn basata su intensità
            base_spawn_rate = max(0.15, 0.5 / (1 + current_minute * 0.08))
            spawn_rate = base_spawn_rate * (1.0 - (spawn_intensity * 0.3))
            
            if self.enemy_spawn_timer >= spawn_rate:
                # Determina quante ondate spawnare
                wave_count = 1
                if random.random() < 0.1 * spawn_intensity:
                    wave_count = random.randint(2, 4)  # Ondate multiple
                
                for wave_idx in range(wave_count):
                    if current_enemies < max_enemies and self.wave_enemies_left > 0:
                        # Usa il nuovo sistema di spawn
                        self.spawn_enemy_at_edge()
                        current_enemies += 1
                        self.wave_enemies_left -= 1
                
                self.enemy_spawn_timer = 0
        
        # GESTIONE WAVE - NUOVA IMPLEMENTAZIONE
        if self.wave_enemies_left <= 0 and current_enemies == 0:
            wave_cooldown = max(2.0, 5.0 - (self.wave_number * 0.1))  # Cooldown decrescente
            if self.game_time - self.last_wave_time >= wave_cooldown:
                self.start_new_wave()
                self.last_wave_time = self.game_time
        
        # GESTIONE BOSS - SOSTITUISCI QUESTA PARTE
        # Aggiorna timer del boss se presente
        if hasattr(self, 'boss_spawn_timer') and self.boss_spawn_timer > 0:
            self.boss_spawn_timer -= dt
            if self.boss_spawn_timer <= 0:
                self.spawn_prepared_boss()
        
        # Logica per iniziare lo spawn del boss
        if not self.boss_spawned_this_wave:
            # Boss ogni 5 wave o ogni 3 minuti dopo la wave 5
            should_spawn_boss = (
                (self.wave_number % 5 == 0 and self.wave_number >= 5) or
                (current_minute >= 3 and current_minute % 3 == 0 and self.wave_number >= 5)
            )
            
            if should_spawn_boss and current_enemies < max_enemies * 0.7:  # Non spawnare se troppi nemici
                self.spawn_boss()
                self.boss_spawned_this_wave = True
            














        # Aggiorna proiettili
        for projectile in self.projectiles[:300]:
            projectile.update(dt, self.enemies)
            
        self.projectiles = [p for p in self.projectiles if p.active][:300]
                
        # Aggiorna aura effects
        for aura in self.aura_effects[:60]:
            aura.update(dt)
            
        self.aura_effects = [a for a in self.aura_effects if a.active][:60]
                
        # Aggiorna nemici
        for enemy in self.enemies[:250]:
            enemy.update(dt, self.player_x, self.player_y, self.game_time)
            
        self.enemies = [e for e in self.enemies if e.alive][:250]
            
        self.check_collisions()
        
        # Aggiorna pickup
        for gem in self.xp_gems[:200]:
            gem.update(dt, self.player_x, self.player_y, self.stats['magnet_range'])
            if gem.collected:
                self.collect_xp(gem.value)
            
        self.xp_gems = [g for g in self.xp_gems if not g.collected][:200]
                
        for coin in self.coins_drops[:200]:
            coin.update(dt, self.player_x, self.player_y, self.stats['magnet_range'])
            if coin.collected:
                self.collect_coin(coin.value)
            
        self.coins_drops = [c for c in self.coins_drops if not c.collected][:200]
                
        for powerup in self.powerup_drops[:50]:
            powerup.update(dt, self.player_x, self.player_y, self.stats['magnet_range'])
            if powerup.collected:
                self.collect_powerup_drop(powerup)
            
        self.powerup_drops = [p for p in self.powerup_drops if not p.collected][:50]
                
        # Aggiorna particelle
        for particle in self.particles[:500]:
            particle.vx *= 0.92
            particle.vy += particle.gravity * dt
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.rotation += particle.rotate_speed * dt
            particle.life -= dt
            
        self.particles = [p for p in self.particles if p.life > 0][:500]
                
        # Aggiorna numeri danno
        for dmg_num in self.damage_numbers[:60]:
            dmg_num.y += dmg_num.vy * dt
            dmg_num.vy -= 100 * dt
            dmg_num.life -= dt
            
        self.damage_numbers = [d for d in self.damage_numbers if d.life > 0][:60]
                
        # Aggiorna testo fluttuante
        for text in self.floating_texts[:30]:
            text.y += text.velocity_y * dt
            text.x += text.velocity_x * dt
            text.life -= dt
            
        self.floating_texts = [t for t in self.floating_texts if t.life > 0][:30]
                
        self.combo_timer -= dt
        if self.combo_timer <= 0:
            if self.combo > self.max_combo:
                self.max_combo = self.combo
                if self.combo >= 50:
                    self.create_combo_effect()
            self.combo = 0
            
        combo_mult = 1.0 + (self.combo * 0.08)
        self.score += int(20 * dt * combo_mult * (1 + self.curse_level * 0.8))
        
        # Game over
        if self.hp <= 0:
            if self.stats['revival_available']:
                self.hp = int(self.max_hp * 0.5)
                self.stats['revival_available'] = False
                self.invulnerable_time = 3.0
                self.create_revival_effect()
                if self.sound:
                    self.sound.create_high_score().play()
            else:
                self.is_game_over = True
                self.score += self.coins * 20
                self.score += self.kill_count * 100
                self.score += self.level * 1500
                self.score += int(self.total_game_time * 10)
                self.prestige_points = self.score // 10000
                self.game_state = GameState.GAME_OVER
                if self.sound:
                    self.sound.create_game_over().play()







    def spawn_enemy_at_edge(self):
        # Sistema di wave e ondate più strutturato
        minute = int(self.game_time / 60)
        wave = self.wave_number
        
        # Calcola intensità in base al tempo
        spawn_intensity = min(1.0, (minute * 0.1) + (wave * 0.05))
        
        # Determina quanti nemici spawnare in questo frame
        spawn_count = 1
        if random.random() < 0.05 * spawn_intensity:  # Occasionalmente spawn multipli
            spawn_count = random.randint(2, 4)
        
        for _ in range(spawn_count):
            # Pattern di spawn variabili (simili a Vampire Survivors)
            spawn_pattern = random.choice([
                'edges',      # Spawn standard dai bordi
                'corners',    # Spawn dagli angoli
                'side_wave',  # Ondata da un lato specifico
                'surround'    # Circondano il giocatore
            ])
            
            if spawn_pattern == 'edges':
                # Pattern standard dai bordi (80% degli spawn)
                edge = random.randint(0, 3)
                camera_center_x = self.camera_x + 640
                camera_center_y = self.camera_y + 360
                
                if edge == 0:  # Alto
                    x = camera_center_x + random.uniform(-600, 600)
                    y = self.camera_y - random.uniform(50, 100)
                elif edge == 1:  # Destra
                    x = self.camera_x + 1280 + random.uniform(50, 100)
                    y = camera_center_y + random.uniform(-400, 400)
                elif edge == 2:  # Basso
                    x = camera_center_x + random.uniform(-600, 600)
                    y = self.camera_y + 720 + random.uniform(50, 100)
                else:  # Sinistra
                    x = self.camera_x - random.uniform(50, 100)
                    y = camera_center_y + random.uniform(-400, 400)
                    
            elif spawn_pattern == 'corners':
                # Spawn dagli angoli (10% degli spawn)
                corner = random.randint(0, 3)
                corner_offset = random.uniform(50, 150)
                
                if corner == 0:  # Alto-sinistra
                    x = self.camera_x - corner_offset
                    y = self.camera_y - corner_offset
                elif corner == 1:  # Alto-destra
                    x = self.camera_x + 1280 + corner_offset
                    y = self.camera_y - corner_offset
                elif corner == 2:  # Basso-destra
                    x = self.camera_x + 1280 + corner_offset
                    y = self.camera_y + 720 + corner_offset
                else:  # Basso-sinistra
                    x = self.camera_x - corner_offset
                    y = self.camera_y + 720 + corner_offset
                    
            elif spawn_pattern == 'side_wave':
                # Ondata da un lato specifico (5% degli spawn)
                side = random.randint(0, 3)
                base_x, base_y = self.camera_x + 640, self.camera_y + 360
                
                if side == 0:  # Da sopra
                    x = base_x + random.uniform(-400, 400)
                    y = self.camera_y - 50
                    # Crea un gruppo coeso
                    for offset in range(-2, 3):
                        if offset != 0 and random.random() < 0.7:
                            self._create_enemy_at_position(
                                x + offset * 60,
                                y,
                                wave,
                                minute
                            )
                            
                elif side == 1:  # Da destra
                    x = self.camera_x + 1280 + 50
                    y = base_y + random.uniform(-300, 300)
                    
                elif side == 2:  # Da sotto
                    x = base_x + random.uniform(-400, 400)
                    y = self.camera_y + 720 + 50
                    
                else:  # Da sinistra
                    x = self.camera_x - 50
                    y = base_y + random.uniform(-300, 300)
                    
            else:  # 'surround' - Circondano il giocatore (5% degli spawn)
                # Calcola posizioni attorno al giocatore appena fuori schermo
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(400, 600)
                
                x = self.player_x + math.cos(angle) * distance
                y = self.player_y + math.sin(angle) * distance
                
                # Assicurati che siano fuori dallo schermo
                while (self.camera_x - 100 < x < self.camera_x + 1380 and
                    self.camera_y - 100 < y < self.camera_y + 820):
                    angle = random.uniform(0, math.pi * 2)
                    distance = random.uniform(400, 600)
                    x = self.player_x + math.cos(angle) * distance
                    y = self.player_y + math.sin(angle) * distance
            
            # Limita alla mappa
            x = max(50, min(9950, x))
            y = max(50, min(9950, y))
            
            # Crea il nemico
            self._create_enemy_at_position(x, y, wave, minute)

    def _create_enemy_at_position(self, x, y, wave, minute):
        """Helper method per creare nemici con logica condivisa"""
        
        # Sistema di tier dei nemici basato su tempo e wave
        game_progress = (minute * 0.5) + (wave * 0.3)
        
        # Determina il tipo di nemico in base alla progressione
        if random.random() < 0.02 + (game_progress * 0.01):  # Elite
            enemy_types = list(range(5, 10))  # Solo nemici speciali
            is_elite = True
        elif random.random() < 0.15 + (game_progress * 0.05):  # Medium
            enemy_types = list(range(3, 8))  # Nemici medi e alcuni speciali
            is_elite = False
        else:  # Base
            enemy_types = list(range(0, 5))  # Nemici base
            is_elite = False
        
        # Aumenta probabilità di nemici forti col tempo
        if game_progress > 10:
            enemy_types = list(range(10))  # Tutti i nemici disponibili
        
        # Seleziona tipo casuale dalla lista
        enemy_type = random.choice(enemy_types)
        
        # Crea il nemico
        enemy = Enemy(x, y, enemy_type, self.difficulty, is_boss=False, game_time=self.game_time)
        
        # Applica modificatori in base al tempo e wave
        time_multiplier = 1.0 + (game_progress * 0.1)
        enemy.max_hp = int(enemy.max_hp * time_multiplier)
        enemy.hp = enemy.max_hp
        enemy.damage = int(enemy.damage * time_multiplier)
        
        # Elite enhancement
        if is_elite or random.random() < 0.05 + (game_progress * 0.02):
            enemy.max_hp = int(enemy.max_hp * 1.8)
            enemy.hp = enemy.max_hp
            enemy.speed *= 1.3
            enemy.damage = int(enemy.damage * 1.5)
            enemy.xp_value *= 2
            enemy.coin_drop_chance *= 1.5
            # Tinta rossastra per gli elite
            enemy.color = (
                min(255, enemy.color[0] + 50),
                max(0, enemy.color[1] - 30),
                max(0, enemy.color[2] - 30)
            )
            enemy.name = f"Elite {enemy.name}"
            
            # Occasionalmente aggiungi effetto particellare
            if random.random() < 0.3:
                enemy.has_particles = True
                enemy.particle_color = (255, 50, 50)
        
        # Wave bonus
        if wave % 5 == 0:  # Ogni 5 wave
            enemy.max_hp = int(enemy.max_hp * 1.2)
            enemy.hp = enemy.max_hp
            enemy.damage = int(enemy.damage * 1.1)
        
        self.enemies.append(enemy)

    def spawn_boss(self):
        """Sistema boss evoluto con pattern di Vampire Survivors"""
        
        minute = int(self.game_time / 60)
        wave = self.wave_number
        
        # Determina se spawnare un boss (ogni 5 minuti o wave 10+)
        boss_interval = max(3, 5 - (wave // 10))  # Interval diminuisce con wave alte
        should_spawn_boss = (minute % boss_interval == 0 and minute > 0) or wave % 10 == 0
        
        if not should_spawn_boss:
            return
        
        # Effetto visivo pre-boss
        self.floating_texts.append(
            FloatingText(self.player_x, self.player_y - 150, 
                        "BOSS INCOMING!", 3.0, (255, 100, 100), 48)
        )
        self.camera_shake = 1.0
        
        # Timer per lo spawn effettivo del boss
        self.boss_spawn_timer = 3.0  # 3 secondi di attesa
        
        # Memorizza i dati del boss da spawnare
        boss_data = self._prepare_boss_data(wave, minute)
        self.pending_boss = boss_data

    def _prepare_boss_data(self, wave, minute):
        """Prepara i dati del boss in base alla progressione"""
        
        # Scelta boss gerarchica
        if wave < 5:
            boss_type = 2  # Skeleton King per wave basse
        elif wave < 15:
            boss_type = random.choice([2, 4, 8])  # Mix per wave medie
        elif wave < 25:
            boss_type = random.choice([4, 8, 9])  # Più difficili
        else:
            boss_type = 9  # Sempre Dragon per wave alte
        
        # Moltiplicatori di difficoltà
        boss_multiplier = 2.5 + (minute * 0.5) + (wave * 0.2)
        
        # Posizionamento strategico
        angle = random.uniform(0, math.pi * 2)
        distance = random.uniform(600, 800)
        
        x = self.player_x + math.cos(angle) * distance
        y = self.player_y + math.sin(angle) * distance
        
        # Assicurati che non sia troppo vicino al bordo
        x = max(500, min(9500, x))
        y = max(500, min(9500, y))
        
        return {
            'type': boss_type,
            'x': x,
            'y': y,
            'multiplier': boss_multiplier,
            'wave': wave
        }

    def spawn_prepared_boss(self):
        """Spawna effettivamente il boss preparato"""
        if not self.pending_boss:
            return
        
        boss_data = self.pending_boss
        self.pending_boss = None
        
        # Crea il boss
        boss = Enemy(
            boss_data['x'], 
            boss_data['y'], 
            boss_data['type'], 
            self.difficulty * boss_data['multiplier'], 
            is_boss=True,
            game_time=self.game_time
        )
        
        # Statistiche boss
        boss.speed *= 1.2
        boss.max_hp = int(boss.max_hp * 3.0)
        boss.hp = boss.max_hp
        boss.damage = int(boss.damage * 2.0)
        boss.xp_value *= 10
        boss.coin_drop_chance = 1.0
        boss.knockback_resistance = 0.8  # Resistente a knockback
        
        # Nomi dei boss
        boss_names = {
            2: "SKELETON KING",
            4: "DEMON LORD", 
            8: "STONE GOLEM",
            9: "FIRE DRAGON"
        }
        boss_name = boss_names.get(boss_data['type'], "ANCIENT BOSS")
        
        # Wave molto alte hanno boss potenziati
        if boss_data['wave'] > 30:
            boss_name = f"ULTRA {boss_name}"
            boss.max_hp = int(boss.max_hp * 1.5)
            boss.hp = boss.max_hp
            boss.damage = int(boss.damage * 1.3)
            boss.speed *= 1.1
        
        # Effetti visivi
        self.floating_texts.append(
            FloatingText(boss.x, boss.y - 100, 
                        f"{boss_name} APPEARS!", 5.0, 
                        (255, 100, 100), 64)
        )
        
        self.camera_shake = 3.0
        self.screen_flash_color = (255, 50, 50)
        self.flash_effect = 1.0
        
        # Spawn minions del boss
        self._spawn_boss_minions(boss.x, boss.y, boss_data['wave'])
        
        self.enemies.append(boss)
        
        # Effetto sonoro
        if self.sound:
            self.sound.create_combo(9).play()

    def _spawn_boss_minions(self, boss_x, boss_y, wave):
        """Spawna i servitori del boss"""
        minion_count = min(30, 10 + (wave // 2))  # Max 30 minions
        
        # Pattern di spawn minions
        pattern = random.choice(['circle', 'lines', 'mixed'])
        
        for i in range(minion_count):
            if pattern == 'circle':
                # Cerchio attorno al boss
                angle = (i / minion_count) * math.pi * 2
                distance = random.uniform(150, 300)
                minion_x = boss_x + math.cos(angle) * distance
                minion_y = boss_y + math.sin(angle) * distance
                
            elif pattern == 'lines':
                # Linee radiali dal boss
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(100, 250)
                minion_x = boss_x + math.cos(angle) * distance
                minion_y = boss_y + math.sin(angle) * distance
                
            else:  # mixed
                # Mix casuale
                offset_angle = random.uniform(0, math.pi * 2)
                offset_dist = random.uniform(100, 350)
                minion_x = boss_x + math.cos(offset_angle) * offset_dist
                minion_y = boss_y + math.sin(offset_angle) * offset_dist
            
            # Tipo di minion basato sulla wave
            if wave < 10:
                minion_type = random.choice([0, 1, 2])  # Base
            elif wave < 20:
                minion_type = random.choice([1, 2, 3])  # Medio
            else:
                minion_type = random.choice([2, 3, 4])  # Forti
            
            minion = Enemy(minion_x, minion_y, minion_type, self.difficulty * 1.5, 
                        game_time=self.game_time)            
            # Minions leggermente potenziati se sono di wave alte
            if wave > 15:
                minion.max_hp = int(minion.max_hp * 1.3)
                minion.hp = minion.max_hp
                minion.damage = int(minion.damage * 1.2)
            
            self.enemies.append(minion)




    def update_garlic_aura(self, dt: float):
        # Trova l'arma Garlic nelle armi del giocatore
        garlic_weapon = None
        for weapon in self.weapons:
            if "Garlic" in weapon.name:
                garlic_weapon = weapon
                break
        
        if not garlic_weapon:
            return
        
        # Calcola i valori basati sul livello dell'arma
        base_damage = garlic_weapon.base_damage
        base_radius = 90
        
        # Aumenta con il livello dell'arma
        level_multiplier = 1 + (garlic_weapon.level - 1) * 0.25
        current_damage = int(base_damage * level_multiplier * self.stats['damage_mult'])
        current_radius = base_radius * level_multiplier * self.stats['area_mult']
        
        # Se è POE e ha l'abilità speciale attiva
        if self.selected_character_index == 0 and self.special_active:
            current_radius *= 2.5
            current_damage = int(current_damage * 2.2)
            heal_amount = garlic_weapon.level * 2  # POE guarisce con l'aura
        else:
            heal_amount = 0
        
        # Crea l'effetto aura
        self.aura_effects.append(AuraEffect(self.player_x, self.player_y, current_radius, 
                                            current_damage, garlic_weapon.color, 0.3))
        
        # Applica danni ai nemici
        for enemy in self.enemies:
            if not enemy.alive:
                continue
                
            dx = enemy.x - self.player_x
            dy = enemy.y - self.player_y
            dist_sq = dx*dx + dy*dy
            
            if dist_sq < current_radius * current_radius:
                if int(self.game_time * 15) % 2 == 0:
                    killed = enemy.take_damage(current_damage)
                    if killed:
                        self.on_enemy_killed(enemy)
                    else:
                        self.create_hit_particles(enemy.x, enemy.y, garlic_weapon.color, False)
                            
                    # Guarigione dall'aglio (solo per POE o se l'arma lo permette)
                    if heal_amount > 0 and self.hp < self.max_hp:
                        self.hp = min(self.max_hp, self.hp + heal_amount)
                        if heal_amount >= 2:
                            self.create_heal_particles(self.player_x, self.player_y, 1)




    def update_expanded_aura(self, dt: float):
        mega_radius = self.garlic_radius * 3.0
        mega_damage = int(self.garlic_damage * 3.0)
        
        self.aura_effects.append(AuraEffect(self.player_x, self.player_y, mega_radius, 
                                          mega_damage, (255, 200, 100), 0.2))
        
        for enemy in self.enemies:
            if not enemy.alive:
                continue
                
            dx = enemy.x - self.player_x
            dy = enemy.y - self.player_y
            dist_sq = dx*dx + dy*dy
            
            if dist_sq < mega_radius * mega_radius:
                if int(self.game_time * 20) % 2 == 0:
                    killed = enemy.take_damage(mega_damage)
                    if killed:
                        self.on_enemy_killed(enemy)
                        
    def update_storm(self, dt: float):
        if int(self.game_time * 30) % 2 == 0:
            for _ in range(8):
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(200, 600)
                strike_x = self.player_x + math.cos(angle) * distance
                strike_y = self.player_y + math.sin(angle) * distance
                
                for enemy in self.enemies:
                    if not enemy.alive:
                        continue
                        
                    dx = enemy.x - strike_x
                    dy = enemy.y - strike_y
                    if dx*dx + dy*dy < 100*100:
                        damage = int(50 * self.stats['damage_mult'])
                        killed = enemy.take_damage(damage, True)  # Sempre critico
                        if killed:
                            self.on_enemy_killed(enemy)
                        
                self.create_lightning_particles(strike_x, strike_y)
                
    def update_fire_circle(self, dt: float):
        if int(self.game_time * 30) % 1 == 0:
            for i in range(16):
                angle = self.game_time * 5 + (i / 16) * math.pi * 2
                distance = 200
                proj_x = self.player_x + math.cos(angle) * distance
                proj_y = self.player_y + math.sin(angle) * distance
                
                damage = int(30 * self.stats['damage_mult'])
                fire_proj = Projectile(proj_x, proj_y, 0, 0, damage,
                                     (255, 120, 60), 10, 0.5, 999, False, 1.4,
                                     self.stats['crit_chance'] + 0.2, "player", "fire")
                fire_proj.glow_intensity = 1.0
                self.projectiles.append(fire_proj)
                
    def update_arrow_barrage(self, dt: float):
        if int(self.game_time * 20) % 2 == 0:
            for _ in range(12):
                target = self.find_closest_enemy()
                if target:
                    angle = math.atan2(target.y - self.player_y, target.x - self.player_x)
                    speed = 800
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    
                    damage = int(25 * self.stats['damage_mult'])
                    arrow = Projectile(self.player_x, self.player_y, vx, vy,
                                     damage, (120, 200, 120), 8, 2.0, 1, True, 1.2,
                                     self.stats['crit_chance'] + 0.3, "player", "arrow")
                    arrow.homing = True
                    arrow.glow_intensity = 0.9
                    self.projectiles.append(arrow)
                    
    def update_minion_summon(self, dt: float):
        self.minion_spawn_timer += dt
        if self.minion_spawn_timer >= 0.5 and len(self.minions) < self.minion_limit:
            self.minion_spawn_timer = 0
            
            # Crea un minion
            minion = {
                'x': self.player_x + random.uniform(-50, 50),
                'y': self.player_y + random.uniform(-50, 50),
                'hp': 50 + self.level * 10,
                'max_hp': 50 + self.level * 10,
                'damage': 10 + self.level * 2,
                'size': 12,
                'color': (180, 100, 220),
                'attack_timer': 0,
                'target': None,
                'lifetime': 10.0
            }
            self.minions.append(minion)
            
    def update_minions(self, dt: float):
        for minion in self.minions[:]:
            minion['lifetime'] -= dt
            if minion['lifetime'] <= 0:
                self.minions.remove(minion)
                continue
                
            # Cerca un bersaglio
            if not minion['target'] or minion['target'] not in [e for e in self.enemies if e.alive]:
                minion['target'] = self.find_closest_enemy()
                
            if minion['target']:
                dx = minion['target'].x - minion['x']
                dy = minion['target'].y - minion['y']
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist > 0:
                    speed = 150
                    minion['x'] += (dx/dist) * speed * dt
                    minion['y'] += (dy/dist) * speed * dt
                    
                minion['attack_timer'] -= dt
                if dist < 50 and minion['attack_timer'] <= 0:
                    minion['attack_timer'] = 1.0
                    killed = minion['target'].take_damage(minion['damage'])
                    if killed:
                        self.on_enemy_killed(minion['target'])
                        minion['target'] = None
                        
    def update_holy_field(self, dt: float):
        holy_radius = 200 if self.special_active else 120
        holy_damage = int(15 * self.stats['damage_mult'])
        holy_heal = 2
        
        self.aura_effects.append(AuraEffect(self.player_x, self.player_y, holy_radius, 
                                          holy_damage, (100, 220, 255), 0.5, heal=True))
        
        for enemy in self.enemies:
            if not enemy.alive:
                continue
                
            dx = enemy.x - self.player_x
            dy = enemy.y - self.player_y
            dist_sq = dx*dx + dy*dy
            
            if dist_sq < holy_radius * holy_radius:
                if int(self.game_time * 10) % 3 == 0:
                    killed = enemy.take_damage(holy_damage)
                    if killed:
                        self.on_enemy_killed(enemy)
                        
        # Guarigione
        if int(self.game_time * 10) % 2 == 0:
            self.hp = min(self.max_hp, self.hp + holy_heal)
                
    def use_special_ability(self):
        self.special_active = True
        self.special_duration = 4.0
        self.special_charge = 0
        
        char_index = self.selected_character_index
        char = self.characters_data[char_index]
        
        self.floating_texts.append(
            FloatingText(self.player_x, self.player_y - 50,
                       char.special_description, 2.5, (255, 220, 120), 36)
        )
            
        if char_index == 0:  # POE
            self.camera_shake = 1.5
            self.screen_flash_color = (255, 200, 100)
            self.flash_effect = 0.8
            
        elif char_index == 1:  # THOR
            self.camera_shake = 2.0
            self.screen_flash_color = (120, 200, 255)
            self.flash_effect = 0.9
            
            for i in range(16):
                angle = (i / 16) * math.pi * 2
                distance = 300
                self.create_lightning_particles(
                    self.player_x + math.cos(angle) * distance,
                    self.player_y + math.sin(angle) * distance
                )
                
        elif char_index == 2:  # AXE
            self.camera_shake = 1.8
            self.screen_flash_color = (255, 160, 80)
            self.flash_effect = 0.8
            self.create_fire_explosion(self.player_x, self.player_y)
            
        elif char_index == 3:  # ARCHER
            self.camera_shake = 1.2
            self.screen_flash_color = (120, 200, 120)
            self.flash_effect = 0.7
            
        elif char_index == 4:  # NECROMANCER
            self.camera_shake = 1.5
            self.screen_flash_color = (180, 100, 220)
            self.flash_effect = 0.8
            self.minion_limit += 5
            for _ in range(3):
                self.update_minion_summon(0)  # Crea immediatamente 3 minion
                
        elif char_index == 5:  # PALADIN
            self.camera_shake = 1.0
            self.screen_flash_color = (100, 220, 255)
            self.flash_effect = 0.7
            self.hp = min(self.max_hp, self.hp + 50)
            self.create_heal_particles(self.player_x, self.player_y, 15)
            
        if self.sound:
            self.sound.create_combo(9).play()
                    
    def fire_weapon(self, weapon: Weapon):
        if "Garlic" in weapon.name:
            return 
        if len(self.enemies) == 0 and not weapon.is_passive:
            return
            
        base_damage = weapon.base_damage + (weapon.level * 4)
        damage = int(base_damage * self.stats['damage_mult'])
        proj_count = weapon.projectile_count + self.stats['amount_bonus']
        area = weapon.area * self.stats['area_mult']
        duration = weapon.duration * self.stats['duration_mult']
        speed = weapon.speed * self.stats['speed_mult'] * self.stats['projectile_speed']
        crit_chance = self.stats['crit_chance'] + weapon.crit_chance_bonus
        
        if "Wand" in weapon.name:
            closest = self.find_closest_enemy()
            if closest:
                for i in range(int(proj_count)):
                    angle_offset = (i - (proj_count-1)/2) * 0.2
                    dx = closest.x - self.player_x
                    dy = closest.y - self.player_y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        angle = math.atan2(dy, dx) + angle_offset
                        proj_speed = 550 * speed
                        vx = math.cos(angle) * proj_speed
                        vy = math.sin(angle) * proj_speed
                        
                        proj = Projectile(self.player_x, self.player_y, vx, vy,
                                        damage, weapon.color, 7 * area, duration * 1.5,
                                        weapon.piercing, weapon.homing, area,
                                        crit_chance, "player", weapon.shape,
                                        weapon.rotate_speed, weapon.glow_intensity,
                                        weapon.bounce_count, weapon.chain_count, weapon.slow_effect)
                        self.projectiles.append(proj)
                        
        elif "Lightning" in weapon.name:
            if self.enemies:
                targets = random.sample([e for e in self.enemies if e.alive], 
                                      min(3, len([e for e in self.enemies if e.alive])))
                for target in targets:
                    if target:
                        self.create_lightning_particles(target.x, target.y)
                        
                        chain_targets = [target]
                        for chain in range(weapon.chain_count):
                            if chain_targets:
                                last_target = chain_targets[-1]
                                for enemy in self.enemies:
                                    if enemy.alive and enemy not in chain_targets:
                                        dx = enemy.x - last_target.x
                                        dy = enemy.y - last_target.y
                                        if dx*dx + dy*dy < 150*150:
                                            chain_targets.append(enemy)
                                            self.create_lightning_particles(enemy.x, enemy.y)
                                            break
                        
                        for enemy in chain_targets:
                            killed = enemy.take_damage(damage)
                            if killed:
                                self.on_enemy_killed(enemy)
                                
        elif "Axe" in weapon.name:
            for i in range(int(proj_count)):
                angle = self.game_time * 3 + (i / max(1, proj_count-1)) * math.pi * 2
                axe_speed = 450 * speed
                vx = math.cos(angle) * axe_speed
                vy = math.sin(angle) * axe_speed
                
                proj = Projectile(self.player_x, self.player_y, vx, vy,
                                damage, weapon.color, 8 * area, 2.5,
                                weapon.piercing, False, area,
                                crit_chance, "player", "axe", 
                                weapon.rotate_speed + 30, weapon.glow_intensity,
                                weapon.bounce_count)
                self.projectiles.append(proj)
                
        elif "Bow" in weapon.name:
            for i in range(int(proj_count)):
                angle = random.uniform(0, math.pi * 2)
                arrow_speed = 500 * speed
                vx = math.cos(angle) * arrow_speed
                vy = math.sin(angle) * arrow_speed
                
                proj = Projectile(self.player_x, self.player_y, vx, vy,
                                damage, weapon.color, 6 * area, 3.0,
                                weapon.piercing, weapon.homing, area,
                                crit_chance + 0.15, "player", "arrow",
                                0, weapon.glow_intensity)
                proj.homing = True
                self.projectiles.append(proj)
                
        elif "Skull" in weapon.name:
            for i in range(int(proj_count)):
                angle = random.uniform(0, math.pi * 2)
                skull_speed = 400 * speed
                vx = math.cos(angle) * skull_speed
                vy = math.sin(angle) * skull_speed
                
                proj = Projectile(self.player_x, self.player_y, vx, vy,
                                damage, weapon.color, 9 * area, 4.0,
                                weapon.piercing, False, area * 1.3,
                                crit_chance, "player", "skull",
                                weapon.rotate_speed, weapon.glow_intensity,
                                weapon.bounce_count)
                self.projectiles.append(proj)
                
        elif "Holy Water" in weapon.name:
            if self.enemies:
                target = random.choice([e for e in self.enemies if e.alive])
                if target:
                    self.aura_effects.append(
                        AuraEffect(target.x, target.y, 150, damage//2,
                                 weapon.color, 5.0, heal=True)
                    )
        
        elif "Fire Wand" in weapon.name:
            for i in range(int(proj_count)):
                angle = random.uniform(0, math.pi * 2)
                fire_speed = 480 * speed
                vx = math.cos(angle) * fire_speed
                vy = math.sin(angle) * fire_speed
                
                proj = Projectile(self.player_x, self.player_y, vx, vy,
                                damage, weapon.color, 8 * area, 3.0,
                                2, True, area * 1.5,
                                crit_chance, "player", "circle", 
                                0, weapon.glow_intensity * 1.2)
                self.projectiles.append(proj)
        
        if self.sound and random.random() < 0.4:
            self.sound.create_shoot().play()
        
    def check_collisions(self):
        for projectile in self.projectiles:
            if not projectile.active:
                continue
                
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                    
                dx = projectile.x - enemy.x
                dy = projectile.y - enemy.y
                dist_sq = dx*dx + dy*dy
                collision_dist = (projectile.size + enemy.size) ** 2
                
                if dist_sq < collision_dist:
                    damage, is_crit = projectile.get_damage()
                    
                    # Effetti speciali
                    if projectile.slow_effect > 0:
                        enemy.apply_slow(projectile.slow_effect)
                    
                    # Life steal
                    if self.stats['life_steal'] > 0 and projectile.owner == "player":
                        heal_amount = int(damage * self.stats['life_steal'])
                        self.hp = min(self.max_hp, self.hp + heal_amount)
                        if heal_amount > 0:
                            self.create_heal_particles(enemy.x, enemy.y, heal_amount // 5)
                    
                    killed = enemy.take_damage(damage, is_crit)
                    projectile.hits += 1
                    projectile.last_hit_enemy = enemy
                    
                    # Knockback
                    knockback_force = 200 if is_crit else 120
                    if dist_sq > 0:
                        dist = math.sqrt(dist_sq)
                        enemy.knockback_vx = (dx/dist) * knockback_force
                        enemy.knockback_vy = (dy/dist) * knockback_force
                    
                    self.create_hit_particles(enemy.x, enemy.y, enemy.color, is_crit)
                    dmg_color = tuple(min(255, max(0, int(c))) for c in ((255, 255, 140) if is_crit else (255, 220, 160)))
                    size = 28 if is_crit else 22
                    self.damage_numbers.append(
                        DamageNumber(enemy.x, enemy.y - 15, damage,
                                   1.2, -70, dmg_color, is_crit, size)
                    )
                    
                    if killed:
                        self.on_enemy_killed(enemy)
                        
                        # Chain lightning
                        if projectile.chain_count > 0:
                            projectile.chain_count -= 1
                            projectile.hits = 0
                            # Trova nuovo bersaglio
                            new_target = None
                            min_dist = float('inf')
                            for other in self.enemies:
                                if other.alive and other != enemy:
                                    dist = (other.x - enemy.x)**2 + (other.y - enemy.y)**2
                                    if dist < min_dist and dist < 300*300:
                                        min_dist = dist
                                        new_target = other
                            if new_target:
                                dx = new_target.x - projectile.x
                                dy = new_target.y - projectile.y
                                dist = math.sqrt(dx*dx + dy*dy)
                                if dist > 0:
                                    projectile.vx = (dx/dist) * 600
                                    projectile.vy = (dy/dist) * 600
                                continue
                        
                        # Bounce
                        if projectile.bounce_count > 0:
                            projectile.bounce_count -= 1
                            projectile.hits = 0
                            # Trova nuovo bersaglio
                            new_target = None
                            min_dist = float('inf')
                            for other in self.enemies:
                                if other.alive and other != enemy:
                                    dist = (other.x - projectile.x)**2 + (other.y - projectile.y)**2
                                    if dist < min_dist and dist < 400*400:
                                        min_dist = dist
                                        new_target = other
                            if new_target:
                                dx = new_target.x - projectile.x
                                dy = new_target.y - projectile.y
                                dist = math.sqrt(dx*dx + dy*dy)
                                if dist > 0:
                                    projectile.vx = (dx/dist) * 500
                                    projectile.vy = (dy/dist) * 500
                                continue
                    else:
                        # Solo se non è stato ucciso e non rimbalza/fa chain
                        if projectile.hits >= projectile.piercing and projectile.chain_count == 0 and projectile.bounce_count == 0:
                            projectile.active = False
                            break
        
        for aura in self.aura_effects:
            if not aura.active:
                continue
                
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                    
                dx = enemy.x - aura.x
                dy = enemy.y - aura.y
                dist_sq = dx*dx + dy*dy
                
                if dist_sq < aura.radius * aura.radius:
                    if aura.heal:
                        # Aura di guarigione non danneggia
                        continue
                    
                    if int(self.game_time * 20) % 3 == 0:
                        killed = enemy.take_damage(aura.damage)
                        if killed:
                            self.on_enemy_killed(enemy)
                        if aura.slow > 0:
                            enemy.apply_slow(aura.slow)
                        
        # Collisione giocatore-nemici
        if self.invulnerable_time <= 0:
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                    
                dx = self.player_x - enemy.x
                dy = self.player_y - enemy.y
                dist_sq = dx*dx + dy*dy
                collision_dist = (30 + enemy.size) ** 2
                
                if dist_sq < collision_dist and enemy.attack_cooldown <= 0:
                    # Danni ridotti dall'armor
                    armor_reduction = self.stats['armor'] * 0.05
                    damage_reduction = 1.0 - min(0.8, armor_reduction)
                    actual_damage = max(1, int(enemy.damage * damage_reduction))
                    
                    # Prima colpisce lo scudo
                    if self.shield_hp > 0:
                        shield_damage = min(self.shield_hp, actual_damage)
                        self.shield_hp -= shield_damage
                        actual_damage -= shield_damage
                        self.create_shield_hit_particles(self.player_x, self.player_y)
                    
                    if actual_damage > 0:
                        self.take_damage(actual_damage)
                        
                    enemy.attack_cooldown = 1.5



    def on_enemy_killed(self, enemy: Enemy):
        self.kill_count += 1
        self.combo += 1
        self.combo_timer = self.combo_max_time
        
        combo_bonus = min(self.combo * 12, 200)
        score_reward = (200 + combo_bonus) * (1 + self.curse_level * 0.8)
        self.score += int(score_reward)
        
        self.create_death_particles(enemy.x, enemy.y, enemy.color, enemy.is_boss)
        
        # XP dalle gemme
        xp_mult = int(1 + self.curse_level * 0.8) * self.stats['exp_gain']
        xp_amount = max(1, enemy.xp_value * xp_mult)
        
        # Crea gemme XP
        gem_count = min(15, int(xp_amount))  # Converti in int
        gem_count = max(1, gem_count)  # Almeno 1 gemma
        for i in range(gem_count):
            offset_x = random.uniform(-25, 30)
            offset_y = random.uniform(-25, 30)
            is_big = (i == 0 and xp_amount >= 3) or (enemy.is_boss and i < 3)
            self.xp_gems.append(XPGem(enemy.x + offset_x, enemy.y + offset_y, 1, is_big))
        
        # Monete
        coin_chance = enemy.coin_drop_chance * (1.0 + self.stats['greed'] * 0.8) * self.stats['coin_gain']
        if random.random() < coin_chance:
            coin_value = random.randint(1, 3) * (1 + self.stats['greed'])
            # Crea monete
            for i in range(coin_value):
                is_big = (i == 0 and coin_value >= 2) or enemy.is_boss
                self.coins_drops.append(Coin(enemy.x, enemy.y, 1, is_big))
        
        # Powerup drop raro
        if enemy.is_boss or (random.random() < 0.05 + self.stats['luck']):
            powerup_types = ['damage', 'fire_rate', 'max_hp', 'move_speed', 'crit_chance']
            powerup_type = random.choice(powerup_types)
            self.powerup_drops.append(PowerUpDrop(enemy.x, enemy.y, powerup_type))
        
        # Bonus per boss
        if enemy.is_boss:
            # Drop extra XP
            for _ in range(8):
                offset_x = random.uniform(-40, 40)
                offset_y = random.uniform(-40, 40)
                self.xp_gems.append(XPGem(enemy.x + offset_x, enemy.y + offset_y, 3, True))
            
            # Drop extra monete
            for _ in range(12):
                offset_x = random.uniform(-40, 40)
                offset_y = random.uniform(-40, 40)
                self.coins_drops.append(Coin(enemy.x + offset_x, enemy.y + offset_y, 1, True))
            
            # Bonus XP immediato per il boss
            self.collect_xp(100)
            
            # Ricarica speciale
            self.special_charge = min(self.special_max, self.special_charge + 5)
            
            # Guarigione
            self.hp = min(self.max_hp, self.hp + 30)
            self.create_heal_particles(self.player_x, self.player_y, 10)
        
        # Combo effetti
        if self.combo % 10 == 0:
            self.create_combo_effect()
            self.camera_shake = min(1.0, self.camera_shake + 0.3)
            
        if self.sound:
            if self.combo > 1 and self.combo % 5 == 0:
                self.sound.create_combo(min(9, self.combo // 5)).play()
            else:
                self.sound.create_target_hit().play()



    def collect_xp(self, value: int):
        actual_value = int(value * self.xp_multiplier * self.stats['exp_gain'])
        self.xp += actual_value
        self.total_xp += actual_value
        
        # Bonus combo per raccolta multipla
        if value > 1:
            combo_bonus = int(value * 0.3)
            if combo_bonus > 0:
                self.xp += combo_bonus
                self.total_xp += combo_bonus
        
        # Check per level up
        while self.xp >= self.xp_to_next_level:
            self.level_up()
            
    def collect_coin(self, value: int):
        actual_value = int(value * self.stats['coin_gain'])
        self.coins += actual_value
        self.total_coins += actual_value
        # Le monete danno anche un po' di XP
        self.collect_xp(value // 2)

        if self.sound and random.random() < 0.3:
            self.sound.create_target_hit().play()
            
    def collect_powerup_drop(self, powerup_drop: PowerUpDrop):
        # Applica il powerup temporaneo
        if powerup_drop.powerup_type == 'damage':
            self.stats['damage_mult'] *= 1.2
            self.floating_texts.append(FloatingText(self.player_x, self.player_y - 50,
                                                   "DAMAGE BOOST!", 2.0, (255, 100, 100), 28))
        elif powerup_drop.powerup_type == 'fire_rate':
            self.stats['fire_rate_mult'] *= 1.25
            self.floating_texts.append(FloatingText(self.player_x, self.player_y - 50,
                                                   "SPEED BOOST!", 2.0, (255, 180, 100), 28))
        elif powerup_drop.powerup_type == 'max_hp':
            self.max_hp += 25
            self.hp += 25
            self.floating_texts.append(FloatingText(self.player_x, self.player_y - 50,
                                                   "HP BOOST!", 2.0, (100, 255, 100), 28))
        elif powerup_drop.powerup_type == 'move_speed':
            self.stats['move_speed'] *= 1.2
            self.floating_texts.append(FloatingText(self.player_x, self.player_y - 50,
                                                   "SPEED BOOST!", 2.0, (220, 160, 255), 28))
        elif powerup_drop.powerup_type == 'crit_chance':
            self.stats['crit_chance'] += 0.1
            self.floating_texts.append(FloatingText(self.player_x, self.player_y - 50,
                                                   "CRIT BOOST!", 2.0, (255, 255, 180), 28))
            
        self.camera_shake = 0.3
        if self.sound:
            self.sound.create_combo(5).play()
            
    def level_up(self):
        self.xp -= self.xp_to_next_level
        self.level += 1
        
        # Formula XP esponenziale: i primi livelli sono veloci, poi diventano più difficili
        base_xp = 30
        growth_factor = 1.45  # Fattore di crescita
        self.xp_to_next_level = int(base_xp * (growth_factor ** (self.level - 1)))
        
        self.flash_effect = 0.9
        self.screen_flash_color = (100, 200, 255)
        self.generate_level_up_choices()
        self.game_state = GameState.LEVEL_UP
        
        if self.sound:
            self.sound.create_target_hit().play()
                
    def generate_level_up_choices(self):
        available = []
        
        # 1. Ottieni l'arma base del personaggio corrente
        base_weapon_name = self.get_character_base_weapon_name(self.selected_character_index)
        
        # 2. Upgrade per armi già possedute
        weapon_choices = []
        for weapon in self.weapons:
            if weapon.level < weapon.max_level:
                weapon_data = {
                    'type': 'weapon',
                    'name': f"Upgrade {weapon.name}",
                    'description': f"Level {weapon.level + 1}: +30% damage, +stats",
                    'icon_color': weapon.color,
                    'max_level': weapon.max_level,
                    'level': weapon.level,
                    'weapon_ref': weapon
                }
                weapon_choices.append(weapon_data)
        
        if len(self.weapons) < 8:
            new_weapons = ["Garlic", "Lightning", "Axe", "Fire Wand", "Holy Water", "Bow", "Skull"]
            
            # Rimuovi le armi già possedute
            for weapon in self.weapons:
                weapon_name = weapon.name
                clean_name = weapon_name.replace("Magic ", "").split()[0]
                if clean_name in new_weapons:
                    new_weapons.remove(clean_name)
            
            # Assicurati di rimuovere l'arma base del personaggio corrente
            # (anche se non è nella lista weapons per qualche motivo)
            if base_weapon_name in new_weapons:
                new_weapons.remove(base_weapon_name)
            
            if new_weapons:
                weapon_name = random.choice(new_weapons)
                
                # Crea l'arma appropriata
                if weapon_name == "Garlic":
                    weapon_ref = Weapon("Garlic", 6, 0.0, (200, 120, 80), 1,
                                    True, "Enhanced Garlic", "circle", True, 1.0, 999, False, "garlic")
                    weapon_ref.is_passive = True
                    weapon_ref.area = 1.0
                    weapon_ref.glow_intensity = 0.5
                elif weapon_name == "Lightning":
                    weapon_ref = Weapon("Lightning", 18, 1.1, (120, 200, 255), 1, False, "", "lightning")
                    weapon_ref.area = 1.6
                    weapon_ref.glow_intensity = 0.8
                    weapon_ref.chain_count = 2
                elif weapon_name == "Axe":
                    weapon_ref = Weapon("Axe", 24, 0.7, (255, 160, 80), 2, False, "", "axe")
                    weapon_ref.rotate_speed = 20
                    weapon_ref.glow_intensity = 0.6
                    weapon_ref.bounce_count = 1
                elif weapon_name == "Fire Wand":
                    weapon_ref = Weapon("Fire Wand", 14, 0.6, (255, 100, 100), 1, False, "", "circle")
                    weapon_ref.homing = True
                    weapon_ref.glow_intensity = 0.9
                elif weapon_name == "Holy Water":
                    weapon_ref = Weapon("Holy Water", 30, 1.4, (100, 220, 255), 1, False, "", "circle")
                    weapon_ref.glow_intensity = 0.7
                elif weapon_name == "Bow":
                    weapon_ref = Weapon("Magic Bow", 14, 0.6, (120, 200, 120), 1, False, "", "arrow")
                    weapon_ref.homing = True
                    weapon_ref.crit_chance_bonus = 0.1
                    weapon_ref.glow_intensity = 0.9
                elif weapon_name == "Skull":
                    weapon_ref = Weapon("Skull Projectile", 20, 0.9, (180, 100, 220), 1, False, "", "skull")
                    weapon_ref.piercing = 2
                    weapon_ref.bounce_count = 2
                    weapon_ref.glow_intensity = 0.7
                
                weapon_data = {
                    'type': 'weapon',
                    'name': f"Unlock {weapon_name}",
                    'description': "New weapon: " + weapon_name,
                    'icon_color': weapon_ref.color,
                    'max_level': 1,
                    'level': 0,
                    'weapon_ref': weapon_ref
                }
                weapon_choices.append(weapon_data)
        
        if weapon_choices:
            available.append(random.choice(weapon_choices))
        
        # Stat powerups
        stat_powerups = []
        for key, powerup_data in self.all_powerups.items():
            if key in ['garlic', 'lightning', 'axe', 'fire_wand', 'holy_water', 'bow', 'skull']:
                continue
                
            if key not in self.powerups:
                powerup = powerup_data.copy()
                powerup['level'] = 0
                stat_powerups.append(powerup)
            elif self.powerups[key]['level'] < self.powerups[key]['max_level']:
                powerup = self.powerups[key].copy()
                stat_powerups.append(powerup)
        
        # Ordina per tier
        stat_powerups.sort(key=lambda x: x.get('tier', 1))
        
        if len(stat_powerups) >= 2:
            # Prendi 2 powerup, preferendo quelli di tier più basso
            selected_stats = []
            weights = [3 if p.get('tier', 1) == 1 else 2 if p.get('tier', 1) == 2 else 1 for p in stat_powerups]
            if sum(weights) > 0:
                selected_stats = random.choices(stat_powerups, weights=weights, k=min(2, len(stat_powerups)))
            available.extend(selected_stats)
        elif stat_powerups:
            available.extend(stat_powerups)
        
        if len(available) > 0:
            num_choices = min(4, len(available))
            self.level_up_choices = random.sample(available, num_choices)
            self.level_up_selected = 0
        else:
            self.level_up_choices = []
            self.game_state = GameState.PLAYING
            
    def apply_powerup(self, powerup_data: dict):
        if powerup_data['type'] == "weapon":
            if 'weapon_ref' in powerup_data:
                weapon = powerup_data['weapon_ref']
                if "Unlock" in powerup_data['name']:
                    self.weapons.append(weapon)
                else:
                    for w in self.weapons:
                        if w.name == powerup_data['name'].replace("Upgrade ", ""):
                            w.level += 1
                            w.base_damage = int(w.base_damage * 1.3)
                            
                        # Upgrade specifici per ogni tipo di arma
                            # Sostituisci la parte per Garlic nell'apply_powerup:
                            if "Garlic" in w.name:
                                # Per tutti i personaggi, l'aglio è un'aura passiva
                                w.area *= 1.25
                                w.base_damage = int(w.base_damage * 1.3)
                                # Solo POE ha guarigione al livello 3
                                if self.selected_character_index == 0 and w.level >= 3:
                                    w.glow_intensity += 0.3
                            elif "Lightning" in w.name:
                                w.area *= 1.2
                                if w.level >= 4:
                                    w.chain_count += 1
                            elif "Axe" in w.name:
                                w.projectile_count += 0.8
                                if w.level >= 3:
                                    w.bounce_count += 1
                            elif "Bow" in w.name:
                                w.crit_chance_bonus += 0.05
                                if w.level >= 4:
                                    w.homing = True
                            elif "Skull" in w.name:
                                w.piercing += 1
                                if w.level >= 3:
                                    w.bounce_count += 1
                            elif "Holy Water" in w.name:
                                w.area *= 1.3
                                if w.level >= 4:
                                    w.glow_intensity += 0.2
                            elif "Fire Wand" in w.name:
                                w.homing = True
                                if w.level >= 3:
                                    w.projectile_count += 1
                            elif "Magic Wand" in w.name:
                                w.homing = True
                                if w.level >= 4:
                                    w.projectile_count += 1
                            break
        else:
            key = powerup_data['name'].lower().replace(" ", "_")
            if key not in self.powerups:
                self.powerups[key] = powerup_data.copy()
            
            target_powerup = self.powerups[key]
            target_powerup['level'] = target_powerup.get('level', 0) + 1
            
            if key == "damage":
                self.stats['damage_mult'] *= 1.2
            elif key == "fire_rate":
                self.stats['fire_rate_mult'] *= 1.25
            elif key == "amount":
                self.stats['amount_bonus'] += 1
            elif key == "max_hp":
                self.max_hp += 25
                self.hp += 25
            elif key == "move_speed":
                self.stats['move_speed'] *= 1.2
            elif key == "magnet":
                self.stats['magnet_range'] *= 1.3
            elif key == "piercing":
                for weapon in self.weapons:
                    if not weapon.is_passive:
                        weapon.piercing += 1
            elif key == "area":
                self.stats['area_mult'] *= 1.25
            elif key == "recovery":
                self.hp_recovery += 0.5
            elif key == "duration":
                self.stats['duration_mult'] *= 1.25
            elif key == "speed":
                self.stats['speed_mult'] *= 1.2
                self.stats['projectile_speed'] *= 1.1
            elif key == "critical":
                self.stats['crit_chance'] += 0.05
            elif key == "critical_power":
                self.stats['crit_damage'] += 0.3
            elif key == "armor":
                self.stats['armor'] += 3
            elif key == "life_steal":
                self.stats['life_steal'] += 0.08
            elif key == "revival":
                self.stats['revival_available'] = True
            elif key == "reroll":
                self.max_rerolls += 1
            elif key == "shield":
                self.max_shield += 25
                self.shield_hp = self.max_shield
                self.stats['shield_regen'] += 0.5
            elif key == "chain_lightning":
                for weapon in self.weapons:
                    if "Lightning" in weapon.name:
                        weapon.chain_count += 1
            elif key == "slow_aura":
                self.aura_effects.append(AuraEffect(self.player_x, self.player_y, 150, 0,
                                                  (180, 180, 255), 5.0, slow=0.5))
                
    def take_damage(self, damage: int):
        self.hp -= damage
        self.invulnerable_time = 1.5
        self.camera_shake = 0.8
        
        self.create_hit_particles(self.player_x, self.player_y, (255, 100, 100), False)
        self.damage_numbers.append(
            DamageNumber(self.player_x, self.player_y - 25, damage,
                       1.5, -80, (255, 60, 60), False, 24)
        )
        
        if self.sound:
            self.sound.create_target_hit().play()
            
    def find_closest_enemy(self) -> Optional[Enemy]:
        closest = None
        min_dist = float('inf')
        for enemy in self.enemies:
            if enemy.alive:
                dx = enemy.x - self.player_x
                dy = enemy.y - self.player_y
                dist = dx*dx + dy*dy
                if dist < min_dist:
                    min_dist = dist
                    closest = enemy
        return closest
            
    def create_hit_particles(self, x: float, y: float, color: Tuple[int, int, int], is_crit: bool):
        count = 15 if is_crit else 8
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(200, 350) if is_crit else random.uniform(100, 200)
            self.particles.append(
                Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                        0.8 if is_crit else 0.5, 0.8 if is_crit else 0.5,
                        color, random.uniform(5, 10) if is_crit else random.uniform(3, 7),
                        gravity=80, trail=True)
            )
            
    def create_heal_particles(self, x: float, y: float, count: int):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 150)
            self.particles.append(
                Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                        1.0, 1.0, (100, 255, 100), random.uniform(4, 8),
                        gravity=-50, trail=True, fade_out=True, glow=True)
            )
            
    def create_shield_hit_particles(self, x: float, y: float):
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(150, 250)
            self.particles.append(
                Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                        0.7, 0.7, (100, 180, 255), random.uniform(4, 7),
                        gravity=0, trail=True, fade_out=True, glow=True)
            )
            
    def create_death_particles(self, x: float, y: float, color: Tuple[int, int, int], is_boss: bool):
        count = 50 if is_boss else 25
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(250, 500) if is_boss else random.uniform(120, 300)
            size = random.uniform(8, 15) if is_boss else random.uniform(4, 9)
            self.particles.append(
                Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                        2.5 if is_boss else 1.5, 2.5 if is_boss else 1.5,
                        color, size, gravity=150, trail=True, fade_out=True)
            )
            
    def create_combo_effect(self):
        for i in range(20):
            angle = (i / 20) * math.pi * 2
            speed = 300
            color = (255, 255, 100) if self.combo < 25 else (255, 150, 50) if self.combo < 50 else (255, 50, 50)
            self.particles.append(
                Particle(self.player_x, self.player_y,
                        math.cos(angle) * speed, math.sin(angle) * speed,
                        1.5, 1.5, color, 8, gravity=0, trail=True, glow=True)
            )
            
    def create_lightning_particles(self, x: float, y: float):
        for i in range(8):
            offset_x = random.uniform(-30, 30)
            offset_y = random.uniform(-30, 30)
            for j in range(10):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(150, 300)
                self.particles.append(
                    Particle(x + offset_x, y + offset_y, 
                            math.cos(angle) * speed, math.sin(angle) * speed,
                            0.6, 0.6, (140, 200, 255), random.uniform(4, 8),
                            gravity=0, trail=True, glow=True)
                )
                
    def create_fire_explosion(self, x: float, y: float):
        for _ in range(40):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(200, 400)
            self.particles.append(
                Particle(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                        1.2, 1.2, (255, 120, 60), random.uniform(6, 12),
                        gravity=100, trail=True, fade_out=True)
            )
            
    def create_revival_effect(self):
        for i in range(60):
            angle = (i / 60) * math.pi * 2
            speed = 300
            self.particles.append(
                Particle(self.player_x, self.player_y,
                        math.cos(angle) * speed, math.sin(angle) * speed,
                        3.0, 3.0, (255, 100, 255), 10, gravity=0, trail=True, glow=True)
            )
            
    def draw(self, surface: pygame.Surface):
        if self.game_state == GameState.CHARACTER_SELECT:
            self.draw_character_select(surface)
        elif self.game_state == GameState.LEVEL_UP:
            self.draw_gameplay(surface)
            self.draw_level_up_menu(surface)
        elif self.game_state == GameState.PLAYING:
            self.draw_gameplay(surface)
        elif self.game_state == GameState.PAUSED:
            self.draw_gameplay(surface)
            self.draw_pause_menu(surface)
        elif self.game_state == GameState.GAME_OVER:
            self.draw_gameplay(surface)
            self.draw_game_over(surface)
        elif self.game_state == GameState.UPGRADE_SHOP:
            self.draw_upgrade_shop(surface)








    def draw_character_select(self, surface: pygame.Surface):
        surface.fill((15, 20, 35))
        
        # Effetto stelle parallasse nel menu
        for i, layer in enumerate(self.parallax_layers):
            for star in layer['stars']:
                twinkle = math.sin(self.animation_time * star['twinkle_speed']) * 0.3 + 0.7
                brightness = int(150 * star['brightness'] * twinkle * (1 - i * 0.3))
                star_x = (star['x'] + layer['offset_x']) % 1280
                star_y = (star['y'] + layer['offset_y']) % 720
                pygame.draw.circle(surface, (brightness, brightness, brightness), 
                                (int(star_x), int(star_y)), int(star['size']))
        
        # Effetto particelle per personaggi sbloccati
        if self.characters_data[self.selected_character_index].unlocked:
            for _ in range(3):
                angle = random.random() * math.pi * 2
                radius = random.randint(50, 120)
                particle_x = 640 + math.cos(angle) * radius
                particle_y = 400 + math.sin(angle) * radius
                size = random.randint(2, 5)
                alpha = int(abs(math.sin(self.animation_time * 3)) * 100)
                color = self.characters_data[self.selected_character_index].color
                particle_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (*color, alpha), (size, size), size)
                surface.blit(particle_surf, (particle_x - size, particle_y - size))
        
        title = "VAMPIRE SURVIVORS CLONE"
        self.draw_text_outlined(surface, title, 640, 70, 64, (220, 100, 100), (40, 20, 20), 3)
        
        subtitle = "CHOOSE YOUR SURVIVOR"
        self.draw_text_outlined(surface, subtitle, 640, 130, 36, (240, 200, 200), (40, 30, 30), 2)
        
        char_spacing = 420
        start_x = 640 - (min(3, len(self.characters_data)) - 1) * char_spacing / 2
        
        for i in range(min(3, len(self.characters_data))):
            char_index = (self.selected_character_index + i - 1) % len(self.characters_data)
            if char_index < 0:
                char_index += len(self.characters_data)
                
            char = self.characters_data[char_index]
            x = int(start_x + i * char_spacing)
            y = 400
            
            is_selected = char_index == self.selected_character_index
            is_unlocked = char.unlocked
            
            scale = 1.0
            if is_selected:
                pulse = math.sin(self.animation_time * 6) * 0.15 + 1.15
                scale = pulse
                float_offset = math.sin(self.animation_time * 3) * 10
            else:
                scale = 0.85
                float_offset = math.sin(self.animation_time * 2 + i) * 3
                
            y += float_offset
            
            box_size = int(380 * scale)
            if is_unlocked:
                box_color = tuple(min(255, int(c * 1.4)) for c in char.color) if is_selected else (60, 65, 85)
                border_color = (255, 255, 255) if is_selected else (140, 150, 180)
            else:
                box_color = (40, 45, 60)
                border_color = (80, 90, 110)
            border_width = 8 if is_selected else 4
            
            box_rect = pygame.Rect(x - box_size//2, y - box_size//2, box_size, box_size)
            
            # Background con gradiente
            pygame.draw.rect(surface, box_color, box_rect, 0, 25)
            
            # Effetto glow per selezionato
            if is_selected:
                glow_rect = pygame.Rect(x - box_size//2 - 10, y - box_size//2 - 10, 
                                    box_size + 20, box_size + 20)
                pygame.draw.rect(surface, (*char.color, 50), glow_rect, 0, 30)
            
            pygame.draw.rect(surface, border_color, box_rect, border_width, 25)
            
            # Icona personaggio dettagliata
            icon_size = int(80 * scale)  # Cambiato da char_size a icon_size
            char_y = y - 70 + float_offset
            
            if char_index == 0:  # POE - Il Vampiro Elegante
                # Mantello fluttuante
                cloak_wave = math.sin(self.animation_time * 4 + i) * 0.3
                points = [
                    (x - icon_size*0.8, char_y + icon_size*0.3),
                    (x - icon_size*1.2, char_y - icon_size*0.5 + cloak_wave * 20),
                    (x, char_y - icon_size*0.8),
                    (x + icon_size*1.2, char_y - icon_size*0.5 - cloak_wave * 20),
                    (x + icon_size*0.8, char_y + icon_size*0.3)
                ]
                pygame.draw.polygon(surface, (100, 20, 40), points)
                
                # Corpo
                pygame.draw.circle(surface, (220, 200, 180), (x, char_y - icon_size*0.2), icon_size*0.4)
                
                # Occhi rossi luminosi
                eye_glow = abs(math.sin(self.animation_time * 5)) * 50 + 150
                for eye_x in [-1, 1]:
                    pygame.draw.circle(surface, (eye_glow, 20, 20), 
                                    (x + eye_x * icon_size*0.2, char_y - icon_size*0.25), 
                                    icon_size*0.12)
                    pygame.draw.circle(surface, (255, 255, 255), 
                                    (x + eye_x * icon_size*0.2, char_y - icon_size*0.25), 
                                    icon_size*0.04)
                
                # Zanne pulsanti
                fang_size = icon_size * 0.15 * (0.8 + 0.4 * abs(math.sin(self.animation_time * 3)))
                for fang_x in [-1, 1]:
                    fang_points = [
                        (x + fang_x * icon_size*0.15, char_y - icon_size*0.05),
                        (x + fang_x * icon_size*0.25, char_y),
                        (x + fang_x * icon_size*0.15, char_y + icon_size*0.05)
                    ]
                    pygame.draw.polygon(surface, (255, 255, 255), fang_points)
                    
                # Particelle di sangue
                for _ in range(5):
                    blood_x = x + random.randint(-30, 30)
                    blood_y = char_y + random.randint(-20, 20)
                    blood_size = random.randint(1, 3)
                    pygame.draw.circle(surface, (180, 0, 0), (blood_x, blood_y), blood_size)
                        
            elif char_index == 1:  # THOR - Dio del Tuono
                # Corpo
                pygame.draw.circle(surface, (200, 220, 255), (x, char_y), icon_size*0.5)
                
                # Barba fulminante
                for j in range(8):
                    angle = math.pi/2 + (j-4)*0.3
                    length = icon_size*0.6 + math.sin(self.animation_time*4 + j)*icon_size*0.1
                    bolt_points = []
                    segments = 5
                    for k in range(segments):
                        t = k/(segments-1)
                        offset = math.sin(t*math.pi*3 + j)*icon_size*0.1
                        px = x + math.cos(angle)*length*t + math.sin(angle)*offset
                        py = char_y + math.sin(angle)*length*t - math.cos(angle)*offset
                        bolt_points.append((px, py))
                    if len(bolt_points) > 1:
                        pygame.draw.lines(surface, (180, 220, 255), False, bolt_points, 
                                        max(3, int(icon_size*0.15)))
                
                # Martello rotante
                hammer_angle = self.animation_time * 6
                hammer_length = icon_size * 1.2
                hammer_x = x + math.cos(hammer_angle) * hammer_length * 0.7
                hammer_y = char_y + math.sin(hammer_angle) * hammer_length * 0.7
                
                # Manico
                pygame.draw.line(surface, (160, 140, 120), (x, char_y), 
                            (hammer_x, hammer_y), int(icon_size*0.2))
                
                # Testa del martello
                head_size = icon_size * 0.4
                pygame.draw.rect(surface, (180, 180, 200), 
                            (hammer_x - head_size//2, hammer_y - head_size//2, 
                                head_size, head_size))
                
                # Particelle di elettricità
                for _ in range(8):
                    spark_angle = random.random() * math.pi * 2
                    spark_dist = random.randint(20, 60)
                    spark_x = x + math.cos(spark_angle) * spark_dist
                    spark_y = char_y + math.sin(spark_angle) * spark_dist
                    spark_size = random.randint(1, 3)
                    pygame.draw.circle(surface, (100, 200, 255), 
                                    (int(spark_x), int(spark_y)), spark_size)
                        
            elif char_index == 2:  # AXE MASTER - Maestro delle Ascie
                # CORREZIONE: current_size non è definito, usa icon_size
                pygame.draw.circle(surface, (180, 160, 140), (x, char_y), int(icon_size*0.6))
                
                # Cappello
                hat_height = icon_size * 0.8
                hat_points = [
                    (x - icon_size*0.7, char_y - icon_size*0.3),
                    (x + icon_size*0.7, char_y - icon_size*0.3),
                    (x, char_y - icon_size*0.3 - hat_height)
                ]
                pygame.draw.polygon(surface, (100, 60, 30), hat_points)
                
                # Ascia rotante
                axe_angle = self.animation_time * 6
                axe_length = icon_size * 1.2
                axe_x = x + math.cos(axe_angle) * axe_length
                axe_y = char_y + math.sin(axe_angle) * axe_length
                
                # Manico ascia
                pygame.draw.line(surface, (140, 120, 80), (x, char_y), (axe_x, axe_y), 
                            max(2, int(icon_size*0.2)))
                
                # Lama ascia - CORREZIONE PRINCIPALE
                blade_size = icon_size * 0.6
                # Crea 3 punti distinti per il triangolo della lama
                blade_points = []
                for j in range(3):
                    if j == 0:
                        # Punto base (attaccato al manico)
                        angle = axe_angle + math.pi  # Direzione opposta all'asse
                    elif j == 1:
                        # Punto della punta
                        angle = axe_angle - math.pi/3
                    else:  # j == 2
                        # Terzo punto per completare il triangolo
                        angle = axe_angle + math.pi/3
                    
                    blade_x = axe_x + math.cos(angle) * blade_size
                    blade_y = axe_y + math.sin(angle) * blade_size
                    blade_points.append((blade_x, blade_y))
                
                # Assicurati che ci siano almeno 3 punti
                if len(blade_points) >= 3:
                    blade_color = (200, 200, 220)
                    pygame.draw.polygon(surface, blade_color, blade_points)
                    pygame.draw.polygon(surface, (255, 255, 200), blade_points, 1)
                
                # Cicatrici sul viso
                pygame.draw.line(surface, (120, 100, 80), 
                            (x - icon_size*0.2, char_y - icon_size*0.1),
                            (x + icon_size*0.1, char_y + icon_size*0.1), 2)
                    
            elif char_index == 3:  # ARCHER - Arciere Elfico
                # Corpo snello
                body_height = icon_size * 1.2
                body_width = icon_size * 0.6
                body_y = char_y + icon_size*0.2
                
                # Corpo principale
                pygame.draw.ellipse(surface, (200, 230, 200),
                                (x - body_width//2, 
                                body_y - body_height//2,
                                body_width, body_height))
                
                # Arco curvato
                bow_curve = math.sin(self.animation_time * 2) * 0.2
                bow_points = []
                for j in range(10):
                    t = j/9
                    angle = math.pi/4 + (t-0.5)*math.pi/2 + bow_curve
                    radius = icon_size * 0.8
                    bx = x + math.cos(angle) * radius
                    by = char_y + math.sin(angle) * radius
                    bow_points.append((bx, by))
                if len(bow_points) > 1:
                    pygame.draw.lines(surface, (160, 140, 100), False, bow_points, 4)
                
                # Freccia tremante
                arrow_shake = math.sin(self.animation_time * 10) * 2
                arrow_angle = math.pi/2
                arrow_length = icon_size * 1.0
                arrow_x = x + arrow_shake + math.cos(arrow_angle) * arrow_length
                arrow_y = char_y + math.sin(arrow_angle) * arrow_length
                
                # Penna della freccia
                for feather_side in [-1, 1]:
                    feather_points = [
                        (x + feather_side * 3, char_y - 5),
                        (x + feather_side * 8, char_y - 15),
                        (x + feather_side * 3, char_y - 25)
                    ]
                    pygame.draw.polygon(surface, (200, 200, 100), feather_points)
                
                # Punta della freccia
                arrow_head = [
                    (arrow_x, arrow_y),
                    (arrow_x - 10, arrow_y - 5),
                    (arrow_x - 10, arrow_y + 5)
                ]
                if len(arrow_head) >= 3:
                    pygame.draw.polygon(surface, (180, 180, 180), arrow_head)
                
                # Effetto vento
                for j in range(5):
                    wind_x = x + random.randint(-20, 20)
                    wind_y = char_y + random.randint(-30, 30)
                    wind_len = random.randint(10, 30)
                    # Correzione: pygame.draw.line non supporta alpha nella tupla colore
                    wind_surf = pygame.Surface((abs(wind_len), abs(wind_len)), pygame.SRCALPHA)
                    pygame.draw.line(wind_surf, (200, 200, 255, 100), 
                                (0, 0), (wind_len, wind_len//2), 1)
                    surface.blit(wind_surf, (wind_x, wind_y))
                    
            elif char_index == 4:  # NECROMANCER - Necromante Oscuro
                # Mantello fluttuante oscuro
                cloak_points = []
                for j in range(12):
                    t = j/11
                    angle = math.pi + t * math.pi
                    radius = icon_size * (0.8 + math.sin(t * math.pi * 2 + self.animation_time*3) * 0.2)
                    cx = x + math.cos(angle) * radius
                    cy = char_y + math.sin(angle) * radius * 0.5
                    cloak_points.append((cx, cy))
                if len(cloak_points) >= 3:
                    pygame.draw.polygon(surface, (40, 20, 60), cloak_points)
                
                # Teschio fluttuante
                skull_float = math.sin(self.animation_time * 2) * 5
                skull_size = icon_size * 0.6
                pygame.draw.circle(surface, (200, 220, 240), 
                                (x, char_y + skull_float), int(skull_size))
                
                # Occhi brillanti
                eye_glow = abs(math.sin(self.animation_time * 4)) * 100 + 100
                for eye_x in [-1, 1]:
                    pygame.draw.circle(surface, (eye_glow, 50, eye_glow), 
                                    (x + eye_x * icon_size*0.15, char_y + skull_float - icon_size*0.05), 
                                    int(icon_size*0.08))
                
                # Bocca oscura
                mouth_open = 0.3 + abs(math.sin(self.animation_time * 2)) * 0.2
                mouth_width = icon_size * 0.4
                mouth_height = icon_size * 0.2 * mouth_open
                pygame.draw.ellipse(surface, (30, 10, 40), 
                                (x - mouth_width/2, 
                                char_y + skull_float + icon_size*0.1, 
                                mouth_width, mouth_height))
                
                # Rune fluttuanti
                for j in range(4):
                    rune_angle = self.animation_time * 2 + j * math.pi/2
                    rune_radius = icon_size * 0.8
                    rune_x = x + math.cos(rune_angle) * rune_radius
                    rune_y = char_y + math.sin(rune_angle) * rune_radius
                    rune_size = icon_size * 0.15
                    rune_points = []
                    for k in range(4):
                        angle = k * math.pi/2
                        px = rune_x + math.cos(angle) * rune_size
                        py = rune_y + math.sin(angle) * rune_size
                        rune_points.append((px, py))
                    if len(rune_points) >= 3:
                        pygame.draw.polygon(surface, (150, 100, 200), rune_points, 1)
                        
            elif char_index == 5:  # PALADIN - Paladino Sacro
                # Armatura lucente
                armor_size = icon_size * 0.7
                pygame.draw.circle(surface, (220, 230, 240), (x, char_y), int(armor_size))
                
                # Scudo dorato
                shield_angle = math.sin(self.animation_time * 1.5) * 0.2
                shield_size = icon_size * 0.6
                pygame.draw.circle(surface, (255, 220, 100), (x, char_y), int(shield_size))
                
                # Croce luminosa sullo scudo
                cross_size = icon_size * 0.4
                # Linea verticale
                pygame.draw.rect(surface, (255, 255, 200), 
                            (x - cross_size//6, char_y - cross_size//2,
                            cross_size//3, cross_size))
                # Linea orizzontale
                pygame.draw.rect(surface, (255, 255, 200), 
                            (x - cross_size//2, char_y - cross_size//6,
                            cross_size, cross_size//3))
                
                # Spada fiammeggiante
                sword_angle = math.sin(self.animation_time * 2) * 0.3 + math.pi/2
                sword_length = icon_size * 1.5
                sword_x = x + math.cos(sword_angle) * sword_length
                sword_y = char_y + math.sin(sword_angle) * sword_length
                
                # Lama
                pygame.draw.line(surface, (255, 255, 220), 
                            (x, char_y),
                            (sword_x, sword_y), 
                            max(2, int(icon_size*0.15)))
                
                # Effetto fiamma sulla punta
                for j in range(3):
                    flame_size = icon_size * 0.2 * (1 + 0.5 * math.sin(self.animation_time*5 + j))
                    flame_points = []
                    for k in range(5):
                        angle = j * math.pi/3 + k/4 * math.pi * 0.5
                        fx = sword_x + math.cos(angle) * flame_size
                        fy = sword_y + math.sin(angle) * flame_size
                        flame_points.append((fx, fy))
                    if len(flame_points) >= 3:
                        pygame.draw.polygon(surface, (255, min(255, 200 + j*20), 100), flame_points)
                
                # Elmo con croce
                helmet_y = char_y - icon_size*0.5
                pygame.draw.circle(surface, (180, 190, 210), 
                                (int(x), int(helmet_y)), int(icon_size*0.3))
                # Croce sull'elmo
                pygame.draw.line(surface, (255, 255, 200), 
                            (x - icon_size*0.15, helmet_y),
                            (x + icon_size*0.15, helmet_y), 2)
                pygame.draw.line(surface, (255, 255, 200), 
                            (x, helmet_y - icon_size*0.15),
                            (x, helmet_y + icon_size*0.15), 2)
            
            name_parts = char.name.split(" - ")
            if is_unlocked:
                text_color = (255, 255, 255) if is_selected else (220, 230, 240)
            else:
                text_color = (120, 130, 150) if is_selected else (100, 110, 130)
            text_size = 30 if is_selected else 26
            
            self.draw_text_outlined(surface, name_parts[0], x, y + 60, text_size, text_color, (30, 35, 50))
            if len(name_parts) > 1:
                self.draw_text_outlined(surface, name_parts[1], x, y + 95, int(text_size * 0.9), 
                                    (220, 230, 255) if is_unlocked else (150, 160, 180), (30, 35, 50))
            
            self.draw_text(surface, char.description, x, y + 125, 18, text_color, centered=True)
            
            stats_y = y + 155
            self.draw_text(surface, f"❤ {char.max_hp}", x - 70, stats_y, 16, (255, 120, 120))
            self.draw_text(surface, f"⚡ {int(char.move_speed)}", x, stats_y, 16, (120, 200, 255))
            self.draw_text(surface, f"★ {char.special_cooldown}s", x + 70, stats_y, 16, (255, 220, 120))
            
            if not char.unlocked:
                self.draw_text_outlined(surface, f"LOCKED - {char.unlock_cost} POINTS", 
                                    x, y + 180, 22, (255, 200, 100), (60, 50, 30))
                self.draw_text(surface, f"You have: {self.character_unlock_points} points", 
                            x, y + 210, 16, (200, 200, 220), centered=True)
        
        instructions = "TRACKBALL: Navigate  •  LEFT: Select"
        if self.character_unlock_points > 0:
            instructions += "  •  Available Points: " + str(self.character_unlock_points)
        self.draw_text_outlined(surface, instructions, 640, 660, 26, (240, 220, 200), (40, 30, 25))


















    def draw_background(self, surface: pygame.Surface):
        # Sfondo deep space molto scuro
        surface.fill((5, 8, 15))  # Blu notte quasi nero
        
        # Stelle più statiche e scure
        for i, layer in enumerate(self.parallax_layers):
            layer_speed = layer['speed'] * 0.3  # Ridotto drasticamente il movimento
            offset_x = (self.camera_x * layer_speed + layer['offset_x']) % 1280
            offset_y = (self.camera_y * layer_speed * 0.5 + layer['offset_y']) % 720
            
            for star in layer['stars']:
                # Twinkle minimo
                twinkle = math.sin(self.animation_time * star['twinkle_speed'] * 0.3) * 0.2 + 0.8
                
                # Stelle molto più scure
                if i == 0:  # Stelle lontane - quasi invisibili
                    brightness = int(80 * star['brightness'] * twinkle)
                elif i == 1:  # Stelle medie
                    brightness = int(120 * star['brightness'] * twinkle * 0.8)
                else:  # Stelle vicine (poche)
                    brightness = int(150 * star['brightness'] * twinkle * 0.7)
                
                size_variation = star['size'] * (0.9 + 0.1 * twinkle)
                
                # Posizione statica con minimo parallasse
                star_x = (star['x'] + offset_x) % 1280
                star_y = (star['y'] + offset_y) % 720
                
                # Colori scuri e freddi
                if i == 0:
                    color = (brightness//2, brightness//2, brightness)  # Blu scuro
                elif i == 1:
                    color = (brightness, brightness//3, brightness//3)  # Rosso bordeaux
                else:
                    color = (brightness//3, brightness//2, brightness//3)  # Verde scuro
                
                # Disegna solo stelle principali, niente bagliori
                pygame.draw.circle(surface, color, 
                                (int(star_x), int(star_y)), int(size_variation))
        
        # Nebulose statiche e discrete
        for i in range(2):  # Solo 2 nebulose
            nebula_x = (self.camera_x * 0.05 + i * 700) % 1280
            nebula_y = (self.camera_y * 0.05 + i * 450) % 720
            
            nebula_size = 180 + i * 120
            
            # Colori molto scuri e trasparenti
            nebula_colors = [
                [(30, 20, 50, 15), (40, 25, 60, 10)],  # Viola scuro
                [(20, 30, 50, 12), (25, 35, 55, 8)]    # Blu scuro
            ][i]
            
            # Disegna nebulose semplici
            for layer_idx, color_data in enumerate(nebula_colors):
                layer_size = nebula_size * (0.8 + layer_idx * 0.2)
                
                nebula_surf = pygame.Surface((int(layer_size*2), int(layer_size*2)), pygame.SRCALPHA)
                pygame.draw.circle(nebula_surf, color_data, 
                                (int(layer_size), int(layer_size)), int(layer_size))
                
                surface.blit(nebula_surf, 
                        (int(nebula_x - layer_size), int(nebula_y - layer_size)))
        
        # Griglia molto sottile e discreta
        grid_size = 160  # Griglia più spaziosa
        grid_alpha = 12  # Quasi trasparente
        
        start_x = int((self.camera_x % grid_size) - grid_size)
        start_y = int((self.camera_y % grid_size) - grid_size)
        
        # Linee verticali - molto sottili
        for x in range(start_x, 1280 + grid_size, grid_size):
            alpha = grid_alpha
            color = (30, 35, 50, alpha)  # Blu-acciaio scuro
            
            # Linee continue ma sottilissime
            for y in range(0, 720, 2):  # Linee tratteggiate molto rade
                if y % 20 < 10:  # Solo metà della linea è disegnata
                    pygame.draw.line(surface, color, (x, y), (x, y+1), 1)
        
        # Linee orizzontali - molto sottili
        for y in range(start_y, 720 + grid_size, grid_size):
            alpha = grid_alpha
            color = (30, 35, 50, alpha)
            
            # Linee continue ma sottilissime
            for x in range(0, 1280, 2):  # Linee tratteggiate molto rade
                if x % 20 < 10:  # Solo metà della linea è disegnata
                    pygame.draw.line(surface, color, (x, y), (x+1, y), 1)
        
        # Pochissime particelle di polvere - quasi invisibili
        dust_alpha = 8
        for i in range(15):  # Solo 15 particelle
            dust_x = (self.camera_x * 0.2 + i * 185) % 1280
            dust_y = (self.camera_y * 0.2 + i * 143) % 720
            
            size = 0.5 + math.sin(i * 0.5) * 0.3
            alpha = int(dust_alpha * (0.3 + 0.7 * math.sin(i * 3)))
            
            if alpha > 3:  # Solo se abbastanza visibile
                dust_color = (60, 70, 90, alpha)
                pygame.draw.circle(surface, dust_color, 
                                (int(dust_x), int(dust_y)), int(size))
        
        # Aggiunta di alcune "stelle cadenti" molto rare e discrete
        if random.random() < 0.001:  # Molto raro
            start_x = random.randint(0, 1280)
            start_y = random.randint(0, 100)
            length = random.randint(10, 30)
            
            for i in range(length):
                alpha = int(40 * (1 - i/length))
                if alpha > 5:
                    x = start_x + i * 2
                    y = start_y + i * 1.5
                    color = (80, 90, 120, alpha)
                    pygame.draw.circle(surface, color, (int(x), int(y)), 1)


         
                    
    def draw_gameplay(self, surface: pygame.Surface):
        self.draw_background(surface)
        
        shake_x = random.uniform(-self.camera_shake * 12, self.camera_shake * 12) if self.camera_shake > 0 else 0
        shake_y = random.uniform(-self.camera_shake * 12, self.camera_shake * 12) if self.camera_shake > 0 else 0
        
        # Aura effects
        for aura in self.aura_effects:
            aura.draw(surface, self.camera_x, self.camera_y, shake_x, shake_y)
                             
        # Particelle
        for particle in self.particles:
            alpha = particle.life / particle.max_life
            if particle.fade_out:
                alpha *= alpha
                
            size = particle.size * alpha
            if size <= 0:
                continue
                
            color = tuple(min(255, max(0, int(c * alpha))) for c in particle.color)
            screen_x = particle.x - self.camera_x + shake_x
            screen_y = particle.y - self.camera_y + shake_y
            
            if -100 <= screen_x <= 1380 and -100 <= screen_y <= 820:
                if particle.glow:
                    glow_size = size * 2.0
                    glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*color, int(alpha * 150)), 
                                     (int(glow_size), int(glow_size)), int(glow_size))
                    surface.blit(glow_surf, (int(screen_x - glow_size), int(screen_y - glow_size)))
                
                if particle.shape == "circle":
                    pygame.draw.circle(surface, color, (int(screen_x), int(screen_y)), int(size))
                elif particle.shape == "star":
                    points = []
                    for i in range(5):
                        angle = particle.rotation + i * math.pi * 2 / 5
                        radius = size * (0.5 if i % 2 == 0 else 1.0)
                        points.append((
                            screen_x + math.cos(angle) * radius,
                            screen_y + math.sin(angle) * radius
                        ))
                    if len(points) > 2:
                        pygame.draw.polygon(surface, color, points)
                             
        # Proiettili
        for projectile in self.projectiles:
            projectile.draw(surface, self.camera_x, self.camera_y, shake_x, shake_y)
            
        # Nemici
        for enemy in self.enemies:
            if enemy.alive:
                enemy.draw(surface, self.camera_x, self.camera_y, shake_x, shake_y)
                
        # Pickup - ordine di disegno per visibilità
        for coin in self.coins_drops:
            coin.draw(surface, self.camera_x, self.camera_y, shake_x, shake_y)
            
        for gem in self.xp_gems:
            gem.draw(surface, self.camera_x, self.camera_y, shake_x, shake_y)
            
        for powerup in self.powerup_drops:
            powerup.draw(surface, self.camera_x, self.camera_y, shake_x, shake_y)
            
        # Minions
        for minion in self.minions:
            screen_x = minion['x'] - self.camera_x + shake_x
            screen_y = minion['y'] - self.camera_y + shake_y
            
            if -50 <= screen_x <= 1330 and -50 <= screen_y <= 770:
                pygame.draw.circle(surface, minion['color'], (int(screen_x), int(screen_y)), 
                                 int(minion['size']))
                pygame.draw.circle(surface, (255, 255, 255), (int(screen_x), int(screen_y)), 
                                 int(minion['size']), 2)
                
                # Barra HP minion
                hp_ratio = minion['hp'] / minion['max_hp']
                bar_width = minion['size'] * 2
                bar_height = 4
                bar_x = screen_x - bar_width/2
                bar_y = screen_y - minion['size'] - 10
                
                pygame.draw.rect(surface, (40, 20, 30), (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(surface, (100, 255, 100), (bar_x, bar_y, bar_width * hp_ratio, bar_height))
            
        # Giocatore
        self.draw_player(surface, shake_x, shake_y)
        
        # Numeri danno
        for dmg_num in self.damage_numbers:
            alpha = dmg_num.life
            size = int(dmg_num.size + (1 - alpha) * 15)
            color = tuple(min(255, max(0, int(c * alpha))) for c in dmg_num.color)
            text = f"{dmg_num.value}" + ("!" if dmg_num.is_critical else "")
            screen_x = dmg_num.x - self.camera_x + shake_x
            screen_y = dmg_num.y - self.camera_y + shake_y
            
            if -100 <= screen_x <= 1380 and -100 <= screen_y <= 820:
                font = pygame.font.Font(None, size)
                
                # Ombra testo
                shadow_surf = font.render(text, True, (30, 30, 40))
                shadow_surf.set_alpha(int(alpha * 255))
                shadow_rect = shadow_surf.get_rect(center=(int(screen_x)+2, int(screen_y)+2))
                surface.blit(shadow_surf, shadow_rect)
                
                # Bordo testo
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx != 0 or dy != 0:
                            outline_surf = font.render(text, True, (60, 60, 80))
                            outline_surf.set_alpha(int(alpha * 180))
                            outline_rect = outline_surf.get_rect(center=(int(screen_x)+dx, int(screen_y)+dy))
                            surface.blit(outline_surf, outline_rect)
                
                # Testo principale
                text_surf = font.render(text, True, color)
                text_rect = text_surf.get_rect(center=(int(screen_x), int(screen_y)))
                surface.blit(text_surf, text_rect)
                          
        # Testo fluttuante
        for text in self.floating_texts:
            alpha = min(1.0, text.life / 1.5)
            color = tuple(min(255, max(0, int(c * alpha))) for c in text.color)
            screen_x = text.x - self.camera_x + shake_x
            screen_y = text.y - self.camera_y + shake_y
            
            if -100 <= screen_x <= 1380 and -100 <= screen_y <= 820:
                font = pygame.font.Font(None, text.size)
                
                # Ombra testo
                shadow_surf = font.render(text.text, True, (40, 40, 60))
                shadow_surf.set_alpha(int(alpha * 180))
                shadow_rect = shadow_surf.get_rect(center=(int(screen_x)+3, int(screen_y)+3))
                surface.blit(shadow_surf, shadow_rect)
                
                # Testo principale
                text_surf = font.render(text.text, True, color)
                text_rect = text_surf.get_rect(center=(int(screen_x), int(screen_y)))
                surface.blit(text_surf, text_rect)
                          
        # HUD
        self.draw_hud(surface)
        
        # Effetto flash
        if self.flash_effect > 0:
            flash_surf = pygame.Surface((1280, 720))
            flash_surf.fill(self.screen_flash_color)
            flash_surf.set_alpha(int(self.flash_effect * 180))
            surface.blit(flash_surf, (0, 0))
















    def draw_player(self, surface: pygame.Surface, shake_x: float, shake_y: float):
        screen_x = self.player_x - self.camera_x + shake_x
        screen_y = self.player_y - self.camera_y + shake_y
        
        if self.invulnerable_time > 0 and int(self.invulnerable_time * 25) % 2 == 0:
            return
            
        char = self.characters_data[self.selected_character_index]
        
        # Animazione di movimento
        move_intensity = math.sqrt(self.player_vx**2 + self.player_vy**2) / 100
        bob_effect = math.sin(self.animation_time * 8) * 3 * (1 + move_intensity * 0.5)
        
        # Ombra con effetto di movimento
        shadow_size = max(5, 25 + move_intensity * 5)
        shadow_alpha = min(255, 150 + int(move_intensity * 50))
        if shadow_size > 0 and shadow_alpha > 0:
            shadow_surf = pygame.Surface((int(shadow_size*2), int(shadow_size*2)), pygame.SRCALPHA)
            # Correggi: usa solo 3 componenti per draw.circle, gestisci alpha tramite Surface
            pygame.draw.circle(shadow_surf, (40, 40, 60), 
                            (int(shadow_size), int(shadow_size)), int(shadow_size))
            shadow_surf.set_alpha(shadow_alpha)
            surface.blit(shadow_surf, (int(screen_x - shadow_size), int(screen_y + 8)))
        
        # Effetto movimento (scia) - solo quando si muove velocemente
        if move_intensity > 0.5:
            trail_length = min(5, int(3 + move_intensity * 2))
            for i in range(trail_length):
                trail_alpha = min(255, int(100 * (1 - i/trail_length) * move_intensity))
                trail_size = max(3, 15 - i * 3)
                if trail_alpha > 10 and trail_size > 0:
                    trail_x = screen_x - self.player_vx * 0.02 * i
                    trail_y = screen_y - self.player_vy * 0.02 * i
                    if trail_size > 0:
                        trail_surf = pygame.Surface((max(2, trail_size*2), max(2, trail_size*2)), pygame.SRCALPHA)
                        # Correggi: usa solo 3 componenti per draw.circle
                        pygame.draw.circle(trail_surf, char.color[:3], 
                                        (trail_size, trail_size), trail_size)
                        trail_surf.set_alpha(trail_alpha)
                        surface.blit(trail_surf, (int(trail_x - trail_size), int(trail_y - trail_size)))
        
        # Calcola l'angolo di movimento per orientare alcune animazioni
        move_angle = 0
        if abs(self.player_vx) > 0.1 or abs(self.player_vy) > 0.1:
            move_angle = math.atan2(self.player_vy, self.player_vx)
        
        # Disegno specifico per ogni personaggio
        if self.selected_character_index == 0:  # POE - Vampiro Elegante
            # Corpo principale
            body_size = max(15, 20 + math.sin(self.animation_time * 4) * 2)
            pygame.draw.circle(surface, (220, 200, 180), 
                            (int(screen_x), int(screen_y + bob_effect)), int(body_size))
            
            # Mantello fluttuante
            cloak_float = math.sin(self.animation_time * 3) * 5
            cloak_points = [
                (screen_x - 25, screen_y + 10 + bob_effect),
                (screen_x - 35, screen_y - 15 + cloak_float),
                (screen_x, screen_y - 25 + bob_effect),
                (screen_x + 35, screen_y - 15 - cloak_float),
                (screen_x + 25, screen_y + 10 + bob_effect)
            ]
            pygame.draw.polygon(surface, (100, 20, 40), cloak_points)
            
            # Occhi rossi luminosi
            eye_glow = min(255, abs(math.sin(self.animation_time * 5)) * 100 + 100)
            for eye_offset in [-8, 8]:
                pygame.draw.circle(surface, (eye_glow, 20, 20), 
                                (int(screen_x + eye_offset), int(screen_y - 2 + bob_effect)), 6)
                pygame.draw.circle(surface, (255, 255, 255), 
                                (int(screen_x + eye_offset + 2), int(screen_y - 4 + bob_effect)), 2)
            
            # Zanne pulsanti
            if int(self.animation_time * 8) % 2 == 0:
                fang_size = max(3, 5 + math.sin(self.animation_time * 4) * 2)
                for fang_offset in [-4, 4]:
                    fang_points = [
                        (screen_x + fang_offset, screen_y + 8 + bob_effect),
                        (screen_x + fang_offset - 3, screen_y + 15 + bob_effect),
                        (screen_x + fang_offset + 3, screen_y + 15 + bob_effect)
                    ]
                    pygame.draw.polygon(surface, (255, 255, 255), fang_points)
            
            # Particelle di sangue se sta danneggiando
            if self.special_active or move_intensity > 1:
                for _ in range(2):
                    blood_x = screen_x + random.randint(-15, 15)
                    blood_y = screen_y + random.randint(-10, 10)
                    blood_size = random.randint(1, 3)
                    pygame.draw.circle(surface, (180, 0, 0), 
                                    (int(blood_x), int(blood_y)), blood_size)
                
        elif self.selected_character_index == 1:  # THOR - Dio del Tuono
            # Corpo
            body_size = 18
            pygame.draw.circle(surface, (200, 220, 255), 
                            (int(screen_x), int(screen_y + bob_effect)), body_size)
            
            # Barba fulminante
            for i in range(5):
                angle = math.pi/2 + (i-2)*0.4
                length = max(10, 15 + math.sin(self.animation_time*4 + i)*5)
                bolt_points = []
                segments = 4
                for k in range(segments):
                    t = k/(segments-1)
                    offset = math.sin(t*math.pi*3 + i)*3
                    px = screen_x + math.cos(angle)*length*t + math.sin(angle)*offset
                    py = screen_y + bob_effect + math.sin(angle)*length*t - math.cos(angle)*offset
                    bolt_points.append((px, py))
                if len(bolt_points) > 1:
                    pygame.draw.lines(surface, (180, 220, 255), False, bolt_points, 2)
            
            # Martello rotante
            hammer_angle = self.animation_time * 6
            hammer_length = 25
            hammer_x = screen_x + math.cos(hammer_angle) * hammer_length
            hammer_y = screen_y + bob_effect + math.sin(hammer_angle) * hammer_length
            
            # Manico martello
            pygame.draw.line(surface, (160, 140, 120), (screen_x, screen_y + bob_effect),
                        (hammer_x, hammer_y), 4)
            
            # Testa martello
            head_size = 8
            pygame.draw.circle(surface, (180, 180, 200), 
                            (int(hammer_x), int(hammer_y)), head_size)
            
            # Fulmini attorno durante movimento veloce
            if move_intensity > 0.8:
                for _ in range(3):
                    spark_angle = random.random() * math.pi * 2
                    spark_dist = random.randint(15, 30)
                    spark_x = screen_x + math.cos(spark_angle) * spark_dist
                    spark_y = screen_y + bob_effect + math.sin(spark_angle) * spark_dist
                    pygame.draw.circle(surface, (100, 200, 255), 
                                    (int(spark_x), int(spark_y)), 2)
                
        elif self.selected_character_index == 2:  # AXE MASTER - Maestro delle Ascie
            # Corpo robusto
            body_size = 20
            pygame.draw.circle(surface, (180, 160, 140), 
                            (int(screen_x), int(screen_y + bob_effect)), body_size)
            
            # Braccia muscolose che oscillano
            arm_swing = math.sin(self.animation_time * 4) * 0.5
            for side in [-1, 1]:
                arm_length = 15
                arm_angle = math.pi/2 + side * (arm_swing + 0.3)
                arm_x = screen_x + math.cos(arm_angle) * arm_length
                arm_y = screen_y + bob_effect + math.sin(arm_angle) * arm_length
                
                pygame.draw.line(surface, (200, 180, 160), 
                            (screen_x, screen_y + bob_effect),
                            (arm_x, arm_y), 6)
                
                # Ascia rotante
                axe_angle = self.animation_time * 10 + side * math.pi
                axe_length = 20
                axe_x = arm_x + math.cos(axe_angle) * axe_length
                axe_y = arm_y + math.sin(axe_angle) * axe_length
                
                # Manico ascia
                pygame.draw.line(surface, (140, 120, 80), 
                            (arm_x, arm_y),
                            (axe_x, axe_y), 3)
                
                # Lama ascia
                blade_size = 8
                for blade_side in [-1, 1]:
                    blade_angle = axe_angle + blade_side * math.pi/3
                    blade_x = axe_x + math.cos(blade_angle) * blade_size
                    blade_y = axe_y + math.sin(blade_angle) * blade_size
                    pygame.draw.line(surface, (200, 200, 220), 
                                (axe_x, axe_y),
                                (blade_x, blade_y), 3)
            
            # Cicatrici sul viso
            scar_angle = self.animation_time * 0.5
            scar_x = screen_x + math.cos(scar_angle) * 2
            scar_y = screen_y + bob_effect - 5 + math.sin(scar_angle) * 1
            pygame.draw.line(surface, (120, 100, 80), 
                        (scar_x - 5, scar_y - 3),
                        (scar_x + 3, scar_y + 4), 2)
                
        elif self.selected_character_index == 3:  # ARCHER - Arciere Elfico
            # Corpo snello
            body_height = 25
            body_width = 15
            
            # Corpo principale
            pygame.draw.ellipse(surface, (200, 230, 200),
                            (screen_x - body_width//2, 
                            screen_y - body_height//2 + bob_effect,
                            body_width, body_height))
            
            # Arco orientato nella direzione di movimento
            bow_angle = move_angle + math.pi/2
            bow_radius = max(15, 20)
            bow_center_x = screen_x
            bow_center_y = screen_y + bob_effect
            
            # Disegna arco come un arco di cerchio
            bow_rect = (bow_center_x - bow_radius, bow_center_y - bow_radius,
                    bow_radius*2, bow_radius*2)
            pygame.draw.arc(surface, (160, 140, 100), bow_rect,
                        bow_angle - math.pi/4, bow_angle + math.pi/4, 3)
            
            # Freccia (se ci si sta muovendo)
            if move_intensity > 0.1:
                arrow_length = 18
                arrow_x = bow_center_x + math.cos(bow_angle) * arrow_length
                arrow_y = bow_center_y + math.sin(bow_angle) * arrow_length
                
                pygame.draw.line(surface, (200, 200, 200), 
                            (bow_center_x, bow_center_y),
                            (arrow_x, arrow_y), 2)
                
                # Punta della freccia
                arrow_head = [
                    (arrow_x, arrow_y),
                    (arrow_x - math.cos(bow_angle + math.pi*0.75) * 6,
                    arrow_y - math.sin(bow_angle + math.pi*0.75) * 6),
                    (arrow_x - math.cos(bow_angle - math.pi*0.75) * 6,
                    arrow_y - math.sin(bow_angle - math.pi*0.75) * 6)
                ]
                pygame.draw.polygon(surface, (180, 180, 180), arrow_head)
            
            # Cappuccio elfico
            hood_points = [
                (screen_x, screen_y - 15 + bob_effect),
                (screen_x - 12, screen_y - 5 + bob_effect),
                (screen_x - 10, screen_y + 5 + bob_effect),
                (screen_x + 10, screen_y + 5 + bob_effect),
                (screen_x + 12, screen_y - 5 + bob_effect)
            ]
            pygame.draw.polygon(surface, (50, 80, 60), hood_points)
                
        elif self.selected_character_index == 4:  # NECROMANCER - Necromante Oscuro
            # Mantello fluttuante
            cloak_wave = math.sin(self.animation_time * 3) * 8
            cloak_points = [
                (screen_x - 20, screen_y + 10 + bob_effect),
                (screen_x - 25, screen_y - cloak_wave),
                (screen_x, screen_y - 20 + bob_effect),
                (screen_x + 25, screen_y + cloak_wave),
                (screen_x + 20, screen_y + 10 + bob_effect)
            ]
            pygame.draw.polygon(surface, (40, 20, 60), cloak_points)
            
            # Teschio fluttuante
            skull_float = math.sin(self.animation_time * 2) * 4
            skull_size = 14
            pygame.draw.circle(surface, (200, 220, 240), 
                            (int(screen_x), int(screen_y - 5 + skull_float + bob_effect)), 
                            skull_size)
            
            # Occhi brillanti
            eye_glow = min(255, abs(math.sin(self.animation_time * 4)) * 150 + 50)
            for eye_offset in [-6, 6]:
                pygame.draw.circle(surface, (eye_glow, 50, eye_glow), 
                                (int(screen_x + eye_offset), 
                                int(screen_y - 7 + skull_float + bob_effect)), 4)
            
            # Bocca oscura
            mouth_width = 12
            mouth_height = max(1, 4 + abs(math.sin(self.animation_time * 3)) * 2)
            mouth_rect = (screen_x - mouth_width//2, 
                        screen_y + 3 + skull_float + bob_effect,
                        max(1, mouth_width), mouth_height)
            pygame.draw.ellipse(surface, (30, 10, 40), mouth_rect)
            
            # Rune fluttuanti attorno
            if self.special_active or move_intensity > 0.5:
                for i in range(3):
                    rune_angle = self.animation_time * 2 + i * math.pi*2/3
                    rune_radius = 25
                    rune_x = screen_x + math.cos(rune_angle) * rune_radius
                    rune_y = screen_y + bob_effect + math.sin(rune_angle) * rune_radius
                    
                    rune_size = 4
                    rune_points = []
                    for j in range(4):
                        angle = j * math.pi/2
                        px = rune_x + math.cos(angle) * rune_size
                        py = rune_y + math.sin(angle) * rune_size
                        rune_points.append((px, py))
                    if len(rune_points) > 2:
                        pygame.draw.polygon(surface, (150, 100, 200), rune_points, 1)
                
        elif self.selected_character_index == 5:  # PALADIN - Paladino Sacro
            # Armatura lucente
            body_size = 22
            pygame.draw.circle(surface, (220, 230, 240), 
                            (int(screen_x), int(screen_y + bob_effect)), body_size)
            
            # Scudo orientato nella direzione di movimento
            shield_angle = move_angle
            shield_radius = 18
            shield_x = screen_x + math.cos(shield_angle) * 15
            shield_y = screen_y + bob_effect + math.sin(shield_angle) * 15
            
            # Scudo circolare
            pygame.draw.circle(surface, (140, 180, 220), 
                            (int(shield_x), int(shield_y)), shield_radius)
            
            # Croce sullo scudo
            cross_size = 10
            pygame.draw.line(surface, (255, 255, 200), 
                        (shield_x - cross_size, shield_y),
                        (shield_x + cross_size, shield_y), 3)
            pygame.draw.line(surface, (255, 255, 200), 
                        (shield_x, shield_y - cross_size),
                        (shield_x, shield_y + cross_size), 3)
            
            # Spada nella mano opposta
            sword_angle = shield_angle + math.pi
            sword_length = 20
            sword_x = screen_x + math.cos(sword_angle) * 12
            sword_y = screen_y + bob_effect + math.sin(sword_angle) * 12
            
            # Lama spada
            pygame.draw.line(surface, (255, 255, 220), 
                        (sword_x, sword_y),
                        (sword_x + math.cos(sword_angle) * sword_length,
                            sword_y + math.sin(sword_angle) * sword_length), 4)
            
            # Effetto fiamma sacra se l'abilità speciale è attiva
            if self.special_active:
                for j in range(3):
                    flame_size = max(3, 6 * (1 + 0.5 * math.sin(self.animation_time*5 + j)))
                    flame_angle = self.animation_time * 3 + j * math.pi*2/3
                    flame_x = screen_x + math.cos(flame_angle) * 30
                    flame_y = screen_y + bob_effect + math.sin(flame_angle) * 30
                    
                    flame_points = []
                    for k in range(5):
                        angle = flame_angle + k * math.pi/2.5
                        px = flame_x + math.cos(angle) * flame_size
                        py = flame_y + math.sin(angle) * flame_size
                        flame_points.append((px, py))
                    if len(flame_points) > 2:
                        pygame.draw.polygon(surface, (255, min(255, 200 + j*20), 100), flame_points)
            
            # Elmo con croce
            helmet_y = screen_y - 10 + bob_effect
            pygame.draw.circle(surface, (180, 190, 210), 
                            (int(screen_x), int(helmet_y)), 10)
            pygame.draw.line(surface, (255, 255, 200), 
                        (screen_x - 5, helmet_y),
                        (screen_x + 5, helmet_y), 2)
            pygame.draw.line(surface, (255, 255, 200), 
                        (screen_x, helmet_y - 5),
                        (screen_x, helmet_y + 5), 2)
        
        # Scudo energetico (se presente)
        if self.shield_hp > 0:
            shield_ratio = self.shield_hp / max(1, self.max_shield)
            shield_size = max(20, 35 + move_intensity * 5)
            shield_alpha = min(255, int(180 * shield_ratio))
            shield_pulse = math.sin(self.animation_time * 8) * 0.2 + 0.8
            
            if shield_size > 0 and shield_alpha > 0:
                shield_surf = pygame.Surface((max(2, int(shield_size*2)), max(2, int(shield_size*2))), pygame.SRCALPHA)
                
                for i in range(3):
                    layer_size = shield_size * (1 - i * 0.1)
                    layer_alpha = min(255, int(shield_alpha * (1 - i * 0.3)))
                    if layer_size > 0 and layer_alpha > 0:
                        # Correggi: usa solo 3 componenti per draw.circle
                        color_surf = pygame.Surface((max(2, int(layer_size*2*shield_pulse)), 
                                                max(2, int(layer_size*2*shield_pulse))), pygame.SRCALPHA)
                        pygame.draw.circle(color_surf, (100, 180, 255), 
                                        (int(layer_size*shield_pulse), int(layer_size*shield_pulse)), 
                                        int(layer_size * shield_pulse), 2)
                        color_surf.set_alpha(layer_alpha)
                        shield_surf.blit(color_surf, (int(shield_size - layer_size*shield_pulse), 
                                                    int(shield_size - layer_size*shield_pulse)))
                
                surface.blit(shield_surf, (int(screen_x - shield_size), int(screen_y - shield_size)))
        
        # Indicatore abilità speciale attiva
        if self.special_active:
            pulse = math.sin(self.animation_time * 12) * 0.3 + 0.8
            radius = max(10, int(45 * pulse))
            
            special_color = char.color[:3]  # Prendi solo RGB
            
            if radius > 0:
                special_surf = pygame.Surface((max(2, radius*2), max(2, radius*2)), pygame.SRCALPHA)
                
                # Aura esterna
                for i in range(3):
                    ring_size = radius * (1 - i * 0.2)
                    ring_alpha = min(255, int(100 * (1 - i * 0.3)))
                    if ring_size > 0 and ring_alpha > 0:
                        ring_surf = pygame.Surface((max(2, int(ring_size*2)), max(2, int(ring_size*2))), pygame.SRCALPHA)
                        pygame.draw.circle(ring_surf, special_color, 
                                        (int(ring_size), int(ring_size)), int(ring_size))
                        ring_surf.set_alpha(ring_alpha)
                        special_surf.blit(ring_surf, (int(radius - ring_size), int(radius - ring_size)))
                
                # Bordo pulsante
                border_width = max(2, int(radius * 0.1))
                border_surf = pygame.Surface((max(2, radius*2), max(2, radius*2)), pygame.SRCALPHA)
                pygame.draw.circle(border_surf, (255, 255, 200), 
                                (radius, radius), radius, border_width)
                border_surf.set_alpha(200)
                special_surf.blit(border_surf, (0, 0))
                
                surface.blit(special_surf, (int(screen_x - radius), int(screen_y - radius)))
            
            # Particelle speciali rotanti
            particle_count = 8
            for i in range(particle_count):
                angle = self.animation_time * 6 + i * math.pi*2/particle_count
                dist = radius * 0.7
                px = screen_x + math.cos(angle) * dist
                py = screen_y + math.sin(angle) * dist
                
                particle_size = max(2, 3 + math.sin(self.animation_time * 10 + i) * 1)
                particle_color = (255, 255, 200) if i % 2 == 0 else (255, 255, 150)
                
                pygame.draw.circle(surface, particle_color, 
                                (int(px), int(py)), int(particle_size))












    def draw_hud(self, surface: pygame.Surface):
        padding = 20
        bar_width = 300
        
        # Barra HP
        hp_bar_height = 35
        hp_ratio = max(0, self.hp / self.max_hp)
        
        # Background barra
        pygame.draw.rect(surface, (50, 40, 60),
                        (padding, padding, bar_width, hp_bar_height), 0, 10)
        
        # HP corrente
        hp_color = (80, 255, 120) if hp_ratio > 0.6 else (255, 200, 80) if hp_ratio > 0.3 else (255, 80, 80)
        pygame.draw.rect(surface, hp_color,
                        (padding, padding, int(bar_width * hp_ratio), hp_bar_height), 0, 10)
        
        # Bordo
        pygame.draw.rect(surface, (80, 70, 90),
                        (padding, padding, bar_width, hp_bar_height), 3, 10)
        
        # Testo HP
        hp_text = f"{int(self.hp)}/{self.max_hp}"
        self.draw_text_outlined(surface, hp_text, padding + bar_width // 2, padding + hp_bar_height // 2, 24,
                              (255, 255, 255), (50, 40, 60), 2)
        
        # Barra scudo sopra HP
        if self.max_shield > 0:
            shield_bar_height = 8
            shield_ratio = self.shield_hp / max(1, self.max_shield)
            shield_y = padding - shield_bar_height - 3
            
            pygame.draw.rect(surface, (40, 60, 80),
                           (padding, shield_y, bar_width, shield_bar_height), 0, 4)
            pygame.draw.rect(surface, (100, 180, 255),
                           (padding, shield_y, int(bar_width * shield_ratio), shield_bar_height), 0, 4)
            pygame.draw.rect(surface, (150, 200, 255),
                           (padding, shield_y, bar_width, shield_bar_height), 1, 4)
        
        # Barra XP
        xp_bar_y = padding + hp_bar_height + 10
        xp_bar_height = 28
        
        if self.xp_to_next_level > 0:
            xp_ratio = self.xp / self.xp_to_next_level
        else:
            xp_ratio = 0
        
        pygame.draw.rect(surface, (50, 40, 60),
                        (padding, xp_bar_y, bar_width, xp_bar_height), 0, 8)
        pygame.draw.rect(surface, (100, 180, 255),
                        (padding, xp_bar_y, int(bar_width * xp_ratio), xp_bar_height), 0, 8)
        pygame.draw.rect(surface, (80, 70, 90),
                        (padding, xp_bar_y, bar_width, xp_bar_height), 2, 8)
        
        # Testo XP e livello
        xp_text = f"{int(self.xp)}/{self.xp_to_next_level}"
        self.draw_text_outlined(surface, xp_text, padding + bar_width // 2, xp_bar_y + xp_bar_height // 2, 20,
                              (255, 255, 255), (50, 40, 60), 1)
        
        level_text = f"LEVEL {self.level}"
        self.draw_text_outlined(surface, level_text, padding + bar_width // 2, xp_bar_y - 14, 18,
                              (220, 240, 255), (50, 40, 60), 1)
        
        # Barra special
        special_bar_y = xp_bar_y + xp_bar_height + 8
        special_bar_height = 24
        special_ratio = self.special_charge / self.special_max
        
        pygame.draw.rect(surface, (50, 40, 60),
                        (padding, special_bar_y, bar_width, special_bar_height), 0, 6)
        
        special_color = (255, 220, 100) if special_ratio >= 1.0 else (180, 200, 255)
        pygame.draw.rect(surface, special_color,
                        (padding, special_bar_y, int(bar_width * special_ratio), special_bar_height), 0, 6)
        pygame.draw.rect(surface, (80, 70, 90),
                        (padding, special_bar_y, bar_width, special_bar_height), 2, 6)
        
        special_text = "SPECIAL" if special_ratio < 1.0 else "READY!"
        special_text_color = (255, 255, 255) if special_ratio < 1.0 else (255, 255, 180)
        self.draw_text_outlined(surface, special_text, padding + bar_width // 2, special_bar_y + special_bar_height // 2, 18,
                              special_text_color, (50, 40, 60), 1)
        
        # Statistiche destra
        stats_x = 1280 - padding - 180
        stats_y = padding + 15
        
        self.draw_text_outlined(surface, f"SCORE: {self.score:,}", stats_x, stats_y, 26,
                              (255, 240, 200), (60, 50, 70), 1)
        self.draw_text_outlined(surface, f"COINS: {self.coins}", stats_x, stats_y + 32, 22,
                              (255, 220, 120), (60, 50, 70), 1)
        self.draw_text_outlined(surface, f"KILLS: {self.kill_count:,}", stats_x, stats_y + 58, 22,
                              (255, 160, 160), (60, 50, 70), 1)
        self.draw_text_outlined(surface, f"WAVE: {self.wave_number}", stats_x, stats_y + 84, 22,
                              (160, 200, 255), (60, 50, 70), 1)
        
        # Combo
        if self.combo > 1:
            combo_text = f"COMBO ×{self.combo}!"
            if self.combo < 10:
                combo_color = (255, 255, 120)
            elif self.combo < 25:
                combo_color = (255, 200, 80)
            elif self.combo < 50:
                combo_color = (255, 150, 50)
            else:
                combo_color = (255, 100, 100)
                
            combo_size = min(56, 30 + self.combo // 2)
            self.draw_text_outlined(surface, combo_text, 640, 60, combo_size, combo_color, (60, 50, 70), 2)
            
        # Tempo di gioco
        minutes = int(self.game_time) // 60
        seconds = int(self.game_time) % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        self.draw_text_outlined(surface, time_text, 1240, 680, 24,
                              (180, 220, 255), (50, 40, 60), 1)
        
        # Nemici rimanenti
        enemies_alive = len([e for e in self.enemies if e.alive])
        enemy_text = f"ENEMIES: {enemies_alive}"
        self.draw_text_outlined(surface, enemy_text, 1240, 650, 20,
                              (255, 160, 160), (50, 40, 60), 1)
        
        # Wave progress
        if self.wave_enemies_left > 0:
            wave_progress = self.wave_total_enemies - self.wave_enemies_left
            wave_text = f"WAVE {self.wave_number}: {wave_progress}/{self.wave_total_enemies}"
            self.draw_text_outlined(surface, wave_text, 640, 700, 20,
                                  (180, 220, 255), (50, 40, 60), 1)
                                  
        # Armi attive (lato destro)
        weapons_x = 1280 - padding - 30
        for i, weapon in enumerate(self.weapons[:8]):
            weapon_y = 180 + i * 42
            
            # Icona arma
            icon_size = 18
            pygame.draw.circle(surface, weapon.color, (weapons_x, weapon_y), icon_size)
            pygame.draw.circle(surface, (255, 255, 255), (weapons_x, weapon_y), icon_size, 1)
            
            # Livello
            level_text = str(weapon.level)
            self.draw_text(surface, level_text, weapons_x, weapon_y, 12, (255, 255, 255))
            
            # Nome abbreviato
            short_name = weapon.name[:4] if len(weapon.name) > 4 else weapon.name
            self.draw_text(surface, short_name, weapons_x - 40, weapon_y, 11, (200, 200, 220))
            
            # Danno corrente
            damage = int((weapon.base_damage + (weapon.level * 4)) * self.stats['damage_mult'])
            self.draw_text(surface, f"{damage}dmg", weapons_x - 85, weapon_y, 10, (220, 180, 180))
            
    def draw_level_up_menu(self, surface: pygame.Surface):
        overlay = pygame.Surface((1280, 720))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))
        
        title = "LEVEL UP!"
        self.draw_text_outlined(surface, title, 640, 80, 72, (255, 220, 120), (70, 60, 0), 3)
        
        subtitle = f"Choose Your Power (Level {self.level})"
        self.draw_text_outlined(surface, subtitle, 640, 150, 32, (230, 230, 230), (50, 45, 55), 2)
        
        choice_spacing = 400
        start_x = 640 - (len(self.level_up_choices) - 1) * choice_spacing / 2
        
        for i, powerup in enumerate(self.level_up_choices):
            x = int(start_x + i * choice_spacing)
            y = 400
            
            is_selected = i == self.level_up_selected
            
            scale = 1.0
            if is_selected:
                pulse = math.sin(self.animation_time * 8) * 0.2 + 1.2
                scale = pulse
                
            box_width = int(380 * scale)
            box_height = int(260 * scale)
            
            box_color = powerup['icon_color'] if is_selected else (70, 65, 85)
            border_color = (255, 255, 255) if is_selected else (140, 130, 160)
            border_width = 8 if is_selected else 4
            
            box_rect = pygame.Rect(x - box_width//2, y - box_height//2, box_width, box_height)
            
            # Background
            pygame.draw.rect(surface, box_color, box_rect, 0, 25)
            
            # Effetto glow per selezionato
            if is_selected:
                glow_rect = pygame.Rect(x - box_width//2 - 15, y - box_height//2 - 15, 
                                      box_width + 30, box_height + 30)
                pygame.draw.rect(surface, (*powerup['icon_color'], 80), glow_rect, 0, 30)
            
            pygame.draw.rect(surface, border_color, box_rect, border_width, 25)
            
            # Icona powerup
            icon_size = int(60 * scale)
            pygame.draw.circle(surface, powerup['icon_color'], (x, y - 70), icon_size)
            pygame.draw.circle(surface, (255, 255, 255), (x, y - 70), icon_size, max(2, int(icon_size*0.1)))
            
            # Livello
            if 'weapon_ref' in powerup:
                level_text = "NEW"
            else:
                level_text = f"Lvl {powerup.get('level', 0) + 1}/{powerup['max_level']}"
            self.draw_text_outlined(surface, level_text, x, y - 70, int(24 * scale), 
                                  (255, 255, 255), (40, 35, 50), 1)
            
            text_color = (255, 255, 255) if is_selected else (230, 240, 250)
            name_size = int(32 * scale) if is_selected else int(28 * scale)
            desc_size = int(20 * scale) if is_selected else int(18 * scale)
            
            self.draw_text_outlined(surface, powerup['name'], x, y + 20, name_size, text_color, (40, 35, 50), 1)
            
            # Descrizione wrappata
            desc_lines = self.wrap_text(powerup['description'], 40)
            for j, line in enumerate(desc_lines):
                self.draw_text(surface, line, x, y + 65 + j * 26, desc_size, text_color, centered=True)
                
            # Tier indicator
            tier = powerup.get('tier', 1)
            tier_colors = [(100, 200, 100), (255, 200, 100), (255, 100, 100)]
            tier_text = ["COMMON", "RARE", "LEGENDARY"][min(tier-1, 2)]
            tier_color = tier_colors[min(tier-1, 2)]
            self.draw_text_outlined(surface, tier_text, x, y + 120, int(18 * scale), 
                                  tier_color, (30, 25, 40), 1)
                
        instructions = "TRACKBALL: Navigate  •  LEFT: Select"
        if self.reroll_count < self.max_rerolls:
            instructions += f"  •  RIGHT: Reroll ({self.max_rerolls - self.reroll_count} left)"
        if self.skip_count < self.max_skips:
            instructions += f"  •  MIDDLE: Skip (+{self.xp_to_next_level//3} XP)"
        self.draw_text_outlined(surface, instructions, 640, 660, 24, (200, 230, 255), (35, 30, 45), 1)
        
    def draw_game_over(self, surface: pygame.Surface):
        overlay = pygame.Surface((1280, 720))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        surface.blit(overlay, (0, 0))
        
        # Titolo
        title = "GAME OVER"
        self.draw_text_outlined(surface, title, 640, 120, 86, (255, 100, 100), (70, 30, 30), 3)
        
        # Statistiche
        stats_y = 220
        stats = [
            f"Final Score: {self.score:,}",
            f"Time Survived: {int(self.total_game_time)//60:02d}:{int(self.total_game_time)%60:02d}",
            f"Level Reached: {self.level}",
            f"Enemies Killed: {self.kill_count:,}",
            f"Wave Reached: {self.wave_number}",
            f"Coins Collected: {self.coins}",
            f"Total XP: {self.total_xp:,}",
            f"Max Combo: {self.max_combo}",
            f"Prestige Points: {self.prestige_points}"
        ]
        
        for i, stat in enumerate(stats):
            y = stats_y + i * 40
            color = (220, 240, 255) if i % 2 == 0 else (200, 220, 240)
            self.draw_text_outlined(surface, stat, 640, y, 28, color, (40, 35, 50), 1)
        
        # Istruzioni
        instructions_y = 600
        instructions = [
            "LEFT BUTTON: Retry Game",
            "RIGHT BUTTON: Upgrade Shop",
            "MIDDLE BUTTON: Main Menu"
        ]
        
        for i, instruction in enumerate(instructions):
            self.draw_text_outlined(surface, instruction, 640, instructions_y + i * 35, 24, 
                                  (220, 240, 255), (40, 35, 50), 1)
        
    def draw_pause_menu(self, surface: pygame.Surface):
        overlay = pygame.Surface((1280, 720))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        surface.blit(overlay, (0, 0))
        
        # Titolo
        title = "GAME PAUSED"
        self.draw_text_outlined(surface, title, 640, 200, 86, (255, 220, 100), (70, 60, 0), 3)
        
        # Istruzioni
        instructions = [
            "MIDDLE BUTTON: Resume Game",
            "RIGHT BUTTON: Return to Menu",
            "LEFT BUTTON: Continue (when unpaused)"
        ]
        
        for i, instruction in enumerate(instructions):
            self.draw_text_outlined(surface, instruction, 640, 320 + i * 50, 32, 
                                  (220, 240, 255), (40, 35, 50), 1)
        
        # Statistiche
        stats_y = 500
        stats = [
            f"Time: {int(self.game_time)//60:02d}:{int(self.game_time)%60:02d}",
            f"Score: {self.score:,}",
            f"Level: {self.level}",
            f"Kills: {self.kill_count:,}",
            f"Wave: {self.wave_number}"
        ]
        
        for i, stat in enumerate(stats):
            self.draw_text_outlined(surface, stat, 640, stats_y + i * 40, 28,
                                  (200, 220, 255), (40, 35, 50), 1)
        
    def draw_upgrade_shop(self, surface: pygame.Surface):
        overlay = pygame.Surface((1280, 720))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        surface.blit(overlay, (0, 0))
        
        title = "UPGRADE SHOP"
        self.draw_text_outlined(surface, title, 640, 80, 72, (255, 220, 100), (70, 60, 0), 3)
        
        subtitle = f"Prestige Points: {self.prestige_points}"
        self.draw_text_outlined(surface, subtitle, 640, 150, 36, (220, 240, 255), (50, 45, 55), 2)
        
        # Upgrade disponibili
        upgrades_y = 250
        for i, (key, upgrade) in enumerate(self.upgrade_shop.items()):
            y = upgrades_y + i * 90
            x = 640
            
            can_afford = self.prestige_points >= upgrade['cost'] and upgrade['current_level'] < upgrade['max_level']
            
            # Box upgrade
            box_width = 600
            box_height = 80
            box_color = (70, 65, 90) if can_afford else (50, 45, 65)
            border_color = (255, 255, 255) if can_afford else (100, 100, 120)
            
            box_rect = pygame.Rect(x - box_width//2, y - box_height//2, box_width, box_height)
            pygame.draw.rect(surface, box_color, box_rect, 0, 15)
            pygame.draw.rect(surface, border_color, box_rect, 3, 15)
            
            # Nome e descrizione
            self.draw_text_outlined(surface, upgrade['name'], x - 200, y - 15, 26, 
                                  (255, 255, 255) if can_afford else (150, 150, 170), 
                                  (40, 35, 50), 1)
            self.draw_text(surface, upgrade['description'], x - 200, y + 15, 18, 
                          (200, 220, 240) if can_afford else (120, 130, 150))
            
            # Livello e costo
            level_text = f"Level: {upgrade['current_level']}/{upgrade['max_level']}"
            self.draw_text(surface, level_text, x + 150, y - 15, 22, (200, 220, 240))
            
            cost_text = f"Cost: {upgrade['cost']} PP"
            cost_color = (255, 220, 120) if can_afford else (180, 150, 100)
            self.draw_text(surface, cost_text, x + 150, y + 15, 22, cost_color)
        
        # Istruzioni
        instructions = "LEFT BUTTON: Back to Game  •  RIGHT BUTTON: Reset All"
        self.draw_text_outlined(surface, instructions, 640, 660, 24, (200, 230, 255), (35, 30, 45), 1)
        
    def wrap_text(self, text: str, max_chars: int) -> List[str]:
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
                
        if current_line:
            lines.append(current_line.strip())
            
        return lines
        
    def draw_text(self, surface: pygame.Surface, text: str, x: int, y: int,
                  size: int, color: Tuple[int, int, int], centered: bool = True):
        color = tuple(min(255, max(0, int(c))) for c in color)
        try:
            font = pygame.font.Font(None, size)
            text_surface = font.render(text, True, color)
            if centered:
                text_rect = text_surface.get_rect(center=(x, y))
            else:
                text_rect = text_surface.get_rect(midleft=(x, y))
            surface.blit(text_surface, text_rect)
        except:
            pass
        
    def draw_text_outlined(self, surface: pygame.Surface, text: str, x: int, y: int,
                          size: int, color: Tuple[int, int, int], outline_color: Tuple[int, int, int],
                          outline_width: int = 2):
        color = tuple(min(255, max(0, int(c))) for c in color)
        outline_color = tuple(min(255, max(0, int(c))) for c in outline_color)
        
        try:
            font = pygame.font.Font(None, size)
            
            # Outline
            for offset_x in range(-outline_width, outline_width + 1):
                for offset_y in range(-outline_width, outline_width + 1):
                    if offset_x != 0 or offset_y != 0:
                        outline_surface = font.render(text, True, outline_color)
                        outline_rect = outline_surface.get_rect(center=(x + offset_x, y + offset_y))
                        surface.blit(outline_surface, outline_rect)
                        
            # Testo principale
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect(center=(x, y))
            surface.blit(text_surface, text_rect)
        except:
            pass
