import pygame as g
from pygame.math import Vector2
from physics import Body
from physics import Bbox
from enemy import Enemy
from paper import Paper


INVINCIBILITY = 1.5 # 1.5s

def chandler(collision):
    player = None
    bounce = None
    if isinstance(collision.a.body, Enemy):
        player = collision.b.body
        bounce = Vector2(collision.intersection[0], collision.intersection[1])
    elif isinstance(collision.b.body, Enemy):
        player = collision.a.body
        bounce = Vector2(-collision.intersection[0], -collision.intersection[1])
    if player:
        if player.invincible <= 0:
            player.health -= 1
            player.apply_force(bounce)
            player.invincible = INVINCIBILITY

    if isinstance(collision.a.body, Paper):
        player = collision.b.body
        paper = collision.a.body
        player.game.world.remove(paper)
        player.papers += 1
    elif isinstance(collision.b.body, Paper):
        player = collision.a.body
        paper = collision.b.body
        player.game.world.remove(paper)
        player.papers += 1


class Player(Body):
    def __init__(self, game):
        self.game = game
        position_x = 250
        position_y = self.game.resolution[1] - 100
        self.width = 50
        self.height = 50
        self.health = 3
        self.invincible = 0
        self.papers = 0

        self.on_ground = False

        shape = Bbox(position_x, position_y, self.width, self.height)
        shape.elayers = 0b100
        shape.ilayers = 0b001
        super(Player, self).__init__(position_x, position_y, shape, self.game.gravity, 0.8)
        shape.on_collide(chandler)

    def jump(self):
        if self.on_ground:
            self.velocity[1] = 0
            self.apply_force(Vector2(0, -self.game.jump_force))
            self.on_ground = False

    def moveLeft(self):
        self.game.camera.set_pos(self.position[0] - self.game.resolution[0] / 2, 0)
        self.apply_force(Vector2(-self.game.move_speed, 0))

    def moveRight(self):
        self.game.camera.set_pos(self.position[0] - self.game.resolution[0] / 2, 0)
        self.apply_force(Vector2(self.game.move_speed, 0))

    def update(self, dt):
        # Input
        pressed = g.key.get_pressed()
        if pressed[g.K_w]:
            self.jump()
        if pressed[g.K_a]:
            self.moveLeft()
        if pressed[g.K_d]:
            self.moveRight()

        if self.velocity[0] > self.game.max_speed:
            self.velocity[0] = self.game.max_speed
        if self.velocity[0] < -self.game.max_speed:
            self.velocity[0] = -self.game.max_speed

        if self.invincible > 0:
            self.invincible -= dt

    def draw(self):
        if self.invincible > 0:
            self.game.camera.draw(g.draw.ellipse, (0, 100, 0), self.position, (self.width, self.height))
        else:
            self.game.camera.draw(g.draw.ellipse, (0, 255, 0), self.position, (self.width, self.height))
