# roms/PongAI.py - ENGINE GAMEOVER ONLY - NO CUSTOM SCREEN
import pygame
import math
import random

class PongAI(MiniGame):
    def __init__(self, *args, sound=None, **kwargs):
        super().__init__("PongAI", "Pong vs AI - First to 5!", *args, **kwargs)
        self.sound = sound
        self.reset()

    def _safe_color(self, r, g, b, a=255):
        return (max(0,min(255,int(r))), max(0,min(255,int(g))), 
                max(0,min(255,int(b))), max(0,min(255,int(a))))

    def reset(self):
        self.score = 0  # Per highscore
        self.is_game_over = False  # Motore lo controlla
        self.is_paused = False
        
        self.paddle_w = 20
        self.paddle_h = 90
        self.player_speed = 480
        self.ai_speed = 400
        
        self.player_y = 360
        self.ai_y = 360
        self.player_pts = 0
        self.ai_pts = 0
        
        self.ball_x = 640
        self.ball_y = 360
        self.ball_vx = 340 * random.choice([-1, 1])
        self.ball_vy = random.uniform(-270, 270)
        self.ball_r = 10
        self.ball_trail = []
        self.shake = 0
        
        self.font_score = pygame.font.Font(None, 92)
        self.font_label = pygame.font.Font(None, 48)
        
        if self.sound:
            self.sound.create_game_start().play()

    def getscore(self):
        return self.score

    def pause(self):
        self.is_paused = True
        if self.sound:
            self.sound.create_pause().play()

    def resume(self):
        self.is_paused = False

    def update(self, dt, trackball):
        if self.is_paused or self.is_game_over:
            return

        # Player
        try:
            _, dy = trackball.get_smooth_delta()
        except:
            dy = 0
        self.player_y += dy * self.player_speed * dt
        self.player_y = max(self.paddle_h/2, min(720-self.paddle_h/2, self.player_y))

        # AI
        target = self.ball_y + random.uniform(-15, 15)
        self.ai_y += (target - self.ai_y) * 0.22
        self.ai_y = max(self.paddle_h/2, min(720-self.paddle_h/2, self.ai_y))

        # Ball
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt

        # Trail
        self.ball_trail.append({'x': self.ball_x, 'y': self.ball_y, 'life': 0.5})
        self.ball_trail = [t for t in self.ball_trail if t['life'] > dt]

        # Bounce
        if self.ball_y < self.ball_r or self.ball_y > 720 - self.ball_r:
            self.ball_vy *= -1.03
            self.shake = max(10, self.shake + 8)
            self.ball_y = max(self.ball_r, min(720-self.ball_r, self.ball_y))

        # Player hit
        py1, py2 = self.player_y - self.paddle_h/2, self.player_y + self.paddle_h/2
        if self.ball_x + self.ball_r > 1260 and py1 < self.ball_y < py2:
            self.ball_vx = -abs(self.ball_vx) * 1.08
            self.ball_vy += (self.ball_y - self.player_y) * 3.2
            self.shake += 16
            self.ball_x = 1260 - self.ball_r
            if self.sound: self.sound.create_target_hit().play()

        # AI hit
        ay1, ay2 = self.ai_y - self.paddle_h/2, self.ai_y + self.paddle_h/2
        if self.ball_x - self.ball_r < 20 and ay1 < self.ball_y < ay2:
            self.ball_vx = abs(self.ball_vx) * 1.05
            self.ball_vy += (self.ball_y - self.ai_y) * 2.8
            self.shake += 16
            self.ball_x = 20 + self.ball_r
            if self.sound: self.sound.create_target_hit().play()

        # Score
        if self.ball_x < 0:
            self.ai_pts += 1
            self.score += 30
            self._reset_ball()
            if self.sound: self.sound.create_combo(self.ai_pts).play()
        elif self.ball_x > 1280:
            self.player_pts += 1
            self.score += 80
            self._reset_ball()
            if self.sound: self.sound.create_combo(self.player_pts).play()

        # 🔥 GAME OVER - SOLO FLAG, NIENTE DRAW
        if self.player_pts >= 5 or self.ai_pts >= 5:
            self.is_game_over = True
            self.score += 5000
            # NO SUONI QUI - motore li gestisce

    def _reset_ball(self):
        self.ball_x = 640
        self.ball_y = 360
        self.ball_vx = 360 * random.choice([-1, 1])
        self.ball_vy = random.uniform(-260, 260)

    def draw(self, surface):
        sx = math.sin(pygame.time.get_ticks() * 0.03) * self.shake
        sy = math.cos(pygame.time.get_ticks() * 0.02) * self.shake * 0.6
        self.shake *= 0.85
        
        temp = pygame.Surface((1280, 720))

        # Background
        for y in range(720):
            pulse = math.sin(pygame.time.get_ticks() * 0.0015 + y * 0.008) * 10
            pygame.draw.line(temp, self._safe_color(4+pulse, 8+pulse, 18+y//12), (0,y), (1280,y))

        # Center line
        for i in range(30):
            pygame.draw.rect(temp, (140,170,220), (638+sx, i*24+sy, 4, 16))

        # Trail
        for t in self.ball_trail:
            a = t['life'] * 3
            s = max(1, int(self.ball_r * a * 0.4))
            pygame.draw.circle(temp, self._safe_color(160*a, 210*a, 255), 
                             (int(t['x']+sx), int(t['y']+sy)), s)

        # Ball
        pygame.draw.circle(temp, (255,255,255), (int(self.ball_x+sx), int(self.ball_y+sy)), self.ball_r)
        pygame.draw.circle(temp, (200,230,255), (int(self.ball_x+sx), int(self.ball_y+sy)), 5)

        # Paddles
        pygame.draw.rect(temp, (70,160,255), (1260+sx, self.player_y-self.paddle_h/2+sy, self.paddle_w, self.paddle_h))
        pygame.draw.rect(temp, (255,130,70), (sx, self.ai_y-self.paddle_h/2+sy, self.paddle_w, self.paddle_h))
        pygame.draw.rect(temp, (255,255,255), (1260+sx, self.player_y-self.paddle_h/2+sy, self.paddle_w, self.paddle_h), 3)
        pygame.draw.rect(temp, (255,255,255), (sx, self.ai_y-self.paddle_h/2+sy, self.paddle_w, self.paddle_h), 3)

        # Scores
        p_txt = self.font_score.render(str(self.player_pts), True, (255,240,200))
        a_txt = self.font_score.render(str(self.ai_pts), True, (240,230,255))
        temp.blit(p_txt, (920+sx-p_txt.get_width()//2, 160+sy))
        temp.blit(a_txt, (360+sx-a_txt.get_width()//2, 160+sy))

        # Labels
        pygame.draw.line(temp, (255,255,255), (420+sx, 280+sy), (860+sx, 280+sy), 2)
        p_lab = self.font_label.render("YOU", True, (255,255,255))
        a_lab = self.font_label.render("AI", True, (255,255,255))
        temp.blit(p_lab, (920+sx-p_lab.get_width()//2, 300+sy))
        temp.blit(a_lab, (360+sx-a_lab.get_width()//2, 300+sy))

        # 🔥 SOLO PAUSA LOCALE - NO GAME OVER
        if self.is_paused:
            ov = pygame.Surface((1280,720), pygame.SRCALPHA)
            ov.fill((20,30,60,220))
            temp.blit(ov, (0,0))
            pst = self.font_score.render("PAUSA", True, (200,240,255))
            temp.blit(pst, (640-pst.get_width()//2+sx, 360+sy))

        surface.blit(temp, (0,0))
