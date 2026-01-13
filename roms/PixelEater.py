# roms/PixelEater.py - BLOB ORGANIC + FIXED COLORS + ULTRA OPTIMIZED
class PixelEater(MiniGame):
    def __init__(self, *args, sound=None, **kwargs):
        super().__init__("PixelEater", "Organic Blob Evolution!", *args, **kwargs)
        self.sound = sound
        self.level = 1
        self.target_pixels_per_level = 40
        self.pixels_eaten_this_level = 0
        self.particles = []
        self.trail_particles = []
        self.screen_shake = 0
        self.time_scale = 1.0
        self.explode_timer = 0
        self.level_up_flash = 0
        # 🔴 BLOB params
        self.blob_time = 0.0
        self.blob_lobes = 6  # Lobi organici
        self.blob_pulse = 0.0
        self.reset()

    def reset(self):
        self.center_x = 640.0
        self.center_y = 360.0
        self.radius = 12.0  # Start piccolo
        self.angle = 0.0
        self.score = 0
        self.is_game_over = False
        self.level = 1
        self.target_pixels_per_level = 40
        self.pixels_eaten_this_level = 0
        self.particles = []
        self.trail_particles = []
        self.screen_shake = 0
        self.time_scale = 1.0
        self.explode_timer = 0
        self.level_up_flash = 0
        self.blob_time = 0.0
        self.blob_pulse = 1.0
        self._generate_pixels()
        self.font = pygame.font.Font(None, 42)
        self.font_big = pygame.font.Font(None, 72)
        self.font_huge = pygame.font.Font(None, 120)

    def _safe_color(self, r, g, b):
        """🔧 FIXED: Sempre colori validi"""
        return (
            max(0, min(255, int(r))),
            max(0, min(255, int(g))),
            max(0, min(255, int(b)))
        )

    def _safe_randint(self, low, high):
        return random.randint(max(0, min(low, high)), min(255, max(low, high)))

    def _spawn_particles(self, x, y, count, color_range):
        min_r, min_g, min_b = color_range[0]
        max_r, max_g, max_b = color_range[1]
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150, 400)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 1.0,
                'max_life': 0.7,
                'size': random.uniform(2, 7),
                'color': (
                    self._safe_randint(min_r, max_r),
                    self._safe_randint(min_g, max_g),
                    self._safe_randint(min_b, max_b)
                )
            })

    def _spawn_trail(self, x, y):
        self.trail_particles.append({
            'x': x, 'y': y,
            'life': 0.6,
            'max_life': 0.6,
            'size': self.radius * 0.3,
            'color': self._safe_color(80, 160, 240)
        })

    def _generate_pixels(self):
        num_pixels = self.target_pixels_per_level + (self.level * 8)
        self.pixels = []
        for _ in range(num_pixels):
            while True:
                px = random.randint(20, 1260)
                py = random.randint(20, 700)
                if math.hypot(px - self.center_x, py - self.center_y) > self.radius * 3:
                    p_type = random.choice([
                        {'type': 'normal', 'color': (160, 210, 255), 'points': 10},
                        {'type': 'flee', 'color': (255, 190, 130), 'points': 20},
                        {'type': 'aggro', 'color': (255, 130, 160), 'points': 30}
                    ])
                    self.pixels.append({
                        'x': float(px), 'y': float(py),
                        'vx': random.uniform(-35, 35),
                        'vy': random.uniform(-35, 35),
                        'type': p_type['type'],
                        'color': p_type['color'],
                        'size': random.uniform(2.5, 4.5),
                        'hunger': 0,
                        'flee_timer': random.uniform(0, 1.5),
                        'pulse_phase': random.uniform(0, math.pi * 2),
                        'points': p_type['points']
                    })
                    break

    def _level_up(self):
        self.level += 1
        self.target_pixels_per_level += 15
        self.pixels_eaten_this_level = 0
        self.level_up_flash = 1.0
        self.screen_shake = 22
        self.radius = min(95, self.radius * 1.22)  # GROW più aggressivo
        self.blob_pulse = 1.4  # Pulse crescita
        self._spawn_particles(self.center_x, self.center_y, 90, ((255,255,100), (255,200,50)))
        if self.sound:
            self.sound.create_combo(self.level).play()

    def update(self, dt: float, trackball: TrackballInput):
        real_dt = dt
        dt *= self.time_scale
        
        if self.is_paused or self.is_game_over: return
        
        try:
            dx, dy = trackball.get_smooth_delta()
        except:
            dx, dy = 0, 0
        
        speed_mult = 5.5 + (self.level * 0.35)  # ANCORA PIÙ VELOCE
        self.center_x = max(self.radius, min(1280 - self.radius, self.center_x + dx * dt * speed_mult))
        self.center_y = max(self.radius, min(720 - self.radius, self.center_y + dy * dt * speed_mult))
        self.angle += dt * 9.0
        self.blob_time += dt * 3.0
        
        # Blob animation
        self.blob_pulse *= 0.96
        if self.blob_pulse < 1.0:
            self.blob_pulse = 1.0
        
        self._spawn_trail(self.center_x, self.center_y)
        
        # Pixels update (ottimizzato - meno loop annidati)
        self.pixels[:] = [p for p in self.pixels if self._update_pixel(p, dt)]
        
        # Eat + MASSIVE GROW
        self.pixels[:] = [p for p in self.pixels if not self._eat_pixel(p)]
        
        if self.pixels_eaten_this_level >= self.target_pixels_per_level:
            self._level_up()
        
        if not self.pixels and self.pixels_eaten_this_level >= self.target_pixels_per_level:
            if self.level < 15:  # 15 livelli!
                self._generate_pixels()
            else:
                self.explode_timer = 3.5
                self.time_scale = 0.06
                self.screen_shake = 50
                self._spawn_particles(self.center_x, self.center_y, 500, ((255,80,80), (255,255,120)))
                if self.sound:
                    self.sound.create_game_over().play()
        
        # Particles optimized
        self.particles[:] = [p for p in self.particles if p['life'] > 0]
        for p in self.particles:
            p['life'] -= real_dt / p['max_life']
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vx'] *= 0.96
            p['vy'] *= 0.96
            p['size'] *= 0.99
        
        self.trail_particles[:] = [p for p in self.trail_particles if p['life'] > 0]
        for t in self.trail_particles:
            t['life'] -= real_dt / t['max_life']
            t['size'] *= 0.98
        
        self.screen_shake *= 0.87
        if self.level_up_flash > 0:
            self.level_up_flash -= real_dt * 3
        if self.explode_timer > 0:
            self.explode_timer -= real_dt
            if self.explode_timer <= 0:
                self.is_game_over = True
                self.time_scale = 1.0

    def _update_pixel(self, p, dt):
        """Ottimizzato pixel update"""
        if p['type'] == 'normal':
            p['vx'] += random.uniform(-20, 20) * dt
            p['vy'] += random.uniform(-20, 20) * dt
            p['vx'] *= 0.95
            p['vy'] *= 0.95
        elif p['type'] == 'flee':
            dx_p = self.center_x - p['x']
            dy_p = self.center_y - p['y']
            dist = math.hypot(dx_p, dy_p)
            if dist < 160:
                p['vx'] -= (dx_p / dist) * 100 * dt
                p['vy'] -= (dy_p / dist) * 100 * dt
            p['flee_timer'] -= dt
            if p['flee_timer'] < 0:
                p['vx'] += random.uniform(-30, 30)
                p['vy'] += random.uniform(-30, 30)
                p['flee_timer'] = random.uniform(0.8, 2)
        elif p['type'] == 'aggro':
            p['hunger'] += dt * 2.5
            if p['hunger'] > 1.2:
                for i, other in enumerate(self.pixels):
                    if other is p: continue
                    odx = other['x'] - p['x']
                    ody = other['y'] - p['y']
                    odist = math.hypot(odx, ody)
                    if odist < 22:
                        p['size'] += other['size'] * 0.4
                        p['hunger'] = 0
                        self._spawn_particles(p['x'], p['y'], 8, ((255,140,140), (255,220,220)))
                        del self.pixels[i]
                        break
        
        p['x'] += p['vx'] * dt
        p['y'] += p['vy'] * dt
        if p['x'] < 0 or p['x'] > 1280: p['vx'] *= -0.85
        if p['y'] < 0 or p['y'] > 720: p['vy'] *= -0.85
        p['pulse_phase'] += dt * 5
        return True

    def _eat_pixel(self, p):
        dist = math.hypot(p['x'] - self.center_x, p['y'] - self.center_y)
        if dist < self.radius + p['size']:
            self.score += p['points']
            self.pixels_eaten_this_level += 1
            self.radius = min(100, self.radius + p['size'] * 0.35)  # MASSIVE GROW!
            self._spawn_particles(self.center_x, self.center_y, 25, (p['color'], (255,255,255)))
            self.screen_shake = max(15, self.screen_shake + 10)
            if self.sound:
                self.sound.create_target_hit().play()
            return True  # Rimuovi
        return False

    def _get_shake_offset(self):
        if self.screen_shake > 0:
            shake_x = math.sin(pygame.time.get_ticks() * 0.025) * self.screen_shake
            shake_y = math.cos(pygame.time.get_ticks() * 0.018) * self.screen_shake * 0.75
            return (shake_x, shake_y)
        return (0, 0)

    def _draw_blob(self, temp_surf, shake_x, shake_y):
        """🔴 BLOB ORGANIC MASSA NERA SFUMATA"""
        self.blob_time += 0.1
        
        # Base shape organica con lobi
        points = []
        for i in range(48):  # Più punti per organic
            a = self.angle + i * 2 * math.pi / 48
            # Lobi blob
            lobe = 1.0 + 0.25 * math.sin(self.blob_time * 2 + i * 0.7)
            r_blob = self.radius * lobe * self.blob_pulse
            x_blob = self.center_x + math.cos(a) * r_blob + shake_x * 0.5
            y_blob = self.center_y + math.sin(a) * r_blob + shake_y * 0.5
            points.append((x_blob, y_blob))
        
        # 🔴 SFUMATURE NERE → VIOLA SCURO
        gradient_points = []
        for i in range(24):
            a = self.angle * 1.3 + i * 2 * math.pi / 24
            r_inner = self.radius * 0.6
            gradient_points.append((
                self.center_x + math.cos(a) * r_inner + shake_x * 0.3,
                self.center_y + math.sin(a) * r_inner + shake_y * 0.3
            ))
        
        # Fill organico con gradient simulato
        blob_color_dark = self._safe_color(15, 10, 35)  # Quasi nero viola
        blob_color_mid = self._safe_color(60, 40, 120)
        blob_color_glow = self._safe_color(120, 80, 220)
        
        # Layer 1: Core scuro
        pygame.draw.polygon(temp_surf, blob_color_dark, points)
        
        # Layer 2: Sfumatura media
        pygame.draw.aalines(temp_surf, blob_color_mid, True, gradient_points)
        
        # Layer 3: Glow bordi
        pygame.draw.aalines(temp_surf, blob_color_glow, True, points)
        
        # Pulse interno
        pulse_r = int(self.radius * 0.3 * (0.9 + 0.1 * math.sin(self.blob_time * 4)))
        pygame.draw.circle(temp_surf, self._safe_color(255, 200, 100), 
                         (int(self.center_x + shake_x), int(self.center_y + shake_y)), pulse_r)

    def draw(self, surface: pygame.Surface):
        shake_x, shake_y = self._get_shake_offset()
        temp_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
        
        # Sfondo comics (invariato)
        for y in range(720):
            factor = y / 720.0
            pulse = abs(math.sin(self.angle * 0.6 + factor * 3)) * 25
            r = max(0, min(255, int(5 + pulse + factor * 8)))
            g = max(0, min(255, int(3 + math.sin(self.angle * 0.4) * 18)))
            b = max(0, min(255, int(20 + factor * 35)))
            pygame.draw.line(temp_surf, (r, g, b), (int(shake_x), y), (int(1280 + shake_x), y))
        
        # Trail FIXED
        for t in self.trail_particles:
            alpha = t['life']
            size = max(1, int(t['size'] * alpha))
            trail_color = self._safe_color(t['color'][0] * alpha * 1.5, 
                                         t['color'][1] * alpha * 1.5, 
                                         t['color'][2] * alpha * 1.5)
            pygame.draw.circle(temp_surf, trail_color, 
                             (int(t['x'] + shake_x), int(t['y'] + shake_y)), size)
        
        # Pixels (invariato)
        for p in self.pixels:
            pulse = 0.75 + 0.25 * math.sin(p['pulse_phase'])
            glow_size = int(p['size'] * pulse * 1.8)
            color_glow = tuple(max(0, min(255, int(c * 0.5))) for c in p['color'])
            
            if glow_size > 1:
                pygame.draw.rect(temp_surf, color_glow, 
                               (int(p['x'] + shake_x - glow_size//2), int(p['y'] + shake_y - glow_size//2),
                                glow_size, glow_size))
            
            pix_size = int(p['size'])
            rect = pygame.Rect(int(p['x'] + shake_x - pix_size//2), 
                             int(p['y'] + shake_y - pix_size//2), pix_size, pix_size)
            pygame.draw.rect(temp_surf, p['color'], rect)
            pygame.draw.rect(temp_surf, (255,255,255), rect, 1)
        
        # Particelle FIXED
        for p in self.particles:
            alpha = p['life']
            size = max(1, int(p['size'] * alpha))
            part_color = self._safe_color(p['color'][0] * alpha, 
                                        p['color'][1] * alpha, 
                                        p['color'][2] * alpha)
            pygame.draw.circle(temp_surf, part_color, 
                             (int(p['x'] + shake_x), int(p['y'] + shake_y)), size)
        
        # 🔴 BLOB ORGANIC MESSA NERA SFUMATA
        self._draw_blob(temp_surf, shake_x, shake_y)
        
        # Progress bar + UI (invariato)
        progress = self.pixels_eaten_this_level / self.target_pixels_per_level
        bar_w = int(400 * progress)
        pygame.draw.rect(temp_surf, (60, 60, 80), (400 + shake_x, 20 + shake_y, 400, 20))
        pygame.draw.rect(temp_surf, (0, 255, 200), (400 + shake_x, 20 + shake_y, bar_w, 20))
        pygame.draw.rect(temp_surf, (255, 255, 255), (400 + shake_x, 20 + shake_y, 400, 20), 2)
        
        score_surf = self.font.render(f"SCORE: {self.score}", True, (255, 240, 200))
        level_surf = self.font.render(f"LIVELLO: {self.level}", True, (0, 255, 200))
        progress_surf = self.font.render(f"{self.pixels_eaten_this_level}/{self.target_pixels_per_level}", True, (180, 220, 255))
        
        # Glow UI FIXED
        for dx in [-3, 3]:
            for dy in [-3, 3]:
                if dx != 0 or dy != 0:
                    score_outline = self.font.render(f"SCORE: {self.score}", True, (0, 0, 0))
                    temp_surf.blit(score_outline, (30 + dx + shake_x, 25 + dy + shake_y))
                    level_outline = self.font.render(f"LIVELLO: {self.level}", True, (0, 0, 0))
                    temp_surf.blit(level_outline, (30 + dx + shake_x, 65 + dy + shake_y))
                    prog_outline = self.font.render(f"{self.pixels_eaten_this_level}/{self.target_pixels_per_level}", True, (0, 0, 0))
                    temp_surf.blit(prog_outline, (850 + dx + shake_x, 25 + dy + shake_y))
        
        temp_surf.blit(score_surf, (30 + shake_x, 25 + shake_y))
        temp_surf.blit(level_surf, (30 + shake_x, 65 + shake_y))
        temp_surf.blit(progress_surf, (850 + shake_x, 25 + shake_y))
        
        # Level up + finale (invariato)
        if self.level_up_flash > 0:
            flash_alpha = int(200 * self.level_up_flash)
            overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
            overlay.fill((255, 255, 150, flash_alpha))
            temp_surf.blit(overlay, (0, 0))
            levelup_surf = self.font_huge.render("LEVEL UP!", True, (255, 200, 50))
            temp_surf.blit(levelup_surf, (640 - levelup_surf.get_width()//2 + shake_x, 200 + shake_y))
        
        if self.explode_timer > 0:
            flash = int(255 * (self.explode_timer % 0.12))
            overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
            overlay.fill((255, 150, 150, flash))
            temp_surf.blit(overlay, (0, 0))
            final_surf = self.font_huge.render("PERFETTO!", True, (255, 255, 255))
            temp_surf.blit(final_surf, (640 - final_surf.get_width()//2 + shake_x, 280 + shake_y))
        
        elif self.is_game_over:
            win_surf = self.font_huge.render("BLOB EVOLUTION!", True, (255, 220, 120))
            temp_surf.blit(win_surf, (640 - win_surf.get_width()//2 + shake_x, 340 + shake_y))
        
        if self.is_paused:
            pause_surf = self.font_big.render("PAUSA", True, (200, 230, 255))
            temp_surf.blit(pause_surf, (640 - pause_surf.get_width()//2 + shake_x, 380 + shake_y))
        
        surface.blit(temp_surf, (0, 0))
