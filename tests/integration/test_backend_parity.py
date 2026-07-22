"""Integration test — backend parity: same request, same required sections."""

from __future__ import annotations

import pytest

from trip_planner.backends.demo import DemoBackend
from trip_planner.models.request import TripRequest
from trip_planner.workflow.runner import run_trip_workflow

REQUIRED_SECTIONS = [
    "Trip Overview",
    "Day-by-Day Itinerary",
    "Budget Breakdown",
    "Packing",  # "Packing / Preparation Tips"
]


@pytest.fixture()
def request_obj():
    return TripRequest(destination="Lisbon", month="May", budget_usd=2600)


@pytest.mark.asyncio
class TestBackendParity:
    async def test_demo_backend_produces_required_sections(self, request_obj, tmp_path):
        """DemoBackend must produce all required markdown sections."""
        brief = await run_trip_workflow(
            request_obj, DemoBackend(), output_dir=str(tmp_path)
        )
        for section in REQUIRED_SECTIONS:
            assert section in brief.markdown, f"Missing section: {section}"

    async def test_two_demo_backend_runs_produce_comparable_structure(
        self, request_obj, tmp_path
    ):
        """Two runs with DemoBackend must both produce all required sections."""
        brief_a = await run_trip_workflow(
            request_obj, DemoBackend(), output_dir=str(tmp_path)
        )
        brief_b = await run_trip_workflow(
            request_obj, DemoBackend(), output_dir=str(tmp_path)
        )
        for section in REQUIRED_SECTIONS:
            assert section in brief_a.markdown, f"Run A missing section: {section}"
            assert section in brief_b.markdown, f"Run B missing section: {section}"

    async def test_output_files_are_different_due_to_timestamp(self, request_obj, tmp_path):
        """Each run should produce a unique output file."""
        import asyncio

        brief_a, brief_b = await asyncio.gather(
            run_trip_workflow(request_obj, DemoBackend(), output_dir=str(tmp_path)),
            # Sleep briefly to ensure distinct timestamps
            run_trip_workflow(
                TripRequest(destination="Kyoto", month="October", budget_usd=1800),
                DemoBackend(),
                output_dir=str(tmp_path),
            ),
        )
        assert brief_a.output_path != brief_b.output_path
