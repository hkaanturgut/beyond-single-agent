"""Unit tests — request parser and TripRequest validation."""

from __future__ import annotations

import pytest
from datetime import datetime

from trip_planner.models.request import TripRequest, parse_trip_request


class TestParseRequest:
    """parse_trip_request happy-path tests."""

    def test_standard_format(self):
        req = parse_trip_request(
            "Plan my 3-day trip to Kyoto in October with budget $1800"
        )
        assert req.destination == "Kyoto"
        assert req.month == "October"
        assert req.budget_usd == 1800.0

    def test_case_insensitive(self):
        req = parse_trip_request(
            "PLAN MY 3-DAY TRIP TO LISBON IN MAY WITH BUDGET $2600"
        )
        assert req.destination == "Lisbon"
        assert req.month == "May"
        assert req.budget_usd == 2600.0

    def test_budget_with_comma(self):
        req = parse_trip_request(
            "Plan my 3-day trip to Paris in June with budget $1,500"
        )
        assert req.budget_usd == 1500.0

    def test_budget_without_dollar_sign(self):
        req = parse_trip_request(
            "Plan my 3-day trip to Barcelona in July with budget 900"
        )
        assert req.budget_usd == 900.0

    def test_multi_word_destination(self):
        req = parse_trip_request(
            "Plan my 3-day trip to New York in December with budget $3000"
        )
        assert req.destination == "New York"

    def test_without_day_count(self):
        req = parse_trip_request(
            "Plan my trip to Tokyo in March with budget $2200"
        )
        assert req.destination == "Tokyo"
        assert req.month == "March"

    def test_safe_destination_slug(self):
        req = parse_trip_request(
            "Plan my 3-day trip to São Paulo in April with budget $1200"
        )
        assert "/" not in req.safe_destination
        assert " " not in req.safe_destination


class TestParseRequestErrors:
    """parse_trip_request error handling."""

    def test_missing_budget_raises(self):
        with pytest.raises(ValueError, match="Could not parse"):
            parse_trip_request("Plan my trip to Lisbon")

    def test_empty_prompt_raises(self):
        with pytest.raises(ValueError):
            parse_trip_request("")

    def test_wrong_format_raises(self):
        with pytest.raises(ValueError):
            parse_trip_request("Take me to the moon")


class TestTripRequestValidation:
    """TripRequest Pydantic model validation."""

    def test_valid_request(self):
        req = TripRequest(destination="Kyoto", month="October", budget_usd=1800)
        assert req.destination == "Kyoto"

    def test_empty_destination_raises(self):
        with pytest.raises(Exception):
            TripRequest(destination="", month="October", budget_usd=1800)

    def test_invalid_month_raises(self):
        with pytest.raises(Exception):
            TripRequest(destination="Kyoto", month="Octember", budget_usd=1800)

    def test_zero_budget_raises(self):
        with pytest.raises(Exception):
            TripRequest(destination="Kyoto", month="October", budget_usd=0)

    def test_negative_budget_raises(self):
        with pytest.raises(Exception):
            TripRequest(destination="Kyoto", month="October", budget_usd=-100)

    def test_all_months_accepted(self):
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        for month in months:
            req = TripRequest(destination="Lisbon", month=month, budget_usd=1000)
            assert req.month == month
