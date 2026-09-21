"""Pure business-logic tests: priority matrix, SLA clocks, state machine. No database required."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

import pytest

from nyra_api.services import priority as prio
from nyra_api.services import sla as sla_svc
from nyra_api.services import state_machine as sm


class TestPriorityMatrix:
    def test_high_impact_high_urgency_is_p1(self):
        assert prio.calculate(1, 1) == 1

    def test_low_impact_low_urgency_is_p5(self):
        assert prio.calculate(3, 3) == 5

    def test_monotonic_in_urgency(self):
        for impact in (1, 2, 3):
            assert prio.calculate(impact, 1) <= prio.calculate(impact, 2) <= prio.calculate(impact, 3)

    def test_monotonic_in_impact(self):
        for urgency in (1, 2, 3):
            assert prio.calculate(1, urgency) <= prio.calculate(2, urgency) <= prio.calculate(3, urgency)

    def test_full_matrix_is_defined(self):
        assert len(prio.matrix_as_table()) == 9

    @pytest.mark.parametrize("impact,urgency", [(0, 1), (4, 1), (1, 0), (1, 4)])
    def test_invalid_inputs_rejected(self, impact, urgency):
        with pytest.raises(ValueError):
            prio.calculate(impact, urgency)

    def test_labels_present(self):
        assert prio.label(1).startswith("P1")
        assert prio.label(5).startswith("P5")


class TestSlaClocks:
    CAL = {
        "id": 1,
        "work_days": [1, 2, 3, 4, 5],
        "work_start": time(9, 0),
        "work_end": time(18, 0),
        "holidays": [],
    }

    def test_within_business_hours(self):
        start = datetime(2026, 9, 21, 10, 0, tzinfo=timezone.utc)  # Monday
        assert sla_svc.add_business_minutes(start, 60, self.CAL) == datetime(2026, 9, 21, 11, 0, tzinfo=timezone.utc)

    def test_rolls_over_to_next_business_day(self):
        start = datetime(2026, 9, 21, 17, 30, tzinfo=timezone.utc)  # Monday 17:30
        end = sla_svc.add_business_minutes(start, 60, self.CAL)
        assert end.date() == datetime(2026, 9, 22).date()
        assert end.hour == 9 and end.minute == 30

    def test_skips_weekend(self):
        friday = datetime(2026, 9, 25, 17, 0, tzinfo=timezone.utc)
        end = sla_svc.add_business_minutes(friday, 120, self.CAL)
        assert end.weekday() == 0  # Monday
        assert end.hour == 10

    def test_skips_holiday(self):
        cal = dict(self.CAL, holidays=["2026-09-22"])
        start = datetime(2026, 9, 21, 17, 30, tzinfo=timezone.utc)
        end = sla_svc.add_business_minutes(start, 60, cal)
        assert end.date() == datetime(2026, 9, 23).date()

    def test_no_calendar_is_plain_addition(self):
        start = datetime(2026, 9, 21, 10, 0, tzinfo=timezone.utc)
        assert sla_svc.add_business_minutes(start, 90, None) == start + timedelta(minutes=90)

    def test_start_before_shift_snaps_to_shift_start(self):
        start = datetime(2026, 9, 21, 6, 0, tzinfo=timezone.utc)
        end = sla_svc.add_business_minutes(start, 30, self.CAL)
        assert (end.hour, end.minute) == (9, 30)

    def test_evaluate_flags_breach(self):
        now = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)
        record = {"opened_at": now - timedelta(hours=5), "resolve_due_at": now - timedelta(hours=1)}
        state = sla_svc.evaluate(record, now)
        assert state["sla_state"] == "breached"
        assert state["sla_percent"] == 100.0

    def test_evaluate_flags_at_risk(self):
        now = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)
        record = {"opened_at": now - timedelta(hours=4), "resolve_due_at": now + timedelta(minutes=30)}
        assert sla_svc.evaluate(record, now)["sla_state"] == "at_risk"

    def test_evaluate_without_target_is_ok(self):
        assert sla_svc.evaluate({"opened_at": datetime.now(timezone.utc), "resolve_due_at": None})["sla_state"] == "ok"


class TestStateMachine:
    def test_legal_forward_path(self):
        assert sm.allowed("new") == ["in_progress", "on_hold", "cancelled"]

    def test_illegal_transition_rejected(self):
        with pytest.raises(sm.TransitionError):
            sm.validate({"state": "new"}, "closed", {})

    def test_resolve_requires_resolution_notes(self):
        with pytest.raises(sm.TransitionError) as err:
            sm.validate({"state": "in_progress"}, "resolved", {})
        assert "resolution_notes" in err.value.missing

    def test_resolve_with_notes_passes(self):
        sm.validate({"state": "in_progress"}, "resolved", {"resolution_notes": "Fixed by patching the client."})

    def test_on_hold_requires_reason(self):
        with pytest.raises(sm.TransitionError) as err:
            sm.validate({"state": "in_progress"}, "on_hold", {})
        assert "on_hold_reason" in err.value.missing

    def test_on_hold_with_reason_passes(self):
        sm.validate({"state": "in_progress"}, "on_hold", {"on_hold_reason": "awaiting_vendor"})

    def test_reopen_from_closed_allowed(self):
        sm.validate({"state": "closed"}, "in_progress", {})

    def test_cancelled_is_terminal(self):
        assert sm.allowed("cancelled") == []
