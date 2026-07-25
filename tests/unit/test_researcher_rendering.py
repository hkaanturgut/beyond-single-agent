"""Unit tests — researcher list rendering (handles web-search structured items)."""

from __future__ import annotations

from trip_planner.agents.researcher import _item_to_str, _to_list


class TestItemToStr:
    def test_plain_string_passthrough(self):
        assert _item_to_str("Fushimi Inari Taisha") == "Fushimi Inari Taisha"

    def test_dict_name_and_date_note(self):
        item = {"name": "Jidai Matsuri", "date_note": "October 22"}
        assert _item_to_str(item) == "Jidai Matsuri — October 22"

    def test_dict_name_only(self):
        assert _item_to_str({"name": "Gion district"}) == "Gion district"

    def test_dict_title_and_description_fallbacks(self):
        item = {"title": "Autumn illuminations", "description": "late October"}
        assert _item_to_str(item) == "Autumn illuminations — late October"

    def test_dict_without_known_keys_is_readable(self):
        # No name/title — should not leak a raw Python dict repr.
        out = _item_to_str({"foo": "bar", "baz": "qux"})
        assert out.startswith("foo: bar")
        assert "{" not in out


class TestToList:
    def test_mixed_list_of_strings_and_dicts(self):
        value = [
            "Kiyomizu-dera",
            {"name": "Kurama Fire Festival", "date_note": "October 22 evening"},
        ]
        assert _to_list(value) == [
            "Kiyomizu-dera",
            "Kurama Fire Festival — October 22 evening",
        ]

    def test_scalar_string(self):
        assert _to_list("just one") == ["just one"]

    def test_none_returns_empty(self):
        assert _to_list(None) == []
