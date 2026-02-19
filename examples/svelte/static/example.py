import math
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


# --- Protocols & Abstract Types ---


@runtime_checkable
class Drawable(Protocol):
    """Any object that can be drawn on a canvas."""

    def draw(self, canvas: "Canvas") -> None: ...

    def bounding_box(self) -> "BoundingBox": ...


# --- Core Data Structures ---


@dataclass(frozen=True)
class Point:
    """A 2D point with x/y coordinates."""

    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def translate(self, dx: float, dy: float) -> "Point":
        return Point(self.x + dx, self.y + dy)

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)


@dataclass(frozen=True)
class BoundingBox:
    """Axis-aligned bounding box."""

    min_point: Point
    max_point: Point

    @property
    def width(self) -> float:
        return self.max_point.x - self.min_point.x

    @property
    def height(self) -> float:
        return self.max_point.y - self.min_point.y

    @property
    def area(self) -> float:
        return self.width * self.height

    def contains(self, point: Point) -> bool:
        return (
            self.min_point.x <= point.x <= self.max_point.x
            and self.min_point.y <= point.y <= self.max_point.y
        )

    def intersects(self, other: "BoundingBox") -> bool:
        return not (
            other.min_point.x > self.max_point.x
            or other.max_point.x < self.min_point.x
            or other.min_point.y > self.max_point.y
            or other.max_point.y < self.min_point.y
        )


# --- Shapes ---


@dataclass
class Circle:
    center: Point
    radius: float
    color: str = "black"

    def draw(self, canvas: "Canvas") -> None:
        canvas.draw_circle(self.center, self.radius, self.color)

    def bounding_box(self) -> BoundingBox:
        return BoundingBox(
            min_point=self.center.translate(-self.radius, -self.radius),
            max_point=self.center.translate(self.radius, self.radius),
        )

    @property
    def circumference(self) -> float:
        return 2 * math.pi * self.radius

    @property
    def area(self) -> float:
        return math.pi * self.radius**2


@dataclass
class Rectangle:
    origin: Point
    width: float
    height: float
    color: str = "black"

    def draw(self, canvas: "Canvas") -> None:
        canvas.draw_rect(self.origin, self.width, self.height, self.color)

    def bounding_box(self) -> BoundingBox:
        return BoundingBox(
            min_point=self.origin,
            max_point=self.origin.translate(self.width, self.height),
        )

    @property
    def area(self) -> float:
        return self.width * self.height

    @classmethod
    def from_points(cls, p1: Point, p2: Point, color: str = "black") -> "Rectangle":
        origin = Point(min(p1.x, p2.x), min(p1.y, p2.y))
        w = abs(p2.x - p1.x)
        h = abs(p2.y - p1.y)
        return cls(origin=origin, width=w, height=h, color=color)


# --- Canvas & Scene ---


@dataclass
class Canvas:
    """Simple canvas that collects draw operations."""

    width: int
    height: int
    operations: list[str] = field(default_factory=list)

    def draw_circle(self, center: Point, radius: float, color: str) -> None:
        self.operations.append(
            f"circle({center.x}, {center.y}, r={radius}, {color})"
        )

    def draw_rect(self, origin: Point, w: float, h: float, color: str) -> None:
        self.operations.append(
            f"rect({origin.x}, {origin.y}, {w}x{h}, {color})"
        )

    def clear(self) -> None:
        self.operations.clear()


def render_scene(canvas: Canvas, shapes: list[Drawable]) -> int:
    """Render all shapes onto the canvas and return the count."""
    canvas.clear()
    for shape in shapes:
        shape.draw(canvas)
    return len(canvas.operations)


# --- Demo ---

origin = Point(0.0, 0.0)
center = Point(50.0, 50.0)

circle = Circle(center=center, radius=25.0, color="red")
rect = Rectangle.from_points(origin, Point(100.0, 80.0), color="blue")

canvas = Canvas(width=200, height=200)
count = render_scene(canvas, [circle, rect])

is_inside = circle.bounding_box().contains(center)
overlaps = circle.bounding_box().intersects(rect.bounding_box())

print(f"Rendered {count} shapes")
print(f"Circle area: {circle.area:.2f}")
print(f"Center inside circle bbox: {is_inside}")
print(f"Shapes overlap: {overlaps}")
