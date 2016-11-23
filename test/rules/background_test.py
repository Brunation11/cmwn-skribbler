"""
Background Test
"""

# import json
# import os
from skribble.rules.background import Background
import pytest


# from skribble.rules.hydrator.json import JsonHydrator
#
# dir_path = os.path.dirname(os.path.realpath(__file__))
#
# good_json = open(dir_path + "/test_skribble.json").read()
# bg_json = json.loads(good_json)
# hydrator = JsonHydrator(bg_json)
#
#
# def test_hydrate_rule_from_json():
#     bg = hydrator.get_background()
#     assert bg.asset_can_overlap is False
#     assert bg.asset_src == "https://media.changemyworldnow.com/f/73531401005"
#     assert bg.asset_name == "bkg_fun_10.png"
#     assert bg.asset_hash_type == "sha1"
#     assert bg.asset_hash == "c1a7fece0c8ab3733b2a546514fbd37b6c433506"
#     assert bg.asset_mime_type == "image/png"
#     assert bg.asset_id == "73531401005"
#     assert bg.asset_type == Background.BACKGROUND

def test_sets_properties_correctly():
    bg = Background(
        asset_src="https://media.changemyworldnow.com/f/73531401005",
        asset_name="bkg_fun_10.png",
        asset_id="73531401005",
        asset_mime_type="image/png",
        asset_can_overlap=False,
        asset_hash="c1a7fece0c8ab3733b2a546514fbd37b6c433506",
        asset_hash_type="sha1",
        asset_type='background'
    )

    assert bg.asset_src == "https://media.changemyworldnow.com/f/73531401005"
    assert bg.asset_name == "bkg_fun_10.png"
    assert bg.asset_mime_type == "image/png"
    assert bg.asset_id == "73531401005"
    assert bg.asset_can_overlap is False
    assert bg.asset_hash == "c1a7fece0c8ab3733b2a546514fbd37b6c433506"
    assert bg.asset_hash_type == "sha1"
    assert bg.asset_type == Background.BACKGROUND


def test_throws_exception_on_bad_hash():
    with pytest.raises(Exception) as info:
        def test():
            Background(asset_hash_type='foo')
        test()

    assert 'Invalid hash type: foo' in info.value


def test_throws_exception_on_invalid_type():
    with pytest.raises(Exception) as info:
        def test():
            Background(asset_type='foo')
        test()

    assert 'Invalid background asset type passed' in info.value


def test_throws_exception_on_item_type():
    with pytest.raises(Exception) as info:
        def test():
            Background(asset_type=Background.ITEM)
        test()

    assert 'Invalid background asset type passed' in info.value


def test_throws_exception_on_background_type():
    with pytest.raises(Exception) as info:
        def test():
            Background(asset_type=Background.MESSAGE)
        test()

    assert 'Invalid background asset type passed' in info.value
