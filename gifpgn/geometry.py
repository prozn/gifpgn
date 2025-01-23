from typing import Tuple, Optional
from math import cos, sin, atan2, sqrt

from ._types import Coord

def rotate_around_point(point: Coord, radians: float, origin: Coord=(0, 0)) -> Coord:
    x, y = point
    ox, oy = origin
    qx = ox + cos(radians) * (x - ox) + sin(radians) * (y - oy)
    qy = oy + -sin(radians) * (x - ox) + cos(radians) * (y - oy)
    return qx, qy

def angle_between_two_points(point1: Coord, point2: Coord) -> float:
    x0, y0 = point1
    x1, y1 = point2
    return -atan2(y1-y0, x1-x0)

def shorten_line(c1: Coord, c2: Coord, pix: int) -> Tuple[Coord,Coord]:
    dx = c2[0] - c1[0]
    dy = c2[1] - c1[1]
    l = sqrt(dx*dx+dy*dy)
    if l > 0:
        dx /= l
        dy /= l
    dx *= l-pix
    dy *= l-pix
    return (c1,(c1[0]+dx, c1[1]+dy))

def line_intersection(line1: Tuple[Coord, Coord], line2: Tuple[Coord, Coord]) -> Optional[Coord]:
    """Returns the intersection point of two lines, or None if no intersection

    Args:
        line1 (tuple): Line 1 defined by a tuple containing two x,y tuples
        line2 (tuple): Line 2 defined by a tuple containing two x,y tuples

    Returns:
        tuple: A tuple contianing the x,y coordinates, or None if no intersection
    """
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)

    if div == 0: # no intersection
        return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y