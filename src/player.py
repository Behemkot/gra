import pygame as g
from pygame.math import Vector2
from physics import Body
from physics import Rectangle


class Player(Body):
    def __init__(self, game):
        self.game = game
        position_x = self.game.resolution[0]/2 - 25
        position_y = 250
        self.width = 50
        self.height = 50

        self.on_ground = False

        shape = Rectangle(position_x, position_y, self.width, self.height)
        super(Player, self).__init__(position_x, position_y, [shape], self.game.gravity, 0.8)

    def jump(self):
        if self.on_ground:
            self.apply_force(Vector2(0, -self.game.jump_force))
            self.on_ground = False

    def moveLeft(self):
        self.apply_force(Vector2(-self.game.move_speed, 0))

    def moveRight(self):
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

    def draw(self):
        box = g.Rect(self.position[0], self.position[1], self.width, self.height)
        g.draw.ellipse(self.game.screen, (0, 255, 0), box)
