class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other: "Vector"):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector"):
        return Vector(self.x - other.x, self.y - other.y)

    def __eq__(self, other: "Vector"):
        return self.x == other.x and self.y == other.y

    def __str__(self):
        return f"Vector({self.x}, {self.y})"

    @property
    def data(self):
        return [self.x, self.y]

    def to_screen(self):
        return Vector(self.x, -self.y)
