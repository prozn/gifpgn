from typing import Tuple, Optional
from math import cos, sin, atan2, sqrt

from ._types import Coord


def rotate_around_point(point: Coord, radians: float, origin: Coord) -> Coord:
    """Rotates point around origin by radians

    :param Coord point:
    :param float radians:
    :param Coord origin: defaults to (0, 0)
    :return Coord:
    """
    x, y = point
    ox, oy = origin
    qx = int(ox + cos(radians) * (x - ox) + sin(radians) * (y - oy))
    qy = int(oy + -sin(radians) * (x - ox) + cos(radians) * (y - oy))
    return Coord(qx, qy)


def angle_between_two_points(point1: Coord, point2: Coord) -> float:
    """Returns the angle of a line between two points in radians

    :param Coord point1:
    :param Coord point2:
    :return float:
    """
    x0, y0 = point1
    x1, y1 = point2
    return -atan2(y1-y0, x1-x0)


def shorten_line(c1: Coord, c2: Coord, pix: int) -> Tuple[Coord, Coord]:
    """Shortens a line between two points by set number of pixels from the second point

    :param Coord c1:
    :param Coord c2:
    :param int pix:
    :return Tuple[Coord,Coord]:
    """
    dx: float = c2[0] - c1[0]
    dy: float = c2[1] - c1[1]
    length = sqrt(dx*dx+dy*dy)
    if length > 0:
        dx /= length
        dy /= length
    dx *= length-pix
    dy *= length-pix
    return (c1, Coord(int(c1[0]+dx), int(c1[1]+dy)))


def line_intersection(line1: Tuple[Coord, Coord], line2: Tuple[Coord, Coord]) -> Optional[Coord]:
    """Returns the intersection point of two line, or None if no intersection

    :param Tuple[Coord, Coord] line1:
    :param Tuple[Coord, Coord] line2:
    :return Optional[Coord]:
    """
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)

    if div == 0:  # no intersection
        return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return Coord(x, y)
