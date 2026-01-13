# Trackball Arcade System – ROM API

**Fonte canonica e normalizzata per modelli di AI generativi**

Questa documentazione descrive in modo **formale, non ambiguo e completo** l’API per sviluppare ROM (minigiochi) per il **Trackball Arcade System**. È pensata per essere usata come **knowledge source** da un modello di AI generativo che deve:

* Generare ROM valide
* Validare codice ROM
* Suggerire fix conformi alle regole del motore

---

## 1. Concetti Fondamentali

* Ogni ROM è un **file Python **`` nella cartella `roms/`
* Ogni ROM **deve** definire **una classe** che eredita da `MiniGame`
* Il motore gestisce:

  * Ciclo di vita (init → update → draw → game over → reset)
  * Pausa globale
  * High score
  * Audio di sistema

La ROM **non deve**:

* Gestire schermate di Game Over
* Salvare punteggi
* Intercettare input di pausa globale

---

## 2. Struttura Minima Obbligatoria

```python
import pygame
import math
import random

class NomeGioco(MiniGame):
    def __init__(self, *args, sound=None, **kwargs):
        super().__init__("NomeGioco", "Descrizione breve del gioco", *args, **kwargs)
        self.sound = sound
        self.reset()

    def reset(self):
        pass

    def update(self, dt: float, trackball):
        pass

    def draw(self, surface: pygame.Surface):
        pass
```

Se **anche uno solo** di questi elementi manca → **ROM NON VALIDA**.

---

## 3. Metodo `__init__` (OBBLIGATORIO)

### Firma obbligatoria

```python
def __init__(self, *args, sound=None, **kwargs):
```

### Comportamento obbligatorio

```python
super().__init__("NomeVisibile", "Descrizione carousel", *args, **kwargs)
self.sound = sound
self.reset()
```

### Regole per AI generativa

* ❌ Non cambiare firma
* ❌ Non omettere `super()`
* ❌ Non inizializzare stato qui
* ✅ Tutto lo stato va in `reset()`

---

## 4. Metodo `reset()` – Reset Stato Gioco

### Scopo

Ripristina **completamente** lo stato iniziale del gioco.

Chiamato automaticamente quando:

* La ROM viene caricata
* `is_game_over` diventa `True`
* L’utente preme **Right** durante pausa

### Contenuto minimo richiesto

```python
def reset(self):
    self.score = 0
    self.is_game_over = False
    self.is_paused = False

    # Stato gioco
    self.player_x = 640
    self.player_y = 360
    self.lives = 3
```

### Regola critica

> ``** non deve mai ricevere parametri**

---

## 5. Metodo `update(dt, trackball)` – Logica di Gioco

### Firma obbligatoria

```python
def update(self, dt: float, trackball):
```

### Pattern obbligatorio (DA COPIARE)

```python
def update(self, dt: float, trackball):
    if self.is_paused or self.is_game_over:
        return

    # INPUT + AUDIO
    dx, dy = trackball.get_smooth_delta()
    self.player_x += dx * 300 * dt
    self.player_y += dy * 300 * dt

    if trackball.button_left_pressed and self.sound:
        self.sound.create_shoot().play()
        self.fire_bullet()

    # HIT + AUDIO
    if self.check_collision():
        self.sound.create_target_hit().play()
        self.score += 100
```

### Regole di Game Over

```python
if self.lives <= 0:
    self.is_game_over = True
    self.score += 5000
    return
```

❌ Non disegnare Game Over ❌ Non riprodurre suoni di Game Over

---

## 6. TrackballInput – API Completa

| Metodo / Proprietà      | Tipo           | Descrizione                          |
| ----------------------- | -------------- | ------------------------------------ |
| `get_smooth_delta()`    | (float, float) | Delta X/Y filtrato (RACCOMANDATO)    |
| `get_delta()`           | (float, float) | Delta raw                            |
| `get_velocity()`        | (float, float) | Velocità                             |
| `button_left_pressed`   | bool           | Click sinistro (solo frame corrente) |
| `button_middle_pressed` | bool           | Click centrale                       |
| `button_right_pressed`  | bool           | Click destro                         |
| `button_left`           | bool           | Sinistro tenuto                      |
| `button_middle`         | bool           | Centrale tenuto                      |
| `button_right`          | bool           | Destro tenuto                        |

---

## 7. Metodo `draw(surface)` – Rendering

### Firma obbligatoria

```python
def draw(self, surface: pygame.Surface):
```

### Specifiche superficie

* Dimensioni fisse: **1280 × 720 (16:9)**
* Scaling gestito dal motore

### Best practice

```python
def draw(self, surface):
    self.draw_background(surface)
    self.draw_entities(surface)
    self.draw_ui(surface)

    if self.is_paused:
        self.draw_pause_overlay(surface)
```

---

## 8. Sistema di Punteggio

* `self.score` è **cumulativo**
* Incrementare spesso e in modo progressivo

```python
self.score += int(10 * dt)      # tempo
self.score += 100               # hit
self.score += 5000              # bonus finale
```

Il motore:

* Salva automaticamente high score
* Mostra ranking

---

## 9. SoundSynthesizer API

Disponibile come `self.sound`

| Metodo                | Descrizione             |
| --------------------- | ----------------------- |
| `create_game_start()` | Avvio gioco             |
| `create_target_hit()` | Colpo                   |
| `create_combo(level)` | Combo 1–9               |
| `create_shoot()`      | Sparo                   |
| `create_pause()`      | Pausa                   |
| `create_game_over()`  | Game Over (solo motore) |
| `create_high_score()` | Nuovo record            |

Uso corretto:

```python
if self.sound:
    self.sound.create_target_hit().play()
```

---

## 10. Gestione Pausa

### Pausa globale (MOTORE)

* Bottone centrale
* `update()` non viene chiamato

### Pausa locale (OPZIONALE)

```python
def pause(self):
    self.is_paused = True

def resume(self):
    self.is_paused = False
```

Overlay consentito in `draw()`.

---

## 11. Workflow Game Over (Canonico)

```text
update() → set is_game_over = True
        → motore chiama reset()
        → mostra schermata GAME OVER
        → salva score
```

La ROM **non controlla il flusso UI**.

---

## 12. Errori Comuni (Da Evitare)

| Errore                            | Motivo                  |
| --------------------------------- | ----------------------- |
| `__init__(self, sound)`           | Firma non valida        |
| Stato inizializzato in `__init__` | Deve stare in `reset()` |
| Disegnare Game Over               | Gestito dal motore      |
| Non usare `get_smooth_delta()`    | Movimento non corretto  |

---

## 13. Obiettivo per AI Generativa

Un modello che usa questo documento **deve essere in grado di**:

* Generare ROM valide al primo tentativo
* Correggere ROM non conformi
* Non violare mai le firme obbligatorie
* Usare correttamente audio, input e score

Questa documentazione è **la fonte di verità**.
