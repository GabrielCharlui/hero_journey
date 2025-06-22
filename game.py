import pgzrun
import math
import random
import sys

WIDTH = 800
HEIGHT = 600

game_state = "menu"
sound_on = True
camera_offset = [0, 0]
hero_health = 100
difficulty = "Normal"
enemy_damage = 1
enemy_health = 100

HERO_IDLE = [f"hero_idle_{i}" for i in range(1, 7)]
HERO_WALK = [f"hero_walk_{i}" for i in range(1, 4)]
HERO_ATTACK = [f"hero_attack_{i}" for i in range(1, 6)]
HERO_DEAD = [f"hero_dead_{i}" for i in range(1, 5)]

ENEMY_IDLE = [f"mob_idle_{i}" for i in range(1, 9)]
ENEMY_WALK = [f"mmob_walk_{i}" for i in range(1, 9)]
ENEMY_ATTACK = [f"mob_attack_{i}" for i in range(1, 6)]
ENEMY_DEAD = [f"mob_dead_{i}" for i in range(1, 4)]

buttons = {
    "start": Rect((300, 200), (200, 50)),
    "sound": Rect((300, 270), (200, 50)),
    "difficulty": Rect((300, 340), (200, 50)),
    "exit": Rect((300, 410), (200, 50))
}

def play_music():
    if sound_on and not music.is_playing('background_music'):
        music.play('background_music')

def stop_music():
    music.stop()

def play_victory_music():
    if sound_on:
        music.stop()
        sounds.wanner.play()  

class Hero:
    def __init__(self):
        self.actor = Actor(HERO_IDLE[0], center=(WIDTH // 2, HEIGHT // 2))
        self.frame = 0
        self.frame_count = 0
        self.speed = 4
        self.flipped = False
        self.attacking = False
        self.attack_timer = 0
        self.dead = False
        self.death_frame = 0
        self.death_timer = 0

    def update(self, keys):
        if self.dead:
            self.handle_death_animation()
            return

        if self.attacking:
            self.handle_attack_animation()
            return

        moving = False
        if keys.right:
            camera_offset[0] += self.speed
            self.flipped = False
            moving = True
        elif keys.left:
            camera_offset[0] -= self.speed
            self.flipped = True
            moving = True
        if keys.up:
            camera_offset[1] -= self.speed
            moving = True
        elif keys.down:
            camera_offset[1] += self.speed
            moving = True

        if moving:
            self.frame_count += 1
            if self.frame_count % 6 == 0:
                self.frame = (self.frame + 1) % len(HERO_WALK)
                self.actor.image = HERO_WALK[self.frame]
        else:
            self.actor.image = HERO_IDLE[0]

        self.actor.flip_x = self.flipped
        self.actor.pos = (WIDTH // 2, HEIGHT // 2)

    def start_attack(self):
        if not self.dead and not self.attacking:
            self.attacking = True
            self.frame = 0
            self.frame_count = 0
            self.attack_timer = 0

    def handle_attack_animation(self):
        self.attack_timer += 1
        if self.attack_timer % 4 == 0:
            self.frame += 1
            if self.frame >= len(HERO_ATTACK):
                self.attacking = False
                self.actor.image = HERO_IDLE[0]
                return
            self.actor.image = HERO_ATTACK[self.frame]

    def start_death(self):
        self.dead = True
        self.death_frame = 0
        self.death_timer = 0

    def handle_death_animation(self):
        self.death_timer += 1
        if self.death_timer % 10 == 0 and self.death_frame < len(HERO_DEAD):
            self.actor.image = HERO_DEAD[self.death_frame]
            self.death_frame += 1
        if self.death_frame >= len(HERO_DEAD):
            global game_state
            if game_state != "gameover":
                game_state = "gameover"
                stop_music()
                if sound_on:
                    sounds.game_over.play()

    def draw(self):
        self.actor.draw()

class Enemy:
    def __init__(self, x, y):
        self.actor = Actor(ENEMY_IDLE[0], pos=(x, y))
        self.origin = (x, y)
        self.frame = 0
        self.frame_count = 0
        self.state = "idle"
        self.speed = 1.5
        self.direction = random.choice(["up", "down", "left", "right"])
        self.health = enemy_health
        self.dead = False
        self.death_frame = 0
        self.death_timer = 0

    def update(self, hero_world_pos):
        if self.dead and self.state != "dying":
            self.state = "dying"
            self.frame = 0
            self.frame_count = 0
            self.death_frame = 0
            self.death_timer = 0

        if self.state == "dying":
            self.handle_death_animation()
            return

        self.frame_count += 1
        if self.state == "idle" and self.frame_count % 8 == 0:
            self.frame = (self.frame + 1) % len(ENEMY_IDLE)
            self.actor.image = ENEMY_IDLE[self.frame]
        elif self.state == "attack" and self.frame_count % 6 == 0:
            self.frame = (self.frame + 1) % len(ENEMY_ATTACK)
            self.actor.image = ENEMY_ATTACK[self.frame]

        if self.state == "idle":
            self.patrol()
            if self.distance_to(hero_world_pos) < 120:
                self.state = "attack"
                self.frame = 0
        elif self.state == "attack":
            self.chase(hero_world_pos)

    def patrol(self):
        dx = dy = 0
        if self.direction == "left": dx = -self.speed
        elif self.direction == "right": dx = self.speed
        elif self.direction == "up": dy = -self.speed
        elif self.direction == "down": dy = self.speed

        self.actor.x += dx
        self.actor.y += dy

        if abs(self.actor.x - self.origin[0]) > 100 or abs(self.actor.y - self.origin[1]) > 100:
            self.direction = random.choice(["up", "down", "left", "right"])

    def chase(self, hero_pos):
        angle = math.atan2(hero_pos[1] - self.actor.y, hero_pos[0] - self.actor.x)
        self.actor.x += math.cos(angle) * self.speed
        self.actor.y += math.sin(angle) * self.speed

    def distance_to(self, hero_pos):
        return math.hypot(hero_pos[0] - self.actor.x, hero_pos[1] - self.actor.y)

    def draw(self):
        if self.state == "dying" and self.death_frame >= len(ENEMY_DEAD):
            return
        screen.blit(self.actor.image, (
            self.actor.x - camera_offset[0] - self.actor.width // 2,
            self.actor.y - camera_offset[1] - self.actor.height // 2
        ))

    def take_damage(self, amount):
        if self.state == "dying":
            return
        self.health -= amount
        if self.health <= 0:
            self.dead = True

    def handle_death_animation(self):
        self.death_timer += 1
        if self.death_timer % 10 == 0 and self.death_frame < len(ENEMY_DEAD):
            self.actor.image = ENEMY_DEAD[self.death_frame]
            self.death_frame += 1

background = Actor("scene_forest_top", topleft=(0, 0))
hero = Hero()

def draw():
    screen.clear()
    if game_state == "menu":
        draw_menu()
    elif game_state == "jogo":
        draw_game()
    elif game_state == "gameover":
        draw_gameover()
    elif game_state == "vitoria":
        draw_victory()

def draw_menu():
    screen.fill((30, 30, 30))
    screen.draw.text("MENU", center=(WIDTH // 2, 100), fontsize=50, color="white")
    labels = {
        "start": "Iniciar",
        "sound": f"Som: {'Ligado' if sound_on else 'Desligado'}",
        "difficulty": f"Dificuldade: {difficulty}",
        "exit": "Sair"
    }
    for key, rect in buttons.items():
        screen.draw.filled_rect(rect, (70, 130, 180))
        screen.draw.text(labels[key], center=rect.center, fontsize=24, color="white")

def draw_game():
    background.topleft = (-camera_offset[0], -camera_offset[1])
    background.draw()
    for enemy in enemies:
        enemy.draw()
    hero.draw()
    screen.draw.text(f"Vida: {int(hero_health)}", topleft=(10, 10), fontsize=26, color="red")
    screen.draw.text(f"[Pressione F para atacar]\n[Pressione as setas direcionais para mover o herói]", topleft=(10, 500), fontsize=26, color="white")

def draw_victory():
    screen.fill((0, 0, 0))
    screen.draw.text("VITÓRIA", center=(WIDTH//2, HEIGHT//2 - 50), fontsize=80, color="green")
    screen.draw.text("Clique para voltar ao menu", center=(WIDTH//2, HEIGHT//2 + 50), fontsize=40, color="white")
    

def draw_gameover():
    screen.fill((0, 0, 0))
    screen.draw.text("FIM DE JOGO", center=(WIDTH//2, HEIGHT//2 - 50), fontsize=80, color="red")
    screen.draw.text("Clique para voltar ao menu", center=(WIDTH//2, HEIGHT//2 + 50), fontsize=40, color="white")

def update():
    global hero_health, game_state

    if game_state != "jogo":
        return

    keys = keyboard
    hero.update(keys)

    hero_world = (camera_offset[0] + WIDTH // 2, camera_offset[1] + HEIGHT // 2)

    for enemy in enemies:
        enemy.update(hero_world)

        if enemy.state != "dying" and enemy.distance_to(hero_world) < 40:
            hero_health = max(hero_health - enemy_damage, 0)

        if hero_health == 0 and not hero.dead:
            hero.start_death()

        if hero.attacking and enemy.distance_to(hero_world) < 60 and enemy.state != "dying":
            enemy.take_damage(10)

    if all(enemy.dead for enemy in enemies):
        game_state = "vitoria"
        play_victory_music()

def on_key_down(key):
    if key == keys.F and game_state == "jogo":
        hero.start_attack()
        if sound_on:
            sounds.slash.play()

def on_mouse_down(pos):
    global game_state, sound_on, hero_health, camera_offset, enemies, hero
    global difficulty, enemy_damage, enemy_health

    if game_state == "menu":
        if buttons["start"].collidepoint(pos):
            game_state = "jogo"
            hero_health = 100
            camera_offset = [0, 0]
            enemies = [Enemy(200, 1200), Enemy(700, 1400), Enemy(900, 300), Enemy(1100, 900)]
            for e in enemies:
                e.health = enemy_health
            hero = Hero()
            if sound_on:
                play_music()
        elif buttons["sound"].collidepoint(pos):
            sound_on = not sound_on
            if sound_on:
                play_music()
            else:
                stop_music()
        elif buttons["difficulty"].collidepoint(pos):
            if difficulty == "Fácil":
                difficulty = "Normal"
                enemy_damage = 2
                enemy_health = 150
            elif difficulty == "Normal":
                difficulty = "Difícil"
                enemy_damage = 6
                enemy_health = 300
            elif difficulty == "Difícil":
                difficulty = "Fácil"
                enemy_damage = 0.5
                enemy_health = 60
        elif buttons["exit"].collidepoint(pos):
            sys.exit()

    elif game_state == "gameover":
        game_state = "menu"
        if sound_on:
            play_music()

    elif game_state == "vitoria":
        game_state = "menu"
        if sound_on:
            play_music()

pgzrun.go()
