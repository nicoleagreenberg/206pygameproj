import pygame
import time
import random
import sys

from pygame.locals import Rect, DOUBLEBUF, QUIT, K_ESCAPE, KEYDOWN, K_DOWN, \
    K_LEFT, K_UP, K_RIGHT, KEYUP, K_LCTRL, K_RETURN, FULLSCREEN #saves these locally so you don't have to type pygame.whatever

X_MAX = 800
Y_MAX = 600 #set dimensions of game using constants 

LEFT, RIGHT, UP, DOWN = 0, 1, 3, 4
START, STOP = 0, 1

bg = pygame.image.load("stovetop.bmp")
bg_x = 0
bg_y = 400

everything = pygame.sprite.Group()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super(Explosion, self).__init__()
        sheet = pygame.image.load("x.bmp")
        self.images = []
        for i in range(0, 768, 48):
            rect = pygame.Rect((i, 0, 48, 48))
            image = pygame.Surface(rect.size)
            image.blit(sheet, (0, 0), rect)
            self.images.append(image)

        self.image = self.images[0]
        self.index = 0
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.add(everything)

    def update(self):
        self.image = self.images[self.index]
        self.index += 1
        if self.index >= len(self.images):
            self.kill()

class Fried(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super(Fried, self).__init__()
        self.image = pygame.image.load("friedegg.bmp").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.add(everything)
        self.explosion_sound = pygame.mixer.Sound("oops.wav")
        self.index = 0

    def update(self):
        self.index += 1
        if self.index >= 5:
            self.kill()

class EggSprite(pygame.sprite.Sprite):
    def __init__(self, x_pos, groups):
        super(EggSprite, self).__init__()
        self.image = pygame.image.load("egg2.bmp").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x_pos, 0)
        self.velocity = random.randint(1, 4)
        self.add(groups)
        self.crack_sound = pygame.mixer.Sound("eggcrack.wav")
        self.sizzle_sound = pygame.mixer.Sound("sizzle.wav")
        self.explosion_sound = pygame.mixer.Sound("oops.wav")
        self.explosion_sound.set_volume(0.4)

    def update(self):
        x, y = self.rect.center
        if y > Y_MAX:
            x, y = random.randint(0, X_MAX), 0
            self.velocity = random.randint(1, 4)
        else:
            x, y = x, y + self.velocity
        self.rect.center = x, (y+5)

    def fry(self):
        x, y = self.rect.center
        if pygame.mixer.get_init():
            self.crack_sound.play(maxtime=1000)
            self.sizzle_sound.play(maxtime=1000)
            Fried(x, y)
        super(EggSprite, self).kill()

    def explode(self):
        x, y = self.rect.center
        if pygame.mixer.get_init():
            self.explosion_sound.play(maxtime=1000)
            Explosion(x, y)
        super(EggSprite, self).kill()
    
class StatusSprite(pygame.sprite.Sprite):
    def __init__(self, pan, groups):
        super(StatusSprite, self).__init__()
        self.image = pygame.Surface((X_MAX, 30))
        self.rect = self.image.get_rect()
        self.rect.bottomleft = 0, Y_MAX

        default_font = pygame.font.get_default_font()
        self.font = pygame.font.Font(default_font, 20)

        self.pan = pan
        self.add(groups)

    def update(self):
        score = self.font.render("Health Score: : {} Fried Eggs : {}".format(
            self.pan.health, self.pan.score), True, (150, 50, 50))
        self.image.fill((0, 0, 0))
        self.image.blit(score, (0, 0))

class PanSprite(pygame.sprite.Sprite):
    def __init__(self, groups):
        super(PanSprite, self).__init__()
        self.image = pygame.image.load("redpan1.bmp").convert()
        self.TransColor = self.image.get_at((0,0))
        self.image.set_colorkey((self.TransColor))
        self.rect = self.image.get_rect()
        self.rect.center = (X_MAX/2, Y_MAX - 40)
        self.dx = self.dy = 0 #how much to move when you hit arrow 
        self.health = 500
        self.score = 0
        self.groups = [groups]
        self.mega = 1
        self.autopilot = False
        self.in_position = False
        self.velocity = 2

    def update(self):
        x, y = self.rect.center

        if not self.autopilot:
            self.rect.center = x + self.dx, y + self.dy
            if self.health < 0:
                self.kill()
        else:
            if not self.in_position:
                if x != X_MAX/2:
                    x += (abs(X_MAX/2 - x)/(X_MAX/2 - x)) * 2
                if y != Y_MAX - 100:
                    y += (abs(Y_MAX - 100 - y)/(Y_MAX - 100 - y)) * 2

                if x == X_MAX/2 and y == Y_MAX - 100:
                    self.in_position = True
            else:
                y -= self.velocity
                self.velocity *= 1.5
                if y <= 0:
                    y = -30
            self.rect.center = x, y

    def steer(self, direction, operation):
        v = 10
        if operation == START:
            if direction in (UP, DOWN):
                self.dy = {UP: -v,
                           DOWN: v}[direction]

            if direction in (LEFT, RIGHT):
                self.dx = {LEFT: -v,
                           RIGHT: v}[direction]

        if operation == STOP:
            if direction in (UP, DOWN):
                self.dy = 0
            if direction in (LEFT, RIGHT):
                self.dx = 0

def main():
    game_over = False

    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((X_MAX, Y_MAX), DOUBLEBUF)
    enemies = pygame.sprite.Group()

    empty = pygame.Surface((X_MAX, Y_MAX))
    clock = pygame.time.Clock()

    pan = PanSprite(everything)
    pan.add(everything)

    status = StatusSprite(pan, everything)

    deadtimer = 30
    credits_timer = 250

    for i in range(4):
        pos = random.randint(0, X_MAX)
        EggSprite(pos, [everything, enemies])
    while True:
        clock.tick(30)
        # Check for input
        for event in pygame.event.get():
            if event.type == QUIT or (
                    event.type == KEYDOWN and event.key == K_ESCAPE):
                sys.exit()

            if not game_over:
                if event.type == KEYDOWN:
                    if event.key == K_DOWN:
                        pan.steer(DOWN, START)
                    if event.key == K_LEFT:
                        pan.steer(LEFT, START)
                    if event.key == K_RIGHT:
                        pan.steer(RIGHT, START)
                    if event.key == K_UP:
                        pan.steer(UP, START)
                    if event.key == K_LCTRL:
                        pan.shoot(START)
                    if event.key == K_RETURN:
                        if pan.mega:
                            pan.mega -= 1
                            for i in enemies:
                                i.kill()

                if event.type == KEYUP:
                    if event.key == K_DOWN:
                        pan.steer(DOWN, STOP)
                    if event.key == K_LEFT:
                        pan.steer(LEFT, STOP)
                    if event.key == K_RIGHT:
                        pan.steer(RIGHT, STOP)
                    if event.key == K_UP:
                        pan.steer(UP, STOP)
                    if event.key == K_LCTRL:
                        pan.shoot(STOP)

        # Check for impact
        if pan.health < 0:
            if deadtimer:
                deadtimer -= 1
                game_over = True
            else:
                sys.exit()

        # Check for successful attacks
        hit_pan = pygame.sprite.spritecollide(pan, enemies, True) 
        
        for k in hit_pan:
            k.fry()
            pan.score += 1

        if len(enemies) < 3 and not game_over:
            pos = random.randint(0, X_MAX)
            EggSprite(pos, [everything, enemies])

        for i in enemies:
            if i.rect.center[1]>400:
                pan.health -= 10
                i.explode()

        # Check for game over
        if pan.score > 2000:
            game_over = True
            for i in enemies:
                i.explode()

            pan.autopilot = True
            pan.shoot(STOP)

        if game_over:
            if credits_timer:
                credits_timer -= 1
            else:
                print("GAME OVER")
                sys.exit()

        # Update sprites
        screen.blit(bg, (bg_x, bg_y))
        everything.clear(screen, empty)
        everything.update()
        everything.draw(screen)
        pygame.display.flip()



if __name__ == '__main__':
    main()
