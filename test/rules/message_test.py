"""
Item Test
"""

from skribble.rules.message import Message
import pytest


def test_sets_properties_correctly():
    item = Message(
        asset_src="https://media.changemyworldnow.com/f/73531437917",
        asset_name="img_sparkles_14.png",
        asset_id="73531437917",
        asset_mime_type="image/png",
        asset_can_overlap=False,
        asset_hash="288fca07f5daccf68f9bf599d45588141a09d414",
        asset_hash_type="sha1",
        asset_type='message'
    )

    assert item.asset_src == "https://media.changemyworldnow.com/f/73531437917"
    assert item.asset_name == "img_sparkles_14.png"
    assert item.asset_mime_type == "image/png"
    assert item.asset_id == "73531437917"
    assert item.asset_can_overlap is False
    assert item.asset_hash == "288fca07f5daccf68f9bf599d45588141a09d414"
    assert item.asset_hash_type == "sha1"
    assert item.asset_type == Message.MESSAGE


def test_throws_exception_on_bad_hash():
    with pytest.raises(Exception) as info:
        def test():
            Message(asset_hash_type='foo')
        test()

    assert 'Invalid hash type: foo' in info.value


def test_throws_exception_on_invalid_type():
    with pytest.raises(Exception) as info:
        def test():
            Message(asset_type='foo')
        test()

    assert 'Invalid message asset type passed' in info.value


def test_throws_exception_on_item_type():
    with pytest.raises(Exception) as info:
        def test():
            Message(asset_type=Message.ITEM)
        test()

    assert 'Invalid message asset type passed' in info.value


def test_throws_exception_on_background_type():
    with pytest.raises(Exception) as info:
        def test():
            Message(asset_type=Message.BACKGROUND)
        test()

    assert 'Invalid message asset type passed' in info.value
