import itertools
from pygame.math import Vector2
from enum import Enum

# trzy opcje kolizji między objektami
class Intersects(Enum):
    No = 0  # nie nachodzą na siebie
    Yes = 1 # są na identycznych warstwach oraz nachodzą na siebie
    NA = 2  # są na różnych warstwach, ale nachodzą na siebie

# axis aligned bounding box
class Bbox(object):
    # parametry: pozycja (x,y), rozmiar (w,h), handlery początku i końca kolizji
    def __init__(self, x, y, w, h, on_collide=None, on_uncollide=None):
        self.on_collide(on_collide, on_uncollide)
        self.position = Vector2(x, y)
        self.w = w
        self.h = h
        self.elayers = 0
        self.ilayers = 0

    def setpos(self, pos):
        self.position = pos

    # zwraca typ kolizji
    def collides(self, other):
        if isinstance(other, Bbox):
            if self.position[0] < other.position[0] + other.w \
                and self.position[0] + self.w > other.position[0] \
                and self.position[1] < other.position[1] + other.h \
                and self.position[1] + self.h > other.position[1]:
                if self.ilayers & other.elayers == 0 or \
                    self.elayers & other.ilayers == 0:
                    return Intersects.NA
                return Intersects.Yes
            else:
                return Intersects.No
        else:
            return Intersects.No

    # zwraca parę (x,y) wartości jak dwa bbox'y na siebie nachodzą
    def intersection(self, other):
        x = None
        y = None

        if self.position[0] < other.position[0] + other.w:
            x = self.position[0] - (other.position[0] + other.w)
        if self.position[0] + self.w > other.position[0]:
            x = self.position[0] + self.w - other.position[0]
        if self.position[1] < other.position[1] + other.h:
            y = self.position[1] - (other.position[1] + other.h)
        if self.position[1] + self.h > other.position[1]:
            y = self.position[1] + self.h - other.position[1]

        return (x, y)

    # ustawia handlery
    def on_collide(self, cb_begin=None, cb_end=None):
        self.collision_begin = cb_begin
        self.collision_end = cb_end

# superklasa konkretnych objektów fizycznych
class Body(object):
    # parametry: pozycja (x,y), bounding box, [grawitacja], [tarcie]
    def __init__(self, x, y, shape, gravity=0, friction=0):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, 0) # w rzeczywistości impuls, nie przyspieszenie
        self.gravity = Vector2(0, gravity)
        self.friction = friction
        self.shape = shape
        # statyczne ciała nie są aktualizowane
        self.static = False
        # dict z ciał z którymi to ciało koliduje
        self.colliding = {}

        shape.body = self

    # metoda wywołana dla wszystkich objektów w World.update
    def update(self, dt):
        pass

    def setpos(self, pos=None):
        if pos:
            self.position = pos

        self.shape.setpos(self.position)

    def apply_force(self, force):
        self.acceleration += force

    def collides(self, other):
        return self.shape.collides(other.shape)

    def intersection(self, other):
        return self.shape.intersection(other.shape)

# objekt reprezentujący kolizję między dwoma ciałami
class Collision(object):
    def __init__(self, a, b, intersects):
        self.intersection = a.body.intersection(b.body)
        self.a = a
        self.b = b
        self.intersects = intersects

    # zacznij kolizję dla obu ciał
    def do_begin(self):
        if self.a.collision_begin:
            self.a.collision_begin(self)

        if self.b.collision_begin:
            self.b.collision_begin(self)

    # zakończ kolizję dla obu ciał
    def do_end(self):
        if self.a.collision_end:
            self.a.collision_end(self)

        if self.b.collision_end:
            self.b.collision_end(self)

# objekt reprezentujący stan świata
class World(object):
    def __init__(self, bodies=[]):
        self.bodies = bodies
        # lista ciał do usunięcia po zakończeniu aktualizacji
        self.kill = []
        self.updating = False

    def add_body(self, body):
        self.bodies.append(body)

    def remove(self, body):
        if not self.updating:
            self.bodies.pop(body)
        else:
            self.kill.append(body)

    # resetuje cały świat
    def ragnarok(self):
        self.bodies = []
        self.kill = []
        self.updating = False

    # parametry: dt — czas od ostatniego wywołania tej funkcji
    def update(self, dt):
        self.updating = True

        for (i, body) in enumerate(self.bodies):
            # statyczne ciała są ignorowane
            if not body.static:
                # dodajemy przyspieszenie i grawitację do prędkości
                body.velocity += (body.acceleration + body.gravity) * dt

                # dict z ciał z którymi `body` koliduje w tej chwili
                colliding = {}

                # dwa wymiary, x oraz y, są sprawdzane osobno
                for dim in [0, 1]:
                    # aktualizacja pozycji w jednym wymiarze
                    body.position[dim] += body.velocity[dim] * dt
                    body.setpos()

                    # wszystkie ciała które nie są tym ciałem
                    bodies = iter(other for other in self.bodies if body != other)
                    # wszystkie kolizje z tymi ciałami
                    collisions = iter(Collision(body.shape, other.shape, body.collides(other)) for other in bodies)

                    for collision in collisions:
                        # jeśli nie ma kolizji, idziemy dalej
                        if collision.intersects == Intersects.No:
                            continue

                        other = collision.b.body
                        colliding[other] = True

                        # jeśli jeszcze nie kolidujemy z tym ciałem, wywołujemy
                        # handler
                        if other not in body.colliding:
                            body.colliding[other] = collision
                            other.colliding[body] = collision
                            collision.do_begin()

                        # jeśli kolizja istnieje na tej samej warstwie, ciało
                        # nie może się ruszyć dalej niż drugie ciało
                        if collision.intersects == Intersects.Yes:
                            body.position[dim] -= collision.intersection[dim]
                            body.velocity[dim] = 0
                            body.setpos()

                # lista ciał z którymi dane ciało już nie koliduje
                remove = []
                for other, collision in body.colliding.items():
                    if other not in colliding:
                        # zakończenie kolizji
                        collision.do_end()
                        remove.append(other)

                # usunięcie niestniejących kolizji
                for other in remove:
                    del body.colliding[other]
                    del other.colliding[body]

                # tarcie
                body.velocity[0] *= 1.0 - body.friction
                body.acceleration *= 0

                body.update(dt)

        # lista ciał do usunięcia po zakończeniu aktualizacji
        for body in self.kill:
            self.bodies.remove(body)

        self.kill = []

        self.updating = False
