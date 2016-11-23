"""
Asset State
"""

from skribble import set_precision


class State(object):
    """
    Asset State

    This defines the scale, rotation, and layer of the asset on the canvas

    To match what is in HTML:
       - the top and left points will be coordinates {0, 0}
       - Rotation is measured in radians
       - Layer states how the assets SHOULD be ordered from front to back
    """
    __slots__ = ('_left', '_top', '_scale', '_rotation', '_layer', '_corners')

    def __new__(cls, left=None, top=None, scale=None, rotation=None, layer=None, corners=None):
        self = object.__new__(cls)

        if corners is None:
            corners = CornerList(
                Corner(0.0, 0.0),
                Corner(0.0, 0.0),
                Corner(0.0, 0.0),
                Corner(0.0, 0.0)
            )

        self._left = set_precision(left)
        self._top = set_precision(top)
        self._scale = set_precision(scale)
        self._rotation = set_precision(rotation)
        self._layer = set_precision(layer)
        self._corners = corners
        return self

    @property
    def left(self):
        return self._left

    @property
    def top(self):
        return self._top

    @property
    def scale(self):
        return self._scale

    @property
    def rotation(self):
        return self._rotation

    @property
    def layer(self):
        return self._layer

    @property
    def corners(self):
        return self._corners


class CornerList(object):
    """
    List of the 4 corners

    It is a bit counter-intuitive but the points on the shape start at the bottom
    right and go counter clockwise around the square.
    Here is an Example of what the points would be:

    Square/Rectangle:   Rhombus / Rotated:

    A ---------- B              A
    |            |             / \
    |            |            /   \
    |            |           /     \
    |            |          C       B
    |            |           \     /
    |            |            \   /
    |            |             \ /
    C ---------- D              D

    A = top_left
    B = top_right
    C = bottom_left
    D = bottom_right

    The point order will always be D -> B -> A -> C
    or
    bottom_right -> top_right -> top_left -> bottom_left

    The corner points are used to detect collision for shapes following the separating axis theorem:
    https://gamedevelopment.tutsplus.com/tutorials/collision-detection-using-the-separating-axis-theorem--gamedev-169
    """
    __slots__ = ('_bottom_right', '_top_right', '_top_left', '_bottom_left')

    def __new__(cls, bottom_right, top_right, top_left, bottom_left):
        self = object.__new__(cls)

        self._bottom_right = bottom_right
        self._top_right = top_right
        self._top_left = top_left
        self._bottom_left = bottom_left
        return self

    @property
    def top_right(self):
        return self._top_right

    @property
    def bottom_right(self):
        return self._bottom_right

    @property
    def bottom_left(self):
        return self._bottom_left

    @property
    def top_let(self):
        return self._top_left


class Corner(object):
    """
    Corner AKA Point
    """
    __slots__ = ('_xpos', '_ypos')

    def __str__(self):
        return "{ %s, %s }" % (self._xpos.__str__(), self._ypos.__str__())

    def __new__(cls, xpos, ypos):
        """
        Creates a new immutable corner point

        :param xpos:
        :param ypos:
        :return:
        """
        self = object.__new__(cls)
        self._xpos = set_precision(xpos)
        self._ypos = set_precision(ypos)

        return self

    @property
    def xpos(self):
        return self._xpos

    @property
    def ypos(self):
        return self._ypos


__all__ = ['State', 'Corner', 'CornerList']
