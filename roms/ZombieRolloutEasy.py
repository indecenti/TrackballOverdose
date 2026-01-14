import pygame
import math
import random
from collections import deque

class ZombieRolloutEasy(MiniGame):
    def __init__(self, *args, sound=None, **kwargs):
        super().__init__("Zombie Rollout Easy", "Survive the zombie apocalypse with your armed sphere!", *args, **kwargs)
        self.sound = sound
        self.reset()

    def reset(self):
        """Reset completo dello stato del gioco - OBBLIGATORIO secondo API"""
        self.score = 0
        self.is_game_over = False
        self.is_paused = False
        
        # Stato del gioco
        self.player_x = 640
        self.player_y = 410
        self.player_radius = 18
        self.player_health = 100
        self.player_max_health = 100
        self.player_speed = 280
        self.player_rotation = 0
        self.player_velocity_x = 0
        self.player_velocity_y = 0
        self.player_friction = 0.88
        
        self.dash_cooldown = 0
        self.dash_max_cooldown = 3.0
        self.dash_duration = 0
        self.dash_speed = 1000
        self.is_dashing = False
        
        self.shockwave_cooldown = 0
        self.shockwave_max_cooldown = 8.0
        self.shockwaves = []
        
        self.bullets = []
        self.bullet_speed = 700
        self.fire_rate = 0.2
        self.fire_timer = 0
        self.auto_fire = True
        self.piercing_shots = 0
        
        self.zombies = []
        self.particles = []
        self.blood_splats = []
        self.damage_numbers = []
        self.powerups = []
        self.xp_gems = []
        
        self.wave = 1
        self.zombies_per_wave = 15
        self.zombies_spawned_this_wave = 0
        self.zombies_killed_this_wave = 0
        self.spawn_timer = 0
        self.spawn_rate = 1.2
        self.wave_transition = False
        self.wave_transition_timer = 0
        self.max_zombies_on_screen = 150
        
        self.play_area_top = 120
        self.play_area_bottom = 720
        self.play_area_left = 0
        self.play_area_right = 1280
        
        self.combo_counter = 0
        self.combo_timer = 0
        self.combo_timeout = 2.0
        
        self.screen_shake = 0
        self.game_time = 0
        self.invulnerable_timer = 0
        
        self.xp = 0
        self.level = 1
        self.xp_to_next_level = 50
        
        self.weapon_level = 1
        self.bullet_damage = 20
        self.bullet_size = 5
        self.crit_chance = 0.05
        self.crit_multiplier = 2.0
        
        self.trail_points = deque(maxlen=12)
        
        self.boss_wave = False
        self.boss = None
        
        self.camera_x = 0
        self.camera_y = 0
        
        self.magnetism_range = 80
        self.pickup_range = 25
        
        self.hp_regen_rate = 0
        self.armor = 0
        self.move_speed_bonus = 0
        self.projectile_speed_bonus = 0
        self.area_damage_bonus = 0
        self.cooldown_reduction = 0
        self.luck = 0
        self.lifesteal = 0
        
        self.level_up_pending = False
        self.level_up_choices = []
        self.selected_choice = 0
        
        self.available_upgrades = {
            'max_health': {'name': 'Vitality', 'desc': '+25 Max HP', 'icon': 'H', 'color': (255, 100, 100)},
            'damage': {'name': 'Power', 'desc': '+15% Damage', 'icon': 'D', 'color': (255, 200, 0)},
            'fire_rate': {'name': 'Speed', 'desc': '-10% Fire Delay', 'icon': 'F', 'color': (255, 255, 0)},
            'projectiles': {'name': 'Multishot', 'desc': '+1 Projectile', 'icon': 'M', 'color': (255, 150, 255)},
            'move_speed': {'name': 'Agility', 'desc': '+8% Move Speed', 'icon': 'A', 'color': (100, 200, 255)},
            'crit_chance': {'name': 'Precision', 'desc': '+5% Crit Chance', 'icon': 'C', 'color': (255, 100, 255)},
            'area': {'name': 'Blast', 'desc': '+15% Area Damage', 'icon': 'B', 'color': (255, 150, 0)},
            'magnetism': {'name': 'Magnet', 'desc': '+40 Pickup Range', 'icon': 'G', 'color': (100, 255, 100)},
            'regen': {'name': 'Regeneration', 'desc': '+2 HP/sec', 'icon': 'R', 'color': (150, 255, 150)},
            'armor': {'name': 'Armor', 'desc': '+5% Damage Reduction', 'icon': 'S', 'color': (200, 200, 200)},
            'cooldown': {'name': 'Haste', 'desc': '-10% Cooldowns', 'icon': 'T', 'color': (150, 255, 255)},
            'lifesteal': {'name': 'Vampire', 'desc': '+5% Lifesteal', 'icon': 'V', 'color': (200, 50, 50)}
        }

    def update(self, dt, trackball):
        """Update logica di gioco - OBBLIGATORIO secondo API"""
        if self.is_game_over:
            return
        
        if self.level_up_pending:
            self.handle_level_up_input(trackball)
            return
        
        if self.is_paused:
            return
        
        self.game_time += dt
        self.fire_timer = max(0, self.fire_timer - dt)
        
        cooldown_mult = 1 - (self.cooldown_reduction * 0.01)
        self.dash_cooldown = max(0, self.dash_cooldown - dt / cooldown_mult)
        self.shockwave_cooldown = max(0, self.shockwave_cooldown - dt / cooldown_mult)
        
        self.combo_timer = max(0, self.combo_timer - dt)
        self.invulnerable_timer = max(0, self.invulnerable_timer - dt)
        
        if self.combo_timer <= 0 and self.combo_counter > 0:
            self.combo_counter = 0
        
        if self.hp_regen_rate > 0:
            self.player_health = min(self.player_max_health, self.player_health + self.hp_regen_rate * dt)
        
        # INPUT usando trackball API corretta
        dx, dy = trackball.get_smooth_delta()
        
        if not self.is_dashing:
            move_multiplier = 1.0
            if self.dash_duration > 0:
                move_multiplier = 0.3
                
            self.player_velocity_x += dx * self.player_speed * 5 * dt
            self.player_velocity_y += dy * self.player_speed * 5 * dt
            
            if abs(dx) > 0.01 or abs(dy) > 0.01:
                self.player_rotation = math.atan2(dy, dx)
        
        # INPUT bottoni secondo API
        if trackball.button_left and self.auto_fire:
            if self.fire_timer <= 0:
                self.shoot()
                self.fire_timer = self.fire_rate
        
        if trackball.button_left_pressed and not self.auto_fire:
            if self.fire_timer <= 0:
                self.shoot()
                self.fire_timer = self.fire_rate
        
        if trackball.button_right_pressed:
            if self.dash_cooldown <= 0:
                self.activate_dash()
                if self.sound:
                    self.sound.create_shoot().play()
        
        if trackball.button_middle_pressed:
            if self.shockwave_cooldown <= 0:
                self.activate_shockwave()
                if self.sound:
                    self.sound.create_combo(min(9, max(1, self.combo_counter // 3))).play()
        
        # Update fisica player
        self.update_player_physics(dt)
        self.update_bullets(dt)
        self.update_zombies(dt)
        self.update_boss(dt)
        self.update_collisions()
        self.update_particles(dt)
        self.update_powerups(dt)
        self.update_xp_gems(dt)
        self.update_damage_numbers(dt)
        self.update_shockwaves(dt)
        self.update_wave_system(dt)
        self.update_camera(dt)
        
        # Incremento punteggio secondo API
        self.score += int(15 * dt * (1 + self.combo_counter * 0.15))
        
        # Game Over secondo API
        if self.player_health <= 0:
            self.is_game_over = True
            self.score += self.wave * 2000 + self.zombies_killed_this_wave * 150
            if self.sound:
                self.sound.create_game_over().play()
            return

    def draw(self, surface):
        """Rendering - OBBLIGATORIO secondo API"""
        surface.fill((15, 15, 25))
        
        self.draw_background(surface)
        self.draw_blood_splats(surface)
        self.draw_trail(surface)
        self.draw_shockwaves(surface)
        self.draw_xp_gems(surface)
        self.draw_zombies(surface)
        self.draw_boss(surface)
        self.draw_bullets(surface)
        self.draw_powerups(surface)
        self.draw_player(surface)
        self.draw_particles(surface)
        self.draw_damage_numbers(surface)
        self.draw_ui(surface)
        
        if self.wave_transition:
            self.draw_wave_transition(surface)
        
        if self.level_up_pending:
            self.draw_level_up_screen(surface)
        
        if self.is_paused and not self.level_up_pending:
            self.draw_pause_overlay(surface)

    # ========== METODI DI GIOCO ==========

    def update_player_physics(self, dt):
        if self.dash_duration > 0:
            self.dash_duration -= dt
            dash_angle = self.player_rotation
            self.player_velocity_x = math.cos(dash_angle) * self.dash_speed
            self.player_velocity_y = math.sin(dash_angle) * self.dash_speed
            self.is_dashing = True
        else:
            self.is_dashing = False
            self.player_velocity_x *= self.player_friction
            self.player_velocity_y *= self.player_friction
        
        max_speed = self.player_speed if not self.is_dashing else self.dash_speed
        speed = math.sqrt(self.player_velocity_x**2 + self.player_velocity_y**2)
        if speed > max_speed:
            self.player_velocity_x = (self.player_velocity_x / speed) * max_speed
            self.player_velocity_y = (self.player_velocity_y / speed) * max_speed
        
        self.player_x += self.player_velocity_x * dt
        self.player_y += self.player_velocity_y * dt
        
        if self.player_x - self.player_radius < self.play_area_left:
            self.player_x = self.play_area_left + self.player_radius
            self.player_velocity_x *= -0.5
        if self.player_x + self.player_radius > self.play_area_right:
            self.player_x = self.play_area_right - self.player_radius
            self.player_velocity_x *= -0.5
        if self.player_y - self.player_radius < self.play_area_top:
            self.player_y = self.play_area_top + self.player_radius
            self.player_velocity_y *= -0.5
        if self.player_y + self.player_radius > self.play_area_bottom:
            self.player_y = self.play_area_bottom - self.player_radius
            self.player_velocity_y *= -0.5
        
        if speed > 50:
            self.trail_points.append((self.player_x, self.player_y))

    def shoot(self):
        nearest_zombie = self.find_nearest_zombie()
        
        if nearest_zombie:
            angle = math.atan2(nearest_zombie['y'] - self.player_y, 
                             nearest_zombie['x'] - self.player_x)
        else:
            angle = self.player_rotation
        
        bullet_offset = self.player_radius + 5
        bullet_x = self.player_x + math.cos(angle) * bullet_offset
        bullet_y = self.player_y + math.sin(angle) * bullet_offset
        
        spread_angles = [0]
        if self.weapon_level >= 2:
            spread_angles = [-0.12, 0.12]
        if self.weapon_level >= 3:
            spread_angles = [-0.15, 0, 0.15]
        if self.weapon_level >= 4:
            spread_angles = [-0.2, -0.07, 0.07, 0.2]
        if self.weapon_level >= 5:
            spread_angles = [-0.25, -0.12, 0, 0.12, 0.25]
        if self.weapon_level >= 6:
            spread_angles = [-0.3, -0.18, -0.06, 0.06, 0.18, 0.3]
        if self.weapon_level >= 7:
            spread_angles = [-0.35, -0.23, -0.11, 0, 0.11, 0.23, 0.35]
        
        is_crit = random.random() < self.crit_chance
        damage = self.bullet_damage * (self.crit_multiplier if is_crit else 1.0)
        
        for spread in spread_angles:
            bullet_angle = angle + spread
            self.bullets.append({
                'x': bullet_x,
                'y': bullet_y,
                'vx': math.cos(bullet_angle) * (self.bullet_speed + self.projectile_speed_bonus),
                'vy': math.sin(bullet_angle) * (self.bullet_speed + self.projectile_speed_bonus),
                'lifetime': 3.0,
                'damage': damage,
                'size': self.bullet_size + (2 if is_crit else 0),
                'is_crit': is_crit,
                'pierce_count': self.piercing_shots
            })
        
        for _ in range(3):
            particle_angle = angle + random.uniform(-0.3, 0.3)
            self.particles.append({
                'x': bullet_x,
                'y': bullet_y,
                'vx': math.cos(particle_angle) * random.uniform(100, 200),
                'vy': math.sin(particle_angle) * random.uniform(100, 200),
                'lifetime': random.uniform(0.2, 0.4),
                'max_lifetime': 0.4,
                'size': random.uniform(2, 4),
                'color': (255, 150, 150) if is_crit else (255, 255, 150)
            })
        
        if self.sound:
            self.sound.create_shoot().play()

    def find_nearest_zombie(self):
        nearest = None
        min_dist = float('inf')
        
        for zombie in self.zombies:
            dist = math.sqrt((zombie['x'] - self.player_x)**2 + 
                           (zombie['y'] - self.player_y)**2)
            if dist < min_dist:
                min_dist = dist
                nearest = zombie
        
        if self.boss:
            dist = math.sqrt((self.boss['x'] - self.player_x)**2 + 
                           (self.boss['y'] - self.player_y)**2)
            if dist < min_dist:
                nearest = self.boss
        
        return nearest

    def activate_dash(self):
        self.dash_duration = 0.2
        self.dash_cooldown = self.dash_max_cooldown
        self.invulnerable_timer = 0.2
        
        for _ in range(15):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(150, 350)
            self.particles.append({
                'x': self.player_x,
                'y': self.player_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': random.uniform(0.3, 0.7),
                'max_lifetime': 0.7,
                'size': random.uniform(3, 7),
                'color': (100, 200, 255)
            })

    def activate_shockwave(self):
        self.shockwave_cooldown = self.shockwave_max_cooldown
        base_damage = 40 + (self.area_damage_bonus * 0.4)
        self.shockwaves.append({
            'x': self.player_x,
            'y': self.player_y,
            'radius': 0,
            'max_radius': 180 + self.area_damage_bonus,
            'lifetime': 0.8,
            'damage': base_damage
        })
        self.screen_shake = 0.6

    def update_shockwaves(self, dt):
        for wave in self.shockwaves[:]:
            wave['lifetime'] -= dt
            wave['radius'] += 500 * dt
            
            if wave['lifetime'] <= 0 or wave['radius'] > wave['max_radius']:
                self.shockwaves.remove(wave)
                continue
            
            for zombie in self.zombies[:]:
                dist = math.sqrt((zombie['x'] - wave['x'])**2 + 
                               (zombie['y'] - wave['y'])**2)
                if dist <= wave['radius'] and dist >= wave['radius'] - 25:
                    if not zombie.get('hit_by_wave_' + str(id(wave))):
                        self.damage_zombie(zombie, wave['damage'])
                        zombie['hit_by_wave_' + str(id(wave))] = True
                        
                        knockback_angle = math.atan2(zombie['y'] - wave['y'], 
                                                    zombie['x'] - wave['x'])
                        zombie['vx'] += math.cos(knockback_angle) * 500
                        zombie['vy'] += math.sin(knockback_angle) * 500
            
            if self.boss:
                dist = math.sqrt((self.boss['x'] - wave['x'])**2 + 
                               (self.boss['y'] - wave['y'])**2)
                if dist <= wave['radius'] and dist >= wave['radius'] - 25:
                    if not self.boss.get('hit_by_wave_' + str(id(wave))):
                        self.damage_zombie(self.boss, wave['damage'])
                        self.boss['hit_by_wave_' + str(id(wave))] = True

    def update_bullets(self, dt):
        for bullet in self.bullets[:]:
            bullet['lifetime'] -= dt
            if bullet['lifetime'] <= 0:
                self.bullets.remove(bullet)
                continue
            
            bullet['x'] += bullet['vx'] * dt
            bullet['y'] += bullet['vy'] * dt
            
            if (bullet['x'] < self.play_area_left or bullet['x'] > self.play_area_right or
                bullet['y'] < self.play_area_top or bullet['y'] > self.play_area_bottom):
                self.bullets.remove(bullet)

    def spawn_zombie(self, zombie_type='normal'):
        if len(self.zombies) >= self.max_zombies_on_screen:
            return
        
        side = random.randint(0, 3)
        if side == 0:
            zombie_x = random.uniform(self.play_area_left, self.play_area_right)
            zombie_y = self.play_area_top - 20
        elif side == 1:
            zombie_x = self.play_area_right + 20
            zombie_y = random.uniform(self.play_area_top, self.play_area_bottom)
        elif side == 2:
            zombie_x = random.uniform(self.play_area_left, self.play_area_right)
            zombie_y = self.play_area_bottom + 20
        else:
            zombie_x = self.play_area_left - 20
            zombie_y = random.uniform(self.play_area_top, self.play_area_bottom)
        
        wave_mult = 1 + (self.wave - 1) * 0.15
        
        if zombie_type == 'fast':
            zombie = {
                'x': zombie_x,
                'y': zombie_y,
                'vx': 0,
                'vy': 0,
                'speed': (120 + self.wave * 4) * wave_mult,
                'health': (25 + self.wave * 3) * wave_mult,
                'max_health': (25 + self.wave * 3) * wave_mult,
                'damage': 8 * wave_mult,
                'radius': 11,
                'color': (255, 100, 100),
                'type': 'fast',
                'animation_timer': 0
            }
        elif zombie_type == 'tank':
            zombie = {
                'x': zombie_x,
                'y': zombie_y,
                'vx': 0,
                'vy': 0,
                'speed': (40 + self.wave * 2) * wave_mult,
                'health': (120 + self.wave * 25) * wave_mult,
                'max_health': (120 + self.wave * 25) * wave_mult,
                'damage': 20 * wave_mult,
                'radius': 22,
                'color': (150, 150, 100),
                'type': 'tank',
                'animation_timer': 0
            }
        elif zombie_type == 'exploder':
            zombie = {
                'x': zombie_x,
                'y': zombie_y,
                'vx': 0,
                'vy': 0,
                'speed': (70 + self.wave * 3) * wave_mult,
                'health': (40 + self.wave * 8) * wave_mult,
                'max_health': (40 + self.wave * 8) * wave_mult,
                'damage': 30 * wave_mult,
                'radius': 14,
                'color': (255, 150, 0),
                'type': 'exploder',
                'animation_timer': 0,
                'explosion_radius': 90
            }
        else:
            zombie = {
                'x': zombie_x,
                'y': zombie_y,
                'vx': 0,
                'vy': 0,
                'speed': (65 + self.wave * 3) * wave_mult,
                'health': (45 + self.wave * 8) * wave_mult,
                'max_health': (45 + self.wave * 8) * wave_mult,
                'damage': 12 * wave_mult,
                'radius': 15,
                'color': (100, 200, 100),
                'type': 'normal',
                'animation_timer': 0
            }
        
        self.zombies.append(zombie)
        self.zombies_spawned_this_wave += 1

    def spawn_boss(self):
        side = random.randint(0, 3)
        if side == 0:
            boss_x = 640
            boss_y = self.play_area_top - 50
        elif side == 1:
            boss_x = self.play_area_right + 50
            boss_y = 410
        elif side == 2:
            boss_x = 640
            boss_y = self.play_area_bottom + 50
        else:
            boss_x = self.play_area_left - 50
            boss_y = 410
        
        wave_mult = 1 + (self.wave - 1) * 0.2
        
        self.boss = {
            'x': boss_x,
            'y': boss_y,
            'vx': 0,
            'vy': 0,
            'speed': 55 * wave_mult,
            'health': (2000 + self.wave * 800) * wave_mult,
            'max_health': (2000 + self.wave * 800) * wave_mult,
            'damage': 35 * wave_mult,
            'radius': 45,
            'color': (200, 50, 50),
            'type': 'boss',
            'animation_timer': 0,
            'charge_timer': 0,
            'charge_cooldown': 2.5,
            'is_charging': False,
            'charge_target_x': 0,
            'charge_target_y': 0,
            'spawn_timer': 0,
            'spawn_cooldown': 4.0
        }

    def update_zombies(self, dt):
        for zombie in self.zombies[:]:
            zombie['animation_timer'] += dt
            
            angle_to_player = math.atan2(self.player_y - zombie['y'], 
                                        self.player_x - zombie['x'])
            
            target_vx = math.cos(angle_to_player) * zombie['speed']
            target_vy = math.sin(angle_to_player) * zombie['speed']
            
            zombie['vx'] = zombie.get('vx', 0) * 0.9 + target_vx * 0.1
            zombie['vy'] = zombie.get('vy', 0) * 0.9 + target_vy * 0.1
            
            zombie['x'] += zombie['vx'] * dt
            zombie['y'] += zombie['vy'] * dt
            
            if zombie['x'] < self.play_area_left - 50 or zombie['x'] > self.play_area_right + 50:
                self.zombies.remove(zombie)
            elif zombie['y'] < self.play_area_top - 50 or zombie['y'] > self.play_area_bottom + 50:
                self.zombies.remove(zombie)

    def update_boss(self, dt):
        if not self.boss:
            return
        
        self.boss['animation_timer'] += dt
        self.boss['charge_timer'] += dt
        self.boss['spawn_timer'] += dt
        
        if self.boss['spawn_timer'] >= self.boss['spawn_cooldown']:
            self.boss['spawn_timer'] = 0
            for _ in range(3):
                zombie_type = random.choice(['normal', 'fast'])
                self.spawn_zombie(zombie_type)
        
        if self.boss['charge_timer'] >= self.boss['charge_cooldown'] and not self.boss['is_charging']:
            self.boss['is_charging'] = True
            self.boss['charge_target_x'] = self.player_x
            self.boss['charge_target_y'] = self.player_y
            self.boss['charge_timer'] = 0
            self.screen_shake = 0.3
            
            if self.sound:
                self.sound.create_combo(6).play()
        
        if self.boss['is_charging']:
            angle_to_target = math.atan2(self.boss['charge_target_y'] - self.boss['y'], 
                                        self.boss['charge_target_x'] - self.boss['x'])
            
            charge_speed = 400
            self.boss['vx'] = math.cos(angle_to_target) * charge_speed
            self.boss['vy'] = math.sin(angle_to_target) * charge_speed
            
            if self.boss['charge_timer'] >= 1.2:
                self.boss['is_charging'] = False
                self.boss['charge_timer'] = 0
        else:
            angle_to_player = math.atan2(self.player_y - self.boss['y'], 
                                        self.player_x - self.boss['x'])
            
            target_vx = math.cos(angle_to_player) * self.boss['speed']
            target_vy = math.sin(angle_to_player) * self.boss['speed']
            
            self.boss['vx'] = self.boss.get('vx', 0) * 0.95 + target_vx * 0.05
            self.boss['vy'] = self.boss.get('vy', 0) * 0.95 + target_vy * 0.05
        
        self.boss['x'] += self.boss['vx'] * dt
        self.boss['y'] += self.boss['vy'] * dt
        
        if self.boss['x'] - self.boss['radius'] < self.play_area_left:
            self.boss['x'] = self.play_area_left + self.boss['radius']
            self.boss['vx'] *= -0.7
        if self.boss['x'] + self.boss['radius'] > self.play_area_right:
            self.boss['x'] = self.play_area_right - self.boss['radius']
            self.boss['vx'] *= -0.7
        if self.boss['y'] - self.boss['radius'] < self.play_area_top:
            self.boss['y'] = self.play_area_top + self.boss['radius']
            self.boss['vy'] *= -0.7
        if self.boss['y'] + self.boss['radius'] > self.play_area_bottom:
            self.boss['y'] = self.play_area_bottom - self.boss['radius']
            self.boss['vy'] *= -0.7

    def update_collisions(self):
        for bullet in self.bullets[:]:
            hit_something = False
            
            for zombie in self.zombies[:]:
                dist = math.sqrt((bullet['x'] - zombie['x'])**2 + 
                               (bullet['y'] - zombie['y'])**2)
                if dist < zombie['radius'] + bullet['size']:
                    self.damage_zombie(zombie, bullet['damage'])
                    hit_something = True
                    
                    if bullet['pierce_count'] <= 0:
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break
                    else:
                        bullet['pierce_count'] -= 1
            
            if not hit_something and self.boss and bullet in self.bullets:
                dist = math.sqrt((bullet['x'] - self.boss['x'])**2 + 
                               (bullet['y'] - self.boss['y'])**2)
                if dist < self.boss['radius'] + bullet['size']:
                    self.damage_zombie(self.boss, bullet['damage'])
                    
                    if bullet['pierce_count'] <= 0:
                        self.bullets.remove(bullet)
                    else:
                        bullet['pierce_count'] -= 1
        
        if self.invulnerable_timer <= 0:
            for zombie in self.zombies:
                dist = math.sqrt((self.player_x - zombie['x'])**2 + 
                               (self.player_y - zombie['y'])**2)
                if dist < self.player_radius + zombie['radius']:
                    damage = zombie['damage'] * (1 - self.armor / 100)
                    self.player_health -= damage
                    self.invulnerable_timer = 0.4
                    self.screen_shake = 0.3
                    self.combo_counter = 0
                    
                    knockback_angle = math.atan2(self.player_y - zombie['y'], 
                                                self.player_x - zombie['x'])
                    self.player_velocity_x = math.cos(knockback_angle) * 350
                    self.player_velocity_y = math.sin(knockback_angle) * 350
                    
                    if self.sound:
                        self.sound.create_target_hit().play()
                    break
            
            if self.boss:
                dist = math.sqrt((self.player_x - self.boss['x'])**2 + 
                               (self.player_y - self.boss['y'])**2)
                if dist < self.player_radius + self.boss['radius']:
                    damage = self.boss['damage'] * (1 - self.armor / 100)
                    self.player_health -= damage
                    self.invulnerable_timer = 0.5
                    self.screen_shake = 0.6
                    self.combo_counter = 0
                    
                    knockback_angle = math.atan2(self.player_y - self.boss['y'], 
                                                self.player_x - self.boss['x'])
                    self.player_velocity_x = math.cos(knockback_angle) * 500
                    self.player_velocity_y = math.sin(knockback_angle) * 500
                    
                    if self.sound:
                        self.sound.create_combo(8).play()

    def damage_zombie(self, zombie, damage):
        zombie['health'] -= damage
        
        if self.lifesteal > 0:
            heal = damage * (self.lifesteal / 100)
            self.player_health = min(self.player_max_health, self.player_health + heal)
        
        self.damage_numbers.append({
            'x': zombie['x'],
            'y': zombie['y'] - zombie['radius'],
            'damage': int(damage),
            'lifetime': 0.8,
            'vy': -60
        })
        
        for _ in range(4):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 150)
            self.particles.append({
                'x': zombie['x'],
                'y': zombie['y'],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': random.uniform(0.3, 0.6),
                'max_lifetime': 0.6,
                'size': random.uniform(2, 5),
                'color': (200, 0, 0)
            })
        
        if zombie['health'] <= 0:
            self.kill_zombie(zombie)

    def kill_zombie(self, zombie):
        if zombie == self.boss:
            self.score += 10000
            self.xp += 200
            
            for _ in range(80):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(150, 500)
                self.particles.append({
                    'x': zombie['x'],
                    'y': zombie['y'],
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'lifetime': random.uniform(0.6, 2.0),
                    'max_lifetime': 2.0,
                    'size': random.uniform(5, 12),
                    'color': (255, 150, 0)
                })
            
            self.blood_splats.append({
                'x': zombie['x'],
                'y': zombie['y'],
                'radius': zombie['radius'] * 3,
                'alpha': 180
            })
            
            for _ in range(15):
                self.spawn_xp_gem(zombie['x'] + random.uniform(-60, 60), 
                                 zombie['y'] + random.uniform(-60, 60), 20)
            
            if self.sound:
                self.sound.create_high_score().play()
            
            self.screen_shake = 1.2
            self.boss = None
            
            return
        
        if zombie in self.zombies:
            self.zombies.remove(zombie)
        
        self.zombies_killed_this_wave += 1
        self.combo_counter += 1
        self.combo_timer = self.combo_timeout
        
        score_multiplier = 1 + (self.combo_counter * 0.12)
        zombie_score = 50
        xp_value = 3
        
        if zombie['type'] == 'fast':
            zombie_score = 75
            xp_value = 4
        elif zombie['type'] == 'tank':
            zombie_score = 120
            xp_value = 8
        elif zombie['type'] == 'exploder':
            zombie_score = 90
            xp_value = 6
        
        self.score += int(zombie_score * score_multiplier)
        
        if zombie['type'] == 'exploder':
            self.create_explosion(zombie['x'], zombie['y'], zombie['explosion_radius'])
        
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 220)
            self.particles.append({
                'x': zombie['x'],
                'y': zombie['y'],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': random.uniform(0.4, 1.0),
                'max_lifetime': 1.0,
                'size': random.uniform(3, 7),
                'color': zombie['color']
            })
        
        self.blood_splats.append({
            'x': zombie['x'],
            'y': zombie['y'],
            'radius': zombie['radius'] * 2,
            'alpha': 120
        })
        
        if self.combo_counter % 10 == 0 and self.sound:
            self.sound.create_combo(min(9, self.combo_counter // 10)).play()
        elif self.combo_counter % 5 == 0 and self.sound:
            self.sound.create_target_hit().play()
        
        drop_chance = 0.4 + (self.luck * 0.01)
        if random.random() < drop_chance:
            for _ in range(xp_value):
                offset_x = random.uniform(-15, 15)
                offset_y = random.uniform(-15, 15)
                self.spawn_xp_gem(zombie['x'] + offset_x, zombie['y'] + offset_y, 5)

    def spawn_xp_gem(self, x, y, value):
        self.xp_gems.append({
            'x': x,
            'y': y,
            'value': value,
            'lifetime': 30.0,
            'radius': 8,
            'animation_timer': 0,
            'vx': random.uniform(-50, 50),
            'vy': random.uniform(-50, 50)
        })

    def update_xp_gems(self, dt):
        for gem in self.xp_gems[:]:
            gem['lifetime'] -= dt
            gem['animation_timer'] += dt
            
            if gem['lifetime'] <= 0:
                self.xp_gems.remove(gem)
                continue
            
            gem['vx'] *= 0.95
            gem['vy'] *= 0.95
            gem['x'] += gem['vx'] * dt
            gem['y'] += gem['vy'] * dt
            
            dist = math.sqrt((self.player_x - gem['x'])**2 + 
                           (self.player_y - gem['y'])**2)
            
            if dist < self.magnetism_range:
                angle_to_player = math.atan2(self.player_y - gem['y'], 
                                            self.player_x - gem['x'])
                magnet_speed = 300
                gem['x'] += math.cos(angle_to_player) * magnet_speed * dt
                gem['y'] += math.sin(angle_to_player) * magnet_speed * dt
            
            if dist < self.pickup_range:
                self.xp += gem['value']
                self.xp_gems.remove(gem)
                
                if self.sound:
                    self.sound.create_target_hit().play()
                
                if self.xp >= self.xp_to_next_level:
                    self.trigger_level_up()

    def trigger_level_up(self):
        self.level += 1
        self.xp -= self.xp_to_next_level
        self.xp_to_next_level = int(self.xp_to_next_level * 1.3)
        
        available_keys = list(self.available_upgrades.keys())
        random.shuffle(available_keys)
        self.level_up_choices = available_keys[:3]
        
        self.level_up_pending = True
        self.selected_choice = 0
        
        if self.sound:
            self.sound.create_pause().play()

    def create_explosion(self, x, y, radius):
        for _ in range(40):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(120, 350)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': random.uniform(0.5, 1.2),
                'max_lifetime': 1.2,
                'size': random.uniform(5, 14),
                'color': (255, 150, 0)
            })
        
        self.screen_shake = 0.7
        
        if self.sound:
            self.sound.create_combo(7).play()
        
        explosion_damage = 60 + self.area_damage_bonus
        
        for zombie in self.zombies[:]:
            dist = math.sqrt((zombie['x'] - x)**2 + (zombie['y'] - y)**2)
            if dist < radius:
                self.damage_zombie(zombie, explosion_damage)
        
        if self.boss:
            dist = math.sqrt((self.boss['x'] - x)**2 + (self.boss['y'] - y)**2)
            if dist < radius:
                self.damage_zombie(self.boss, explosion_damage)
        
        player_dist = math.sqrt((self.player_x - x)**2 + (self.player_y - y)**2)
        if player_dist < radius and self.invulnerable_timer <= 0:
            damage = 15 * (1 - self.armor / 100)
            self.player_health -= damage
            self.invulnerable_timer = 0.4

    def update_powerups(self, dt):
        for powerup in self.powerups[:]:
            powerup['lifetime'] -= dt
            powerup['animation_timer'] += dt
            
            if powerup['lifetime'] <= 0:
                self.powerups.remove(powerup)
                continue
            
            dist = math.sqrt((self.player_x - powerup['x'])**2 + 
                           (self.player_y - powerup['y'])**2)
            
            if dist < self.player_radius + powerup['radius']:
                self.collect_powerup(powerup)
                self.powerups.remove(powerup)

    def collect_powerup(self, powerup):
        if powerup['type'] == 'health':
            heal_amount = 40
            self.player_health = min(self.player_max_health, self.player_health + heal_amount)
            
            for _ in range(12):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(60, 180)
                self.particles.append({
                    'x': powerup['x'],
                    'y': powerup['y'],
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'lifetime': random.uniform(0.3, 0.7),
                    'max_lifetime': 0.7,
                    'size': random.uniform(2, 6),
                    'color': (0, 255, 0)
                })
        
        self.score += 100
        
        if self.sound:
            self.sound.create_combo(3).play()

    def update_particles(self, dt):
        for particle in self.particles[:]:
            particle['lifetime'] -= dt
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)
                continue
            
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            
            particle['vx'] *= 0.96
            particle['vy'] *= 0.96

    def update_damage_numbers(self, dt):
        for number in self.damage_numbers[:]:
            number['lifetime'] -= dt
            if number['lifetime'] <= 0:
                self.damage_numbers.remove(number)
                continue
            
            number['y'] += number['vy'] * dt
            number['vy'] += 80 * dt

    def update_wave_system(self, dt):
        if self.wave_transition:
            self.wave_transition_timer -= dt
            if self.wave_transition_timer <= 0:
                self.wave_transition = False
                self.wave += 1
                self.zombies_spawned_this_wave = 0
                self.zombies_killed_this_wave = 0
                self.zombies_per_wave = int(15 + self.wave * 8)
                
                if self.wave % 5 == 0:
                    self.boss_wave = True
                else:
                    self.boss_wave = False
                
                if self.sound:
                    self.sound.create_game_start().play()
            return
        
        if self.boss_wave:
            if not self.boss:
                if self.zombies_spawned_this_wave == 0:
                    self.spawn_boss()
                    self.zombies_spawned_this_wave = 1
            else:
                return
            
            if not self.boss and len(self.zombies) == 0:
                self.wave_transition = True
                self.wave_transition_timer = 2.5
                self.boss_wave = False
        else:
            if self.zombies_spawned_this_wave < self.zombies_per_wave:
                self.spawn_timer += dt
                
                spawn_rate = max(0.3, self.spawn_rate - self.wave * 0.03)
                
                if self.spawn_timer >= spawn_rate:
                    self.spawn_timer = 0
                    
                    rand = random.random()
                    if rand < 0.45:
                        self.spawn_zombie('normal')
                    elif rand < 0.7:
                        self.spawn_zombie('fast')
                    elif rand < 0.88:
                        self.spawn_zombie('tank')
                    else:
                        self.spawn_zombie('exploder')
            
            if self.zombies_spawned_this_wave >= self.zombies_per_wave and len(self.zombies) == 0:
                self.wave_transition = True
                self.wave_transition_timer = 2.5

    def update_camera(self, dt):
        if self.screen_shake > 0:
            self.screen_shake -= dt
            self.camera_x = random.uniform(-self.screen_shake * 20, self.screen_shake * 20)
            self.camera_y = random.uniform(-self.screen_shake * 20, self.screen_shake * 20)
        else:
            self.camera_x = 0
            self.camera_y = 0

    def handle_level_up_input(self, trackball):
        dx, dy = trackball.get_smooth_delta()
        
        if dx > 0.3:
            self.selected_choice = min(2, self.selected_choice + 1)
            if self.sound:
                self.sound.create_shoot().play()
        elif dx < -0.3:
            self.selected_choice = max(0, self.selected_choice - 1)
            if self.sound:
                self.sound.create_shoot().play()
        
        if trackball.button_left_pressed or trackball.button_right_pressed or trackball.button_middle_pressed:
            self.apply_upgrade(self.level_up_choices[self.selected_choice])
            self.level_up_pending = False
            self.level_up_choices = []
            self.selected_choice = 0
            if self.sound:
                self.sound.create_high_score().play()

    def apply_upgrade(self, upgrade_key):
        if upgrade_key == 'max_health':
            self.player_max_health += 25
            self.player_health = min(self.player_max_health, self.player_health + 25)
        elif upgrade_key == 'damage':
            self.bullet_damage = int(self.bullet_damage * 1.15)
        elif upgrade_key == 'fire_rate':
            self.fire_rate = max(0.05, self.fire_rate * 0.9)
        elif upgrade_key == 'projectiles':
            self.weapon_level = min(7, self.weapon_level + 1)
        elif upgrade_key == 'move_speed':
            self.move_speed_bonus += 8
            self.player_speed = 280 * (1 + self.move_speed_bonus / 100)
        elif upgrade_key == 'crit_chance':
            self.crit_chance = min(0.75, self.crit_chance + 0.05)
        elif upgrade_key == 'area':
            self.area_damage_bonus += 15
        elif upgrade_key == 'magnetism':
            self.magnetism_range += 40
        elif upgrade_key == 'regen':
            self.hp_regen_rate += 2
        elif upgrade_key == 'armor':
            self.armor = min(50, self.armor + 5)
        elif upgrade_key == 'cooldown':
            self.cooldown_reduction = min(50, self.cooldown_reduction + 10)
        elif upgrade_key == 'lifesteal':
            self.lifesteal = min(30, self.lifesteal + 5)

    # ========== METODI DI RENDERING ==========

    def draw_background(self, surface):
        grid_size = 50
        grid_color = (25, 25, 35)
        
        offset_x = int(self.camera_x) % grid_size
        offset_y = int(self.camera_y) % grid_size
        
        for x in range(-grid_size + offset_x, 1280 + grid_size, grid_size):
            pygame.draw.line(surface, grid_color, (x, self.play_area_top), (x, self.play_area_bottom), 1)
        
        for y in range(self.play_area_top - grid_size + offset_y, self.play_area_bottom + grid_size, grid_size):
            pygame.draw.line(surface, grid_color, (0, y), (1280, y), 1)
        
        border_color = (60, 60, 80)
        pygame.draw.rect(surface, border_color, 
                        (self.play_area_left, self.play_area_top, 
                         self.play_area_right - self.play_area_left, 
                         self.play_area_bottom - self.play_area_top), 3)

    def draw_blood_splats(self, surface):
        for splat in self.blood_splats[:]:
            splat['alpha'] -= 0.3
            if splat['alpha'] <= 0:
                self.blood_splats.remove(splat)
                continue
            
            draw_x = int(splat['x'] + self.camera_x)
            draw_y = int(splat['y'] + self.camera_y)
            
            splat_surface = pygame.Surface((splat['radius'] * 2, splat['radius'] * 2), pygame.SRCALPHA)
            color = (100, 0, 0, int(splat['alpha']))
            pygame.draw.circle(splat_surface, color, (splat['radius'], splat['radius']), splat['radius'])
            surface.blit(splat_surface, (draw_x - splat['radius'], draw_y - splat['radius']))

    def draw_trail(self, surface):
        if len(self.trail_points) < 2:
            return
        
        for i, (x, y) in enumerate(self.trail_points):
            alpha = int(200 * (i / len(self.trail_points)))
            radius = int(self.player_radius * 0.6 * (i / len(self.trail_points)))
            
            if radius < 2:
                continue
            
            draw_x = int(x + self.camera_x)
            draw_y = int(y + self.camera_y)
            
            trail_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            color = (100, 200, 255, alpha // 2)
            pygame.draw.circle(trail_surface, color, (radius, radius), radius)
            surface.blit(trail_surface, (draw_x - radius, draw_y - radius))

    def draw_player(self, surface):
        draw_x = int(self.player_x + self.camera_x)
        draw_y = int(self.player_y + self.camera_y)
        
        if self.invulnerable_timer > 0 and int(self.invulnerable_timer * 25) % 2 == 0:
            return
        
        glow_radius = int(self.player_radius * 1.6)
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        glow_color = (100, 200, 255, 120)
        pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surface, (draw_x - glow_radius, draw_y - glow_radius))
        
        pygame.draw.circle(surface, (70, 140, 200), (draw_x, draw_y), self.player_radius)
        pygame.draw.circle(surface, (110, 190, 255), (draw_x, draw_y), self.player_radius, 3)
        
        barrel_length = self.player_radius + 10
        barrel_end_x = draw_x + math.cos(self.player_rotation) * barrel_length
        barrel_end_y = draw_y + math.sin(self.player_rotation) * barrel_length
        pygame.draw.line(surface, (200, 200, 50), (draw_x, draw_y), (barrel_end_x, barrel_end_y), 5)
        pygame.draw.circle(surface, (255, 255, 100), (int(barrel_end_x), int(barrel_end_y)), 4)
        
        eye_offset = self.player_radius * 0.4
        eye_x = draw_x + math.cos(self.player_rotation) * eye_offset
        eye_y = draw_y + math.sin(self.player_rotation) * eye_offset
        pygame.draw.circle(surface, (255, 255, 255), (int(eye_x), int(eye_y)), 5)
        pygame.draw.circle(surface, (0, 0, 0), (int(eye_x), int(eye_y)), 2)

    def draw_zombies(self, surface):
        for zombie in self.zombies:
            draw_x = int(zombie['x'] + self.camera_x)
            draw_y = int(zombie['y'] + self.camera_y)
            
            if draw_x < -50 or draw_x > 1330 or draw_y < 70 or draw_y > 770:
                continue
            
            wobble = math.sin(zombie['animation_timer'] * 12) * 2
            draw_y += int(wobble)
            
            shadow_surface = pygame.Surface((zombie['radius'] * 2, zombie['radius'] * 2), pygame.SRCALPHA)
            shadow_color = (0, 0, 0, 60)
            pygame.draw.ellipse(shadow_surface, shadow_color, (0, zombie['radius'], zombie['radius'] * 2, zombie['radius']))
            surface.blit(shadow_surface, (draw_x - zombie['radius'], draw_y))
            
            body_color = zombie['color']
            pygame.draw.circle(surface, body_color, (draw_x, draw_y), zombie['radius'])
            
            darker_color = tuple(max(0, c - 50) for c in body_color)
            pygame.draw.circle(surface, darker_color, (draw_x, draw_y), zombie['radius'], 2)
            
            if zombie['type'] == 'exploder':
                pulse = abs(math.sin(zombie['animation_timer'] * 6))
                glow_radius = int(zombie['radius'] * (1 + pulse * 0.4))
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                glow_color = (255, 150, 0, int(120 * pulse))
                pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
                surface.blit(glow_surface, (draw_x - glow_radius, draw_y - glow_radius))
            
            eye_offset = zombie['radius'] * 0.4
            left_eye_x = draw_x - 4
            right_eye_x = draw_x + 4
            eye_y = draw_y - eye_offset
            
            pygame.draw.circle(surface, (255, 0, 0), (left_eye_x, int(eye_y)), 3)
            pygame.draw.circle(surface, (255, 0, 0), (right_eye_x, int(eye_y)), 3)
            
            if zombie['type'] != 'fast' or zombie['health'] < zombie['max_health']:
                health_bar_width = zombie['radius'] * 2
                health_bar_height = 3
                health_bar_x = draw_x - zombie['radius']
                health_bar_y = draw_y - zombie['radius'] - 8
                
                health_ratio = zombie['health'] / zombie['max_health']
                health_color = (255, 0, 0) if health_ratio < 0.3 else (255, 165, 0) if health_ratio < 0.6 else (0, 255, 0)
                pygame.draw.rect(surface, (40, 40, 40), 
                               (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
                pygame.draw.rect(surface, health_color, 
                               (health_bar_x, health_bar_y, int(health_bar_width * health_ratio), health_bar_height))

    def draw_boss(self, surface):
        if not self.boss:
            return
        
        boss = self.boss
        draw_x = int(boss['x'] + self.camera_x)
        draw_y = int(boss['y'] + self.camera_y)
        
        if boss['is_charging']:
            charge_glow = abs(math.sin(boss['charge_timer'] * 25))
            glow_radius = int(boss['radius'] * (1.4 + charge_glow * 0.4))
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            glow_color = (255, 50, 50, int(180 * charge_glow))
            pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surface, (draw_x - glow_radius, draw_y - glow_radius))
        
        wobble = math.sin(boss['animation_timer'] * 10) * 4
        draw_y += int(wobble)
        
        shadow_surface = pygame.Surface((boss['radius'] * 3, boss['radius'] * 2), pygame.SRCALPHA)
        shadow_color = (0, 0, 0, 100)
        pygame.draw.ellipse(shadow_surface, shadow_color, (0, 0, boss['radius'] * 3, boss['radius'] * 2))
        surface.blit(shadow_surface, (draw_x - boss['radius'] * 1.5, draw_y + boss['radius'] * 0.3))
        
        pygame.draw.circle(surface, boss['color'], (draw_x, draw_y), boss['radius'])
        pygame.draw.circle(surface, (150, 30, 30), (draw_x, draw_y), boss['radius'], 5)
        
        for i in range(12):
            angle = (i / 12) * math.pi * 2 + boss['animation_timer']
            spike_x = draw_x + math.cos(angle) * boss['radius']
            spike_y = draw_y + math.sin(angle) * boss['radius']
            spike_end_x = spike_x + math.cos(angle) * 18
            spike_end_y = spike_y + math.sin(angle) * 18
            pygame.draw.line(surface, (100, 20, 20), (int(spike_x), int(spike_y)), 
                           (int(spike_end_x), int(spike_end_y)), 4)
        
        eye_positions = [(-12, -12), (12, -12)]
        for ex, ey in eye_positions:
            pygame.draw.circle(surface, (255, 0, 0), (draw_x + ex, draw_y + ey), 8)
            pygame.draw.circle(surface, (100, 0, 0), (draw_x + ex, draw_y + ey), 4)
        
        health_bar_width = boss['radius'] * 3
        health_bar_height = 10
        health_bar_x = draw_x - boss['radius'] * 1.5
        health_bar_y = draw_y - boss['radius'] - 25
        
        pygame.draw.rect(surface, (50, 50, 50), 
                       (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        
        health_ratio = boss['health'] / boss['max_health']
        health_color = (255, 0, 0) if health_ratio < 0.3 else (255, 100, 0) if health_ratio < 0.6 else (255, 200, 0)
        pygame.draw.rect(surface, health_color, 
                       (health_bar_x, health_bar_y, int(health_bar_width * health_ratio), health_bar_height))
        pygame.draw.rect(surface, (200, 200, 200), 
                       (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)
        
        font = pygame.font.Font(None, 28)
        boss_text = font.render("BOSS", True, (255, 50, 50))
        text_rect = boss_text.get_rect(center=(draw_x, health_bar_y - 12))
        surface.blit(boss_text, text_rect)

    def draw_bullets(self, surface):
        for bullet in self.bullets:
            draw_x = int(bullet['x'] + self.camera_x)
            draw_y = int(bullet['y'] + self.camera_y)
            
            glow_radius = int(bullet['size'] * 2.5)
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            glow_color = (255, 200, 200, 120) if bullet['is_crit'] else (255, 255, 150, 100)
            pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surface, (draw_x - glow_radius, draw_y - glow_radius))
            
            bullet_color = (255, 100, 100) if bullet['is_crit'] else (255, 255, 0)
            pygame.draw.circle(surface, bullet_color, (draw_x, draw_y), bullet['size'])
            pygame.draw.circle(surface, (255, 255, 200), (draw_x, draw_y), bullet['size'] - 1)

    def draw_xp_gems(self, surface):
        for gem in self.xp_gems:
            draw_x = int(gem['x'] + self.camera_x)
            draw_y = int(gem['y'] + self.camera_y)
            
            float_offset = math.sin(gem['animation_timer'] * 4) * 3
            draw_y += int(float_offset)
            
            color = (150, 100, 255)
            
            glow_radius = int(gem['radius'] * 1.8)
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pulse = abs(math.sin(gem['animation_timer'] * 5))
            glow_color = (*color, int(100 * pulse))
            pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surface, (draw_x - glow_radius, draw_y - glow_radius))
            
            pygame.draw.circle(surface, color, (draw_x, draw_y), gem['radius'])
            pygame.draw.circle(surface, (200, 150, 255), (draw_x, draw_y), gem['radius'] - 2)

    def draw_powerups(self, surface):
        for powerup in self.powerups:
            draw_x = int(powerup['x'] + self.camera_x)
            draw_y = int(powerup['y'] + self.camera_y)
            
            float_offset = math.sin(powerup['animation_timer'] * 3) * 6
            draw_y += int(float_offset)
            
            if powerup['type'] == 'health':
                color = (0, 255, 0)
                symbol = '+'
            else:
                color = (255, 0, 255)
                symbol = '?'
            
            glow_radius = int(powerup['radius'] * 1.7)
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pulse = abs(math.sin(powerup['animation_timer'] * 5))
            glow_color = (*color, int(120 * pulse))
            pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surface, (draw_x - glow_radius, draw_y - glow_radius))
            
            pygame.draw.circle(surface, color, (draw_x, draw_y), powerup['radius'])
            pygame.draw.circle(surface, (255, 255, 255), (draw_x, draw_y), powerup['radius'], 2)
            
            font = pygame.font.Font(None, 36)
            symbol_text = font.render(symbol, True, (255, 255, 255))
            text_rect = symbol_text.get_rect(center=(draw_x, draw_y))
            surface.blit(symbol_text, text_rect)

    def draw_particles(self, surface):
        for particle in self.particles:
            draw_x = int(particle['x'] + self.camera_x)
            draw_y = int(particle['y'] + self.camera_y)
            
            if draw_x < -20 or draw_x > 1300 or draw_y < 100 or draw_y > 740:
                continue
            
            alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
            color = (*particle['color'], alpha)
            
            particle_surface = pygame.Surface((int(particle['size'] * 2), int(particle['size'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color, (int(particle['size']), int(particle['size'])), int(particle['size']))
            surface.blit(particle_surface, (draw_x - int(particle['size']), draw_y - int(particle['size'])))

    def draw_damage_numbers(self, surface):
        font = pygame.font.Font(None, 30)
        
        for number in self.damage_numbers:
            draw_x = int(number['x'] + self.camera_x)
            draw_y = int(number['y'] + self.camera_y)
            
            alpha = int(255 * (number['lifetime'] / 0.8))
            
            text = font.render(str(number['damage']), True, (255, 255, 255))
            text_surface = pygame.Surface(text.get_size(), pygame.SRCALPHA)
            text_surface.fill((0, 0, 0, 0))
            text_surface.blit(text, (0, 0))
            text_surface.set_alpha(alpha)
            
            text_rect = text_surface.get_rect(center=(draw_x, draw_y))
            surface.blit(text_surface, text_rect)

    def draw_shockwaves(self, surface):
        for wave in self.shockwaves:
            draw_x = int(wave['x'] + self.camera_x)
            draw_y = int(wave['y'] + self.camera_y)
            
            alpha = int(255 * (wave['lifetime'] / 0.8))
            
            wave_surface = pygame.Surface((int(wave['radius'] * 2), int(wave['radius'] * 2)), pygame.SRCALPHA)
            color = (100, 200, 255, alpha // 2)
            pygame.draw.circle(wave_surface, color, (int(wave['radius']), int(wave['radius'])), int(wave['radius']), 4)
            surface.blit(wave_surface, (draw_x - int(wave['radius']), draw_y - int(wave['radius'])))

    def draw_ui(self, surface):
        panel_height = 115
        panel_surface = pygame.Surface((1280, panel_height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 180))
        surface.blit(panel_surface, (0, 0))
        
        font_large = pygame.font.Font(None, 52)
        font_medium = pygame.font.Font(None, 34)
        font_small = pygame.font.Font(None, 26)
        
        score_text = font_large.render(f"Score: {self.score}", True, (255, 255, 255))
        surface.blit(score_text, (20, 12))
        
        wave_text = font_medium.render(f"Wave {self.wave}", True, (255, 200, 100))
        surface.blit(wave_text, (20, 65))
        
        level_text = font_medium.render(f"Lv.{self.level}", True, (255, 150, 255))
        surface.blit(level_text, (150, 65))
        
        health_bar_x = 380
        health_bar_y = 25
        health_bar_width = 320
        health_bar_height = 28
        
        health_label = font_small.render("Health", True, (255, 255, 255))
        surface.blit(health_label, (health_bar_x, health_bar_y - 22))
        
        pygame.draw.rect(surface, (100, 0, 0), 
                       (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        
        health_ratio = max(0, self.player_health / self.player_max_health)
        health_color = (0, 255, 0) if health_ratio > 0.6 else (255, 165, 0) if health_ratio > 0.3 else (255, 0, 0)
        pygame.draw.rect(surface, health_color, 
                       (health_bar_x, health_bar_y, int(health_bar_width * health_ratio), health_bar_height))
        
        pygame.draw.rect(surface, (255, 255, 255), 
                       (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)
        
        health_text = font_small.render(f"{int(self.player_health)}/{self.player_max_health}", True, (255, 255, 255))
        text_rect = health_text.get_rect(center=(health_bar_x + health_bar_width // 2, health_bar_y + health_bar_height // 2))
        surface.blit(health_text, text_rect)
        
        xp_bar_y = 70
        xp_label = font_small.render("XP", True, (255, 255, 255))
        surface.blit(xp_label, (health_bar_x, xp_bar_y - 22))
        
        pygame.draw.rect(surface, (50, 50, 100), 
                       (health_bar_x, xp_bar_y, health_bar_width, 18))
        
        xp_ratio = self.xp / self.xp_to_next_level
        pygame.draw.rect(surface, (200, 100, 255), 
                       (health_bar_x, xp_bar_y, int(health_bar_width * xp_ratio), 18))
        
        pygame.draw.rect(surface, (255, 255, 255), 
                       (health_bar_x, xp_bar_y, health_bar_width, 18), 1)
        
        if self.combo_counter > 0:
            combo_text = font_large.render(f"x{self.combo_counter}", True, (255, 255, 0))
            combo_rect = combo_text.get_rect(center=(1180, 35))
            surface.blit(combo_text, combo_rect)
            
            combo_label = font_small.render("COMBO", True, (255, 200, 0))
            combo_label_rect = combo_label.get_rect(center=(1180, 65))
            surface.blit(combo_label, combo_label_rect)
        
        ability_x = 750
        ability_y = 20
        
        dash_cooldown_ratio = 1 - (self.dash_cooldown / self.dash_max_cooldown)
        self.draw_ability_icon(surface, ability_x, ability_y, "DASH", dash_cooldown_ratio, (100, 200, 255))
        
        shockwave_cooldown_ratio = 1 - (self.shockwave_cooldown / self.shockwave_max_cooldown)
        self.draw_ability_icon(surface, ability_x + 120, ability_y, "WAVE", shockwave_cooldown_ratio, (255, 200, 100))
        
        kills_text = font_small.render(f"Killed: {self.zombies_killed_this_wave}", True, (200, 200, 200))
        surface.blit(kills_text, (270, 65))

    def draw_ability_icon(self, surface, x, y, name, cooldown_ratio, color):
        icon_size = 70
        
        pygame.draw.rect(surface, (40, 40, 40), (x, y, icon_size, icon_size))
        
        if cooldown_ratio < 1:
            cooldown_height = int(icon_size * (1 - cooldown_ratio))
            pygame.draw.rect(surface, (20, 20, 20), (x, y, icon_size, cooldown_height))
        
        pygame.draw.rect(surface, color if cooldown_ratio >= 1 else (80, 80, 80), 
                       (x, y, icon_size, icon_size), 4)
        
        font = pygame.font.Font(None, 22)
        name_text = font.render(name, True, (255, 255, 255))
        text_rect = name_text.get_rect(center=(x + icon_size // 2, y + icon_size // 2))
        surface.blit(name_text, text_rect)
        
        if cooldown_ratio < 1:
            cooldown_time = (1 - cooldown_ratio) * (self.dash_max_cooldown if name == "DASH" else self.shockwave_max_cooldown)
            cooldown_text = font.render(f"{cooldown_time:.1f}s", True, (255, 255, 255))
            cooldown_rect = cooldown_text.get_rect(center=(x + icon_size // 2, y + icon_size + 12))
            surface.blit(cooldown_text, cooldown_rect)

    def draw_wave_transition(self, surface):
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        
        font_huge = pygame.font.Font(None, 110)
        font_large = pygame.font.Font(None, 70)
        
        if self.wave > 1:
            wave_text = font_huge.render(f"WAVE {self.wave}", True, (255, 255, 100))
            wave_rect = wave_text.get_rect(center=(640, 320))
            surface.blit(wave_text, wave_rect)
            
            if self.boss_wave:
                boss_text = font_large.render("BOSS INCOMING!", True, (255, 50, 50))
                boss_rect = boss_text.get_rect(center=(640, 430))
                surface.blit(boss_text, boss_rect)
            else:
                ready_text = font_large.render("GET READY!", True, (200, 200, 200))
                ready_rect = ready_text.get_rect(center=(640, 430))
                surface.blit(ready_text, ready_rect)

    def draw_level_up_screen(self, surface):
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        font_huge = pygame.font.Font(None, 96)
        font_large = pygame.font.Font(None, 48)
        font_medium = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 28)
        
        title_text = font_huge.render("LEVEL UP!", True, (255, 255, 0))
        title_rect = title_text.get_rect(center=(640, 150))
        surface.blit(title_text, title_rect)
        
        subtitle_text = font_small.render("Choose your upgrade - Move trackball and click to select", True, (200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(640, 220))
        surface.blit(subtitle_text, subtitle_rect)
        
        card_width = 320
        card_height = 380
        card_spacing = 40
        start_x = 640 - (card_width * 1.5 + card_spacing)
        card_y = 280
        
        for i, upgrade_key in enumerate(self.level_up_choices):
            upgrade = self.available_upgrades[upgrade_key]
            card_x = start_x + (card_width + card_spacing) * i
            
            is_selected = (i == self.selected_choice)
            
            card_color = (80, 80, 100) if not is_selected else (120, 120, 150)
            border_color = (150, 150, 150) if not is_selected else (255, 255, 0)
            border_width = 3 if not is_selected else 6
            
            card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
            card_surface.fill((*card_color, 220))
            pygame.draw.rect(card_surface, border_color, (0, 0, card_width, card_height), border_width)
            
            icon_size = 100
            icon_x = card_width // 2 - icon_size // 2
            icon_y = 30
            pygame.draw.rect(card_surface, upgrade['color'], (icon_x, icon_y, icon_size, icon_size))
            pygame.draw.rect(card_surface, (255, 255, 255), (icon_x, icon_y, icon_size, icon_size), 3)
            
            icon_text = font_huge.render(upgrade['icon'], True, (255, 255, 255))
            icon_rect = icon_text.get_rect(center=(card_width // 2, icon_y + icon_size // 2))
            card_surface.blit(icon_text, icon_rect)
            
            name_text = font_large.render(upgrade['name'], True, (255, 255, 255))
            name_rect = name_text.get_rect(center=(card_width // 2, 170))
            card_surface.blit(name_text, name_rect)
            
            desc_lines = upgrade['desc'].split('\n')
            desc_y = 230
            for line in desc_lines:
                desc_text = font_medium.render(line, True, (200, 200, 200))
                desc_rect = desc_text.get_rect(center=(card_width // 2, desc_y))
                card_surface.blit(desc_text, desc_rect)
                desc_y += 40
            
            if is_selected:
                select_text = font_medium.render(">>> CLICK TO SELECT <<<", True, (255, 255, 0))
                select_rect = select_text.get_rect(center=(card_width // 2, card_height - 30))
                card_surface.blit(select_text, select_rect)
            
            surface.blit(card_surface, (card_x, card_y))

    def draw_pause_overlay(self, surface):
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 110)
        pause_text = font.render("PAUSED", True, (255, 255, 255))
        text_rect = pause_text.get_rect(center=(640, 360))
        surface.blit(pause_text, text_rect)