from apps.core.templatetags.design_tags import cover_class, spine_height


def test_cover_class_maps_to_nearest_cloth_colour():
    assert cover_class("#F4A261") == "c-ochre"
    assert cover_class("#24415E") == "c-navy"
    assert cover_class("2f5f5c") == "c-teal"


def test_cover_class_falls_back_on_bad_input():
    for bad in (None, "", "#12", "zzzzzz", 42):
        assert cover_class(bad) == "c-navy"


def test_spine_height_is_clamped_and_monotonic():
    assert spine_height(10) == 140
    assert spine_height(60) == 140
    assert spine_height(400) == 210
    assert spine_height(5000) == 210
    assert spine_height(None) == 140
    assert 140 < spine_height(152) < spine_height(300) < 210
