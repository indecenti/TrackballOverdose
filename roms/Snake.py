import pygame
import math
import random

class SnakeGame(MiniGame):
    def __init__(self, *args, sound=None, **kwargs):
        super().__init__("Snake", "Classic snake: eat apples, grow longer!", *args, **kwargs)
        self.sound = sound
        self.reset()
    
    def reset(self):
        self.score = 0
        self.is_game_over = False
        self.is_paused = False
        
        # Grid settings (1280x720 / 30 = 42x24 grid)
        self.grid_size = 30
        self.grid_width = 42
        self.grid_height = 24
        
        # Snake inizia al centro
        self.snake_segments = [
            {'x': 21, 'y': 12},
            {'x': 20, 'y': 12},
            {'x': 19, 'y': 12}
        ]
        
        # Direzione iniziale (1=right, -1=left, 2=down, -2=up)
        self.direction = 1
        self.next_direction = 1
        
        # Timer per movimento a grid
        self.move_timer = 0
        self.move_interval = 0.15  # Secondi tra movimenti
        
        # Food (mela)
        self.spawn_food()
        
        # Effetti visivi
        self.shake = 0
        self.particles = []
        self.eat_animation = 0
        
        # Background animato
        self.bg_offset = 0
        
        self.sound.create_game_start().play()
    
    def spawn_food(self):
        # Spawn food in posizione libera
        while True:
            fx = random.randint(1, self.grid_width - 2)
            fy = random.randint(1, self.grid_height - 2)
            
            # Verifica che non sia sulla snake
            occupied = False
            for segment in self.snake_segments:
                if segment['x'] == fx and segment['y'] == fy:
                    occupied = True
                    break
            
            if not occupied:
                self.food_x = fx
                self.food_y = fy
                break
    
    def update(self, dt, trackball):
        if self.is_paused or self.is_game_over:
            return
        
        # Background animato
        self.bg_offset += dt * 20
        
        # Input trackball per direzione
        dx, dy = trackball.get_smooth_delta()
        
        # Cambio direzione basato sul movimento trackball
        if abs(dx) > abs(dy):
            if dx > 3 and self.direction not in [1, -1]:  # Non può invertire
                self.next_direction = 1  # Destra
            elif dx < -3 and self.direction not in [1, -1]:
                self.next_direction = -1  # Sinistra
        else:
            if dy > 3 and self.direction not in [2, -2]:
                self.next_direction = 2  # Giù
            elif dy < -3 and self.direction not in [2, -2]:
                self.next_direction = -2  # Su
        
        # Update particelle
        for particle in self.particles[:]:
            particle['life'] -= dt
            particle['y'] -= particle['vy'] * dt
            particle['x'] += particle['vx'] * dt
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        self.eat_animation = max(0, self.eat_animation - dt * 3)
        
        # Timer movimento griglia
        self.move_timer += dt
        if self.move_timer >= self.move_interval:
            self.move_timer = 0
            self.move_snake()
    
    def move_snake(self):
        # Applica direzione pendente
        self.direction = self.next_direction
        
        # Calcola nuova posizione testa
        head = self.snake_segments[0].copy()
        
        if self.direction == 1:  # Destra
            head['x'] += 1
        elif self.direction == -1:  # Sinistra
            head['x'] -= 1
        elif self.direction == 2:  # Giù
            head['y'] += 1
        elif self.direction == -2:  # Su
            head['y'] -= 1
        
        # Collision detection con muri
        if head['x'] < 0 or head['x'] >= self.grid_width or head['y'] < 0 or head['y'] >= self.grid_height:
            self.is_game_over = True
            self.score += 5000
            self.sound.create_target_miss().play()
            return
        
        # Collision detection con se stesso
        for segment in self.snake_segments:
            if head['x'] == segment['x'] and head['y'] == segment['y']:
                self.is_game_over = True
                self.score += 5000
                self.sound.create_target_miss().play()
                return
        
        # Inserisce nuova testa
        self.snake_segments.insert(0, head)
        
        # Check se mangia food
        if head['x'] == self.food_x and head['y'] == self.food_y:
            # Cresce (non rimuove coda)
            self.score += 100
            self.shake = 12
            self.eat_animation = 1.0
            
            # Effetto particelle
            for _ in range(15):
                self.particles.append({
                    'x': self.food_x * self.grid_size + self.grid_size // 2,
                    'y': self.food_y * self.grid_size + self.grid_size // 2,
                    'vx': random.uniform(-100, 100),
                    'vy': random.uniform(-150, -50),
                    'life': random.uniform(0.3, 0.6),
                    'color': (random.randint(200, 255), random.randint(50, 100), random.randint(50, 100))
                })
            
            self.sound.create_target_hit().play()
            self.spawn_food()
            
            # Aumenta velocità progressivamente
            if len(self.snake_segments) % 5 == 0:
                self.move_interval = max(0.08, self.move_interval - 0.01)
                self.sound.create_combo(len(self.snake_segments) // 5).play()
        else:
            # Non mangia, rimuove coda
            self.snake_segments.pop()
        
        # Punto per sopravvivenza
        self.score += 1
    
    def draw(self, surface):
        # Background con pattern animato
        for i in range(0, 1280, 40):
            for j in range(0, 720, 40):
                offset = int(self.bg_offset) % 40
                brightness = 15 + int(math.sin((i + j + self.bg_offset) * 0.02) * 5)
                pygame.draw.rect(surface, (brightness, brightness + 5, brightness + 10), 
                               (i - offset, j - offset, 38, 38))
        
        # Shake effect
        shake_x = int(math.sin(pygame.time.get_ticks() * 0.05) * self.shake)
        shake_y = int(math.cos(pygame.time.get_ticks() * 0.07) * self.shake)
        self.shake *= 0.85
        
        # Grid decorativa (bordo)
        for i in range(self.grid_width + 1):
            x = i * self.grid_size
            pygame.draw.line(surface, (40, 50, 70), (x, 0), (x, 720), 1)
        for j in range(self.grid_height + 1):
            y = j * self.grid_size
            pygame.draw.line(surface, (40, 50, 70), (0, y), (1280, y), 1)
        
        # Draw food (mela fumettistica)
        food_screen_x = self.food_x * self.grid_size + self.grid_size // 2 + shake_x
        food_screen_y = self.food_y * self.grid_size + self.grid_size // 2 + shake_y
        
        # Animazione pulsante food
        pulse = 1.0 + math.sin(pygame.time.get_ticks() * 0.005) * 0.15
        food_radius = int(self.grid_size * 0.4 * pulse)
        
        # Ombra food
        pygame.draw.circle(surface, (50, 20, 20), 
                         (food_screen_x + 3, food_screen_y + 3), food_radius)
        # Food principale (rosso)
        pygame.draw.circle(surface, (255, 50, 50), 
                         (food_screen_x, food_screen_y), food_radius)
        # Highlight food
        pygame.draw.circle(surface, (255, 150, 150), 
                         (food_screen_x - food_radius // 3, food_screen_y - food_radius // 3), 
                         food_radius // 3)
        # Gambo
        pygame.draw.rect(surface, (80, 200, 80), 
                       (food_screen_x - 2, food_screen_y - food_radius - 5, 4, 6))
        
        # Draw snake (stile fumetto con outline)
        for i, segment in enumerate(self.snake_segments):
            sx = segment['x'] * self.grid_size + self.grid_size // 2 + shake_x
            sy = segment['y'] * self.grid_size + self.grid_size // 2 + shake_y
            
            # Colore gradiente verde
            is_head = (i == 0)
            brightness = 255 - min(i * 3, 100)
            
            if is_head:
                # Testa più grande con animazione mangiata
                head_size = self.grid_size * 0.55
                if self.eat_animation > 0:
                    head_size *= (1.0 + self.eat_animation * 0.3)
                
                # Outline nero
                pygame.draw.circle(surface, (20, 20, 20), 
                                 (int(sx), int(sy)), int(head_size) + 3)
                # Testa verde chiaro
                pygame.draw.circle(surface, (100, 255, 100), 
                                 (int(sx), int(sy)), int(head_size))
                
                # Occhi fumettistici
                eye_offset = 6
                eye_radius = 4
                
                # Occhio sinistro
                pygame.draw.circle(surface, (255, 255, 255), 
                                 (int(sx - eye_offset), int(sy - 3)), eye_radius)
                pygame.draw.circle(surface, (20, 20, 20), 
                                 (int(sx - eye_offset + 1), int(sy - 2)), 2)
                
                # Occhio destro
                pygame.draw.circle(surface, (255, 255, 255), 
                                 (int(sx + eye_offset), int(sy - 3)), eye_radius)
                pygame.draw.circle(surface, (20, 20, 20), 
                                 (int(sx + eye_offset + 1), int(sy - 2)), 2)
                
                # Bocca
                pygame.draw.arc(surface, (20, 20, 20), 
                              (int(sx - 6), int(sy), 12, 8), 
                              3.14, 6.28, 2)
            else:
                # Corpo con outline
                body_size = self.grid_size * 0.45
                pygame.draw.circle(surface, (20, 20, 20), 
                                 (int(sx), int(sy)), int(body_size) + 2)
                pygame.draw.circle(surface, (50, brightness, 50), 
                                 (int(sx), int(sy)), int(body_size))
                # Highlight corpo
                pygame.draw.circle(surface, (150, 255, 150), 
                                 (int(sx - 3), int(sy - 3)), int(body_size * 0.3))
        
        # Particelle mangiata
        for particle in self.particles:
            size = max(1, int(particle['life'] * 8))
            alpha_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color = particle['color'] + (int(particle['life'] * 255),)
            pygame.draw.circle(alpha_surf, color, (size, size), size)
            surface.blit(alpha_surf, (int(particle['x']) - size, int(particle['y']) - size))
        
        # Score display (fumettistico)
        font_big = pygame.font.Font(None, 92)
        font_small = pygame.font.Font(None, 48)
        
        # Outline score
        score_text = str(self.score)
        for offset_x in [-3, 3]:
            for offset_y in [-3, 3]:
                score_surf = font_big.render(score_text, True, (20, 20, 20))
                surface.blit(score_surf, (1180 - score_surf.get_width() + offset_x, 30 + offset_y))
        
        # Score principale
        score_surf = font_big.render(score_text, True, (255, 255, 100))
        surface.blit(score_surf, (1180 - score_surf.get_width(), 30))
        
        # Lunghezza snake
        length_text = f"Length: {len(self.snake_segments)}"
        length_surf = font_small.render(length_text, True, (150, 255, 150))
        surface.blit(length_surf, (50, 40))
        
        # Pause overlay
        if self.is_paused:
            self._draw_pause_overlay(surface)
    
    def _draw_pause_overlay(self, surface):
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((20, 30, 60, 220))
        surface.blit(overlay, (0, 0))
        
        font_big = pygame.font.Font(None, 140)
        pause_text = font_big.render("PAUSED", True, (255, 255, 255))
        surface.blit(pause_text, (640 - pause_text.get_width() // 2, 280))
        
        font_small = pygame.font.Font(None, 52)
        resume_text = font_small.render("MIDDLE BUTTON: RESUME", True, (100, 255, 100))
        menu_text = font_small.render("RIGHT BUTTON: MENU EXIT", True, (255, 200, 100))
        
        surface.blit(resume_text, (640 - resume_text.get_width() // 2, 420))
        surface.blit(menu_text, (640 - menu_text.get_width() // 2, 480))
    
    def getscore(self):
        return self.score
