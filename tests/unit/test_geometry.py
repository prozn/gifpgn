import pytest

from gifpgn._types import Coord
from gifpgn.geometry import (
    rotate_around_point,
    angle_between_two_points,
    shorten_line,
    line_intersection
)

from math import pi


def test_rotate_around_point():
    assert rotate_around_point(Coord(10, 10), pi, Coord(10, 20)) == Coord(10, 30)
    assert rotate_around_point(Coord(10, 10), pi*1.5, Coord(10, 20)) == Coord(20, 20)
    assert rotate_around_point(Coord(10, 10), pi*1.5, Coord(10, 10)) == Coord(10, 10)
    assert rotate_around_point(Coord(10, 10), pi/2, Coord(10, 20)) == Coord(0, 20)
    assert rotate_around_point(Coord(10, 10), pi*2, Coord(10, 20)) == Coord(10, 10)

def test_angle_between_two_points():
    assert angle_between_two_points(Coord(10, 10), Coord(10, 20)) == pytest.approx(-pi/2, abs=1e-14)
    assert angle_between_two_points(Coord(10, 10), Coord(20, 10)) == pytest.approx(0, abs=1e-14)
    assert angle_between_two_points(Coord(10, 10), Coord(0, 10)) == pytest.approx(-pi, abs=1e-14)
    assert angle_between_two_points(Coord(10, 10), Coord(10, 0)) == pytest.approx(pi/2, abs=1e-14)
    assert angle_between_two_points(Coord(0, 0), Coord(30, 30)) == pytest.approx(-pi/4, abs=1e-14)
    assert angle_between_two_points(Coord(0, 0), Coord(10, 10)) == \
        pytest.approx(angle_between_two_points(Coord(0, 0), Coord(30, 30)), abs=1e-14)
    assert angle_between_two_points(Coord(10, 10), Coord(10, 10)) == pytest.approx(0, abs=1e-14)

def test_shorten_line():
    assert shorten_line(Coord(10, 10), Coord(10, 20), 5) == (Coord(10, 10), Coord(10, 15))
    assert shorten_line(Coord(10, 10), Coord(10, 20), 10) == (Coord(10, 10), Coord(10, 10))
    assert shorten_line(Coord(10, 10), Coord(10, 20), 0) == (Coord(10, 10), Coord(10, 20))
    assert shorten_line(Coord(10, 10), Coord(10, 20), 15) == (Coord(10, 10), Coord(10, 5))
    assert shorten_line(Coord(10, 10), Coord(30, 30), 10) == (Coord(10, 10), Coord(22, 22))
    assert shorten_line(Coord(40, 40), Coord(20, 40), 10) == (Coord(40, 40), Coord(30, 40))

def test_line_intersection():
    assert line_intersection((Coord(10, 10), Coord(40, 10)), (Coord(20, 0), Coord(20, 20))) == Coord(20, 10)
    assert line_intersection((Coord(0, 10), Coord(100, 10)), (Coord(0, 20), Coord(100, 0))) == Coord(50, 10)
    assert line_intersection((Coord(0, 40), Coord(480, 40)), (Coord(20, 80), Coord(30, 40))) == Coord(30, 40)
    assert line_intersection((Coord(0, 40), Coord(480, 40)), (Coord(0, 45), Coord(480, 45))) is None