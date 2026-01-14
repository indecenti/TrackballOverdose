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








Comportati come un esperto sviluppatore Python e Pygame. Analizza il file engine.txt e, seguendo scrupolosamente tutte le istruzioni e le specifiche indicate senza cambiare nome ai metodi o alle variabili, sviluppa un gioco pienamente compatibile con l’engine. Fornisci il codice completo e funzionante, rispettando rigorosamente le convenzioni:
# 📋 REGOLA #1: NESSUN CAMELCASE - MAI

**Tutte** variabili, metodi, attributi: `snake_case` con underscore `_`


Considera che il gioco deve funzionare con una trackball arcade che gestisce due assi e tre pulsanti: sinistro, destro e centrale (click rotella).

Analizza attentamente il controller e implementa una calibrazione adeguata in base al gioco richiesto.


Assicurati che i suoni vengano riprodotti solo nella funzione update() quando il gioco è effettivamente in corso, non in reset(), per evitare malfunzionamenti.

Analizza attentamente il codice dell’engine e correggi eventuali bug, garantendo la piena stabilità del gioco.

Presta particolare attenzione alla firma delle classi e funzioni che ereditano dall’engine, soprattutto all’uso corretto di *args e **kwargs, così come agli argomenti keyword come sound=None.

Fornisci una versione testata e funzionante del gioco, compatibile con tutte le funzionalità specificate in engine.txt. NIENTE ALLUCINAZIONI, non inventare. ragiona.

Alla fine, consegna il codice completo pronto da eseguire, con commenti chiari sulle parti critiche, in particolare gestione del controller, calibrazione trackball, suoni e update loop.   self.sound.create_game_start().play() giusto, self.sound.create_game_start.play() sbagliato, stai attento ad errori come questo con synth, trackball.getsmoothdelta() sbagliato, trackball.get_smooth_delta() corretto continui a fare errori cosi non leggi bene gli allegati fai di meglio ragiona.cura le grafiche aggiungi animazioni, voglio un sistema a livelli, un gioco evoluto, completo, arcade stile fumettistico, almeno 1200 righe di codice senza commenti inutili.