"""
State Tests
"""

from skribble.rules.state import Corner
from skribble.rules.state import CornerList
from skribble.rules.state import State
import pytest
from decimal import *


def test_create_state():
    state = State(
        0.1,
        0.2,
        0.3,
        0.4,
        5
    )

    assert state.left == 0.1
    assert state.top == 0.2
    assert state.scale == 0.3
    assert state.rotation == 0.4
    assert state.layer == 5
    assert isinstance(state.corners, CornerList) is True


def test_create_state_with_precision():
    state = State(
        layer=1000,
        left=-87.80487804878,
        rotation=0.70816212734781,
        scale=0.50570880713635,
        top=-115.67944250871
    )

    assert state.left == Decimal(-87.80487804878)
    assert state.top == Decimal(-115.67944250871)
    assert state.scale == Decimal(0.50570880713635)
    assert state.rotation == Decimal(0.70816212734781)
    assert state.layer == Decimal(1000)


def test_create_state_with_precise_strings():
    state = State(
        layer="1000",
        left="-87.80487804878",
        rotation="0.70816212734781",
        scale="0.50570880713635",
        top="-115.67944250871"
    )

    assert state.left == Decimal("-87.80487804878")
    assert state.top == Decimal("-115.67944250871")
    assert state.scale == Decimal("0.50570880713635")
    assert state.rotation == Decimal("0.70816212734781")
    assert state.layer == Decimal("1000")


def test_corner_list_fills_correctly():
    bottom_right = Corner(4, 4)
    top_right = Corner(4, 1)
    top_left = Corner(1, 1)
    bottom_left = Corner(1, 4)

    corners = CornerList(
        bottom_right,
        top_right,
        top_left,
        bottom_left
    )

    assert corners.bottom_right == bottom_right
    assert corners.top_right == top_right
    assert corners.top_left == top_left
    assert corners.bottom_left == bottom_left


def test_throw_type_error_on_non_float_for_left():
    with pytest.raises(InvalidOperation) as info:
        def test():
            State('foobar', 0.2, 0.3, 0.4, 5)

        test()

    assert "Invalid literal for Decimal: 'foobar'" in info.value


def test_throw_type_error_on_non_float_for_top():
    with pytest.raises(InvalidOperation) as info:
        def test():
            State(0.1, 'foobar', 0.3, 0.4, 5)

        test()

    assert "Invalid literal for Decimal: 'foobar'" in info.value


def test_throw_type_error_on_non_float_for_scale():
    with pytest.raises(InvalidOperation) as info:
        def test():
            State(0.1, 0.2, 'foobar', 0.4, 5)

        test()

    assert "Invalid literal for Decimal: 'foobar'" in info.value


def test_throw_type_error_on_non_float_for_rotation():
    with pytest.raises(InvalidOperation) as info:
        def test():
            State(0.1, 0.2, 0.3, 'foobar', 5)

        test()

    assert "Invalid literal for Decimal: 'foobar'" in info.value


def test_throw_type_error_on_non_int_for_layer():
    with pytest.raises(InvalidOperation) as info:
        def test():
            State(0.1, 0.2, 0.3, 0.4, 'foobar')

        test()

    assert "Invalid literal for Decimal: 'foobar'" in info.value


def test_create_corner():
    corner = Corner(1.2, 2.3)

    assert corner.xpos == Decimal(1.2)
    assert corner.ypos == Decimal(2.3)


def test_create_corner_with_precision():
    corner = Corner(1204.70383275259996, 562.19512195122)
    assert corner.xpos == Decimal(1204.70383275259996)
    assert str(corner.xpos) == "1204.70383275259996"
    assert corner.ypos == Decimal(562.19512195122)
    assert str(corner.ypos) == "562.19512195122"


def test_create_corner_with_precision_strings():
    corner = Corner("1204.7038327526", "562.19512195122")

    assert corner.xpos == Decimal("1204.7038327526")
    assert corner.ypos == Decimal("562.19512195122")


def test_throw_type_error_on_non_float_for_xpos():
    with pytest.raises(InvalidOperation) as info:
        def test():
            Corner('foobar', 2.3)

        test()

    assert "Invalid literal for Decimal: 'foobar'" in info.value


def test_throw_type_error_on_non_float_for_ypos():
    with pytest.raises(InvalidOperation) as info:
        def test():
            Corner(1.2, 'foobar')

        test()

    assert "Invalid literal for Decimal: 'foobar'" in info.value

def test_corner_as_string():
    corner = Corner(1.2, '3.4')

    assert corner.__str__() == '{ 1.2, 3.4 }'