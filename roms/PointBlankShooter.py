import pygame
import math
import random

class PointBlankShooter(MiniGame):
    def __init__(self, *args, sound=None, **kwargs):
        super().__init__("Point Blank Shooter", "Colpisci i bersagli prima che spariscano!", *args, **kwargs)
        self.sound = sound
        self.reset()

    def reset(self):
        self.score = 0
        self.is_game_over = False
        self.is_paused = False
        
        self.crosshair_x = 640
        self.crosshair_y = 360
        self.crosshair_size = 40
        self.crosshair_angle = 0
        self.crosshair_pulse = 0
        
        self.targets = []
        self.particles = []
        self.floating_texts = []
        
        self.level = 1
        self.targets_hit_in_level = 0
        self.targets_needed_for_level = 10
        self.targets_missed = 0
        self.max_misses = 5
        
        self.combo = 0
        self.combo_timer = 0
        self.combo_max_time = 1.5
        
        self.level_timer = 0
        self.level_duration = 30.0
        
        self.spawn_timer = 0
        self.spawn_interval = 1.5
        
        self.flash_timer = 0
        self.screen_shake_x = 0
        self.screen_shake_y = 0
        self.shake_intensity = 0
        
        self.background_stars = []
        for _ in range(50):
            self.background_stars.append({
                'x': random.randint(0, 1280),
                'y': random.randint(0, 720),
                'size': random.randint(1, 3),
                'speed': random.uniform(0.1, 0.5)
            })
        
        self.game_started = False
        self.start_delay = 0

    def update(self, dt: float, trackball):
        if self.is_paused or self.is_game_over:
            return
        
        if not self.game_started:
            self.start_delay += dt
            if self.start_delay > 0.5:
                self.game_started = True
                if self.sound:
                    self.sound.create_game_start().play()
            return
        
        self.update_crosshair(dt, trackball)
        self.update_shooting(trackball)
        self.update_targets(dt)
        self.update_particles(dt)
        self.update_floating_texts(dt)
        self.update_timers(dt)
        self.update_spawning(dt)
        self.update_screen_effects(dt)
        self.update_level_progression()
        
        self.score += int(10 * dt * self.level)

    def update_crosshair(self, dt, trackball):
        dx, dy = trackball.get_smooth_delta()
        
        sensitivity = 400 + (self.level * 20)
        self.crosshair_x += dx * sensitivity * dt
        self.crosshair_y += dy * sensitivity * dt
        
        self.crosshair_x = max(20, min(1260, self.crosshair_x))
        self.crosshair_y = max(20, min(700, self.crosshair_y))
        
        self.crosshair_angle += 180 * dt
        self.crosshair_pulse = math.sin(pygame.time.get_ticks() / 200) * 5

    def update_shooting(self, trackball):
        if trackball.button_left_pressed:
            self.handle_shot()

    def handle_shot(self):
        if self.sound:
            self.sound.create_shoot().play()
        
        self.create_muzzle_flash()
        self.shake_screen(5)
        
        hit_target = None
        min_distance = float('inf')
        
        for target in self.targets:
            if target['state'] != 'alive':
                continue
            
            distance = math.sqrt(
                (self.crosshair_x - target['x'])**2 + 
                (self.crosshair_y - target['y'])**2
            )
            
            hit_radius = target['size'] + self.crosshair_size / 2
            
            if distance < hit_radius and distance < min_distance:
                hit_target = target
                min_distance = distance
        
        if hit_target:
            self.hit_target(hit_target, min_distance)
        else:
            self.create_miss_effect()

    def hit_target(self, target, distance):
        target['state'] = 'dying'
        target['death_timer'] = 0
        
        accuracy_bonus = max(0, 1.0 - (distance / target['size']))
        
        base_points = target['points']
        accuracy_multiplier = 1.0 + accuracy_bonus
        combo_multiplier = 1.0 + (self.combo * 0.1)
        level_multiplier = 1.0 + (self.level * 0.2)
        
        if target['type'] == 'bonus':
            type_multiplier = 2.0
        elif target['type'] == 'fast':
            type_multiplier = 1.5
        else:
            type_multiplier = 1.0
        
        total_points = int(base_points * accuracy_multiplier * combo_multiplier * level_multiplier * type_multiplier)
        
        self.score += total_points
        self.targets_hit_in_level += 1
        self.combo += 1
        self.combo_timer = 0
        
        if self.sound:
            if self.combo > 1:
                combo_level = min(self.combo, 9)
                self.sound.create_combo(combo_level).play()
            else:
                self.sound.create_target_hit().play()
        
        self.create_hit_particles(target['x'], target['y'], target['color'])
        self.create_floating_text(target['x'], target['y'], f"+{total_points}", (255, 255, 100))
        
        if self.combo > 1:
            self.create_floating_text(
                target['x'], 
                target['y'] - 30, 
                f"COMBO x{self.combo}!", 
                (255, 100, 255)
            )
        
        self.shake_screen(8)
        self.flash_timer = 0.1

    def create_miss_effect(self):
        self.create_impact_particles(self.crosshair_x, self.crosshair_y)
        self.combo = 0

    def update_targets(self, dt):
        for target in self.targets[:]:
            if target['state'] == 'spawning':
                target['spawn_timer'] += dt
                if target['spawn_timer'] >= target['spawn_duration']:
                    target['state'] = 'alive'
                    target['alive_timer'] = 0
            
            elif target['state'] == 'alive':
                target['alive_timer'] += dt
                
                if target['type'] == 'moving':
                    target['x'] += target['vel_x'] * dt
                    target['y'] += target['vel_y'] * dt
                    
                    if target['x'] < 50 or target['x'] > 1230:
                        target['vel_x'] *= -1
                    if target['y'] < 50 or target['y'] > 670:
                        target['vel_y'] *= -1
                
                elif target['type'] == 'orbiting':
                    target['orbit_angle'] += target['orbit_speed'] * dt
                    target['x'] = target['orbit_center_x'] + math.cos(target['orbit_angle']) * target['orbit_radius']
                    target['y'] = target['orbit_center_y'] + math.sin(target['orbit_angle']) * target['orbit_radius']
                
                if target['alive_timer'] >= target['lifetime']:
                    target['state'] = 'missed'
                    self.targets_missed += 1
                    self.combo = 0
                    self.create_floating_text(target['x'], target['y'], "MISS!", (255, 50, 50))
            
            elif target['state'] == 'dying':
                target['death_timer'] += dt
                if target['death_timer'] >= 0.3:
                    self.targets.remove(target)
            
            elif target['state'] == 'missed':
                target['death_timer'] += dt
                if target['death_timer'] >= 0.5:
                    self.targets.remove(target)

    def update_particles(self, dt):
        for particle in self.particles[:]:
            particle['lifetime'] += dt
            particle['x'] += particle['vel_x'] * dt
            particle['y'] += particle['vel_y'] * dt
            particle['vel_y'] += 300 * dt
            
            if particle['lifetime'] > particle['max_lifetime']:
                self.particles.remove(particle)

    def update_floating_texts(self, dt):
        for text in self.floating_texts[:]:
            text['lifetime'] += dt
            text['y'] -= 50 * dt
            
            if text['lifetime'] > text['max_lifetime']:
                self.floating_texts.remove(text)

    def update_timers(self, dt):
        self.level_timer += dt
        
        if self.combo > 0:
            self.combo_timer += dt
            if self.combo_timer > self.combo_max_time:
                self.combo = 0

    def update_spawning(self, dt):
        self.spawn_timer += dt
        
        adjusted_interval = max(0.3, self.spawn_interval - (self.level * 0.1))
        
        if self.spawn_timer >= adjusted_interval:
            self.spawn_timer = 0
            self.spawn_target()

    def spawn_target(self):
        if len(self.targets) >= 8 + self.level:
            return
        
        target_type_roll = random.random()
        
        if target_type_roll < 0.5:
            target_type = 'static'
        elif target_type_roll < 0.7:
            target_type = 'moving'
        elif target_type_roll < 0.85:
            target_type = 'orbiting'
        elif target_type_roll < 0.95:
            target_type = 'fast'
        else:
            target_type = 'bonus'
        
        x = random.randint(100, 1180)
        y = random.randint(100, 620)
        
        if target_type == 'static':
            size = random.randint(40, 60)
            color = (255, 80, 80)
            points = 100
            lifetime = 3.0
        elif target_type == 'moving':
            size = random.randint(35, 50)
            color = (80, 150, 255)
            points = 150
            lifetime = 4.0
        elif target_type == 'orbiting':
            size = random.randint(30, 45)
            color = (150, 80, 255)
            points = 200
            lifetime = 5.0
        elif target_type == 'fast':
            size = random.randint(25, 35)
            color = (255, 150, 50)
            points = 300
            lifetime = 1.5
        else:
            size = random.randint(50, 70)
            color = (255, 255, 50)
            points = 500
            lifetime = 2.0
        
        target = {
            'x': x,
            'y': y,
            'size': size,
            'color': color,
            'points': points,
            'lifetime': lifetime,
            'type': target_type,
            'state': 'spawning',
            'spawn_timer': 0,
            'spawn_duration': 0.2,
            'alive_timer': 0,
            'death_timer': 0,
            'pulse': 0
        }
        
        if target_type == 'moving':
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 200)
            target['vel_x'] = math.cos(angle) * speed
            target['vel_y'] = math.sin(angle) * speed
        
        elif target_type == 'orbiting':
            target['orbit_center_x'] = x
            target['orbit_center_y'] = y
            target['orbit_radius'] = random.uniform(50, 100)
            target['orbit_angle'] = random.uniform(0, math.pi * 2)
            target['orbit_speed'] = random.uniform(2, 4)
        
        self.targets.append(target)

    def update_screen_effects(self, dt):
        if self.flash_timer > 0:
            self.flash_timer -= dt
        
        if self.shake_intensity > 0:
            self.shake_intensity -= 30 * dt
            self.screen_shake_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.screen_shake_y = random.uniform(-self.shake_intensity, self.shake_intensity)
        else:
            self.screen_shake_x = 0
            self.screen_shake_y = 0

    def update_level_progression(self):
        if self.targets_hit_in_level >= self.targets_needed_for_level:
            self.level += 1
            self.targets_hit_in_level = 0
            self.targets_needed_for_level += 5
            self.level_timer = 0
            
            self.score += 1000 * self.level
            
            self.create_floating_text(640, 360, f"LEVEL {self.level}!", (100, 255, 255))
            
            if self.sound:
                self.sound.create_combo(9).play()
        
        if self.targets_missed >= self.max_misses:
            self.is_game_over = True
            self.score += 5000
            return
        
        if self.level_timer >= self.level_duration and len(self.targets) == 0:
            self.is_game_over = True
            self.score += 10000
            return

    def shake_screen(self, intensity):
        self.shake_intensity = intensity

    def create_muzzle_flash(self):
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 150)
            self.particles.append({
                'x': self.crosshair_x,
                'y': self.crosshair_y,
                'vel_x': math.cos(angle) * speed,
                'vel_y': math.sin(angle) * speed,
                'color': (255, 255, 200),
                'size': random.randint(2, 5),
                'lifetime': 0,
                'max_lifetime': 0.2
            })

    def create_hit_particles(self, x, y, color):
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 300)
            self.particles.append({
                'x': x,
                'y': y,
                'vel_x': math.cos(angle) * speed,
                'vel_y': math.sin(angle) * speed - 100,
                'color': color,
                'size': random.randint(3, 8),
                'lifetime': 0,
                'max_lifetime': random.uniform(0.3, 0.6)
            })

    def create_impact_particles(self, x, y):
        for _ in range(5):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 100)
            self.particles.append({
                'x': x,
                'y': y,
                'vel_x': math.cos(angle) * speed,
                'vel_y': math.sin(angle) * speed,
                'color': (150, 150, 150),
                'size': random.randint(2, 4),
                'lifetime': 0,
                'max_lifetime': 0.3
            })

    def create_floating_text(self, x, y, text, color):
        self.floating_texts.append({
            'x': x,
            'y': y,
            'text': text,
            'color': color,
            'lifetime': 0,
            'max_lifetime': 1.0
        })

    def draw(self, surface: pygame.Surface):
        shake_x = int(self.screen_shake_x)
        shake_y = int(self.screen_shake_y)
        
        self.draw_background(surface, shake_x, shake_y)
        self.draw_particles(surface, shake_x, shake_y)
        self.draw_targets(surface, shake_x, shake_y)
        self.draw_floating_texts(surface, shake_x, shake_y)
        self.draw_crosshair(surface, shake_x, shake_y)
        self.draw_ui(surface)
        
        if self.flash_timer > 0:
            flash_alpha = int((self.flash_timer / 0.1) * 100)
            flash_surface = pygame.Surface((1280, 720))
            flash_surface.fill((255, 255, 255))
            flash_surface.set_alpha(flash_alpha)
            surface.blit(flash_surface, (0, 0))
        
        if not self.game_started:
            self.draw_ready_screen(surface)
        
        if self.is_paused:
            self.draw_pause_overlay(surface)

    def draw_background(self, surface, shake_x, shake_y):
        surface.fill((20, 20, 40))
        
        for star in self.background_stars:
            star_x = int(star['x'] + shake_x * 0.5)
            star_y = int(star['y'] + shake_y * 0.5)
            pygame.draw.circle(surface, (100, 100, 150), (star_x, star_y), star['size'])
        
        grid_color = (40, 40, 60)
        for x in range(0, 1280, 80):
            pygame.draw.line(surface, grid_color, (x + shake_x, shake_y), (x + shake_x, 720 + shake_y), 1)
        for y in range(0, 720, 80):
            pygame.draw.line(surface, grid_color, (shake_x, y + shake_y), (1280 + shake_x, y + shake_y), 1)

    def draw_targets(self, surface, shake_x, shake_y):
        for target in self.targets:
            x = int(target['x']) + shake_x
            y = int(target['y']) + shake_y
            size = target['size']
            color = target['color']
            
            if target['state'] == 'spawning':
                progress = target['spawn_timer'] / target['spawn_duration']
                size = int(size * progress)
                alpha = int(255 * progress)
                
                temp_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(temp_surface, (*color, alpha), (size, size), size)
                pygame.draw.circle(temp_surface, (255, 255, 255, alpha), (size, size), size, 3)
                surface.blit(temp_surface, (x - size, y - size))
            
            elif target['state'] == 'alive':
                pulse = math.sin(target['alive_timer'] * 10) * 5
                draw_size = size + int(pulse)
                
                lifetime_ratio = target['alive_timer'] / target['lifetime']
                if lifetime_ratio > 0.7:
                    blink = int(math.sin(target['alive_timer'] * 20) * 128 + 127)
                    warning_color = (255, blink, blink)
                else:
                    warning_color = color
                
                pygame.draw.circle(surface, warning_color, (x, y), draw_size)
                pygame.draw.circle(surface, (255, 255, 255), (x, y), draw_size, 4)
                
                inner_size = draw_size - 15
                if inner_size > 0:
                    pygame.draw.circle(surface, (0, 0, 0), (x, y), inner_size)
                    pygame.draw.circle(surface, warning_color, (x, y), inner_size, 2)
                
                pygame.draw.circle(surface, (255, 255, 255), (x, y), 5)
                
                if target['type'] == 'bonus':
                    star_points = []
                    for i in range(5):
                        angle = (i * math.pi * 2 / 5) - math.pi / 2
                        px = x + math.cos(angle) * (draw_size - 10)
                        py = y + math.sin(angle) * (draw_size - 10)
                        star_points.append((px, py))
                    pygame.draw.lines(surface, (255, 255, 255), True, star_points, 2)
            
            elif target['state'] == 'dying':
                progress = target['death_timer'] / 0.3
                size = int(size * (1 - progress))
                alpha = int(255 * (1 - progress))
                
                if size > 0:
                    temp_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(temp_surface, (*color, alpha), (size, size), size)
                    surface.blit(temp_surface, (x - size, y - size))
            
            elif target['state'] == 'missed':
                progress = target['death_timer'] / 0.5
                alpha = int(255 * (1 - progress))
                y_offset = int(progress * 50)
                
                temp_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(temp_surface, (*color, alpha), (size, size), size)
                surface.blit(temp_surface, (x - size, y - size + y_offset))

    def draw_particles(self, surface, shake_x, shake_y):
        for particle in self.particles:
            x = int(particle['x']) + shake_x
            y = int(particle['y']) + shake_y
            
            lifetime_ratio = particle['lifetime'] / particle['max_lifetime']
            alpha = int(255 * (1 - lifetime_ratio))
            size = max(1, int(particle['size'] * (1 - lifetime_ratio)))
            
            temp_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (*particle['color'], alpha), (size, size), size)
            surface.blit(temp_surface, (x - size, y - size))

    def draw_floating_texts(self, surface, shake_x, shake_y):
        font = pygame.font.Font(None, 48)
        for text_obj in self.floating_texts:
            x = int(text_obj['x']) + shake_x
            y = int(text_obj['y']) + shake_y
            
            lifetime_ratio = text_obj['lifetime'] / text_obj['max_lifetime']
            alpha = int(255 * (1 - lifetime_ratio))
            
            text_surface = font.render(text_obj['text'], True, text_obj['color'])
            text_surface.set_alpha(alpha)
            
            text_rect = text_surface.get_rect(center=(x, y))
            surface.blit(text_surface, text_rect)

    def draw_crosshair(self, surface, shake_x, shake_y):
        x = int(self.crosshair_x) + shake_x
        y = int(self.crosshair_y) + shake_y
        size = self.crosshair_size + int(self.crosshair_pulse)
        
        color = (0, 255, 0)
        
        pygame.draw.circle(surface, color, (x, y), size, 3)
        pygame.draw.circle(surface, color, (x, y), size // 2, 2)
        
        line_length = size + 10
        line_gap = 8
        
        pygame.draw.line(surface, color, (x - line_gap, y), (x - line_length, y), 3)
        pygame.draw.line(surface, color, (x + line_gap, y), (x + line_length, y), 3)
        pygame.draw.line(surface, color, (x, y - line_gap), (x, y - line_length), 3)
        pygame.draw.line(surface, color, (x, y + line_gap), (x, y + line_length), 3)
        
        pygame.draw.circle(surface, (255, 0, 0), (x, y), 3)
        
        angle_rad = math.radians(self.crosshair_angle)
        for i in range(4):
            angle = angle_rad + (i * math.pi / 2)
            dot_x = x + math.cos(angle) * (size - 5)
            dot_y = y + math.sin(angle) * (size - 5)
            pygame.draw.circle(surface, color, (int(dot_x), int(dot_y)), 4)

    def draw_ui(self, surface):
        font_large = pygame.font.Font(None, 64)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        score_text = font_large.render(f"SCORE: {self.score}", True, (255, 255, 255))
        surface.blit(score_text, (20, 20))
        
        level_text = font_medium.render(f"LEVEL {self.level}", True, (100, 255, 255))
        surface.blit(level_text, (20, 90))
        
        progress_text = font_small.render(f"Targets: {self.targets_hit_in_level}/{self.targets_needed_for_level}", True, (200, 200, 200))
        surface.blit(progress_text, (20, 140))
        
        for i in range(self.max_misses):
            x = 1150 + (i * 30)
            y = 30
            if i < self.targets_missed:
                pygame.draw.line(surface, (255, 50, 50), (x - 10, y - 10), (x + 10, y + 10), 4)
                pygame.draw.line(surface, (255, 50, 50), (x - 10, y + 10), (x + 10, y - 10), 4)
            else:
                pygame.draw.circle(surface, (50, 255, 50), (x, y), 10, 3)
        
        if self.combo > 1:
            combo_text = font_large.render(f"COMBO x{self.combo}", True, (255, 100, 255))
            combo_rect = combo_text.get_rect(center=(640, 650))
            surface.blit(combo_text, combo_rect)
            
            combo_bar_width = 200
            combo_bar_height = 10
            combo_progress = 1 - (self.combo_timer / self.combo_max_time)
            
            bar_x = 640 - combo_bar_width // 2
            bar_y = 680
            
            pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, combo_bar_width, combo_bar_height))
            pygame.draw.rect(surface, (255, 100, 255), (bar_x, bar_y, int(combo_bar_width * combo_progress), combo_bar_height))
        
        time_remaining = max(0, self.level_duration - self.level_timer)
        timer_text = font_medium.render(f"TIME: {int(time_remaining)}s", True, (255, 200, 100))
        timer_rect = timer_text.get_rect(topright=(1260, 20))
        surface.blit(timer_text, timer_rect)

    def draw_ready_screen(self, surface):
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        font_huge = pygame.font.Font(None, 128)
        font_medium = pygame.font.Font(None, 48)
        
        ready_text = font_huge.render("GET READY!", True, (255, 255, 100))
        ready_rect = ready_text.get_rect(center=(640, 300))
        surface.blit(ready_text, ready_rect)
        
        instruction_text = font_medium.render("Move trackball to aim - Left click to shoot!", True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(640, 420))
        surface.blit(instruction_text, instruction_rect)

    def draw_pause_overlay(self, surface):
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 96)
        pause_text = font.render("PAUSED", True, (255, 255, 255))
        pause_rect = pause_text.get_rect(center=(640, 360))
        surface.blit(pause_text, pause_rect)
