# Copyright 2026 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Spinner tests."""

from collections.abc import Generator
from unittest.mock import Mock

import pytest

from colours.main import _CUSTOM_SPINNERS, SPINNER_NAMES, SPINNERS, Spinner, _make_spinner  # noqa: PLC2701


@pytest.fixture(autouse=True)
def reset_spinner() -> Generator[None, None, None]:
    """Ensure spinner singleton state does not leak between tests."""
    Spinner._live = None
    Spinner._spinner = None
    Spinner._depth = 0
    yield
    Spinner._live = None
    Spinner._spinner = None
    Spinner._depth = 0


class TestSpinner:
    """Test spinner singleton behavior."""

    @staticmethod
    def test_start_reuses_active_spinner_and_updates_text() -> None:
        """Start should reuse existing spinner and update its text."""
        Spinner.start("Task A", name="dots")
        live = Spinner._live
        Spinner.start("Task B")
        assert Spinner._live is live
        assert Spinner._spinner is not None
        assert str(Spinner._spinner.text) == "Task B"
        Spinner.terminate()

    @staticmethod
    def test_start_random_name() -> None:
        """Start without explicit name picks a valid spinner from the pool."""
        Spinner.start("loading")
        assert Spinner._spinner is not None
        assert Spinner._spinner.name in SPINNER_NAMES
        Spinner.terminate()

    @staticmethod
    def test_stop_behaviour() -> None:
        """Stop is a no-op when inactive (depth stays 0); cleans up even on error."""
        Spinner.stop()
        Spinner.stop()
        assert Spinner._depth == 0

        # Cleanup even when Live.stop() raises
        live = Mock()
        live.stop.side_effect = RuntimeError("console closed")
        Spinner._live = live
        Spinner._spinner = Mock()
        Spinner._depth = 1
        with pytest.raises(RuntimeError, match="console closed"):
            Spinner.stop()
        assert Spinner._live is None
        assert Spinner._spinner is None

    @staticmethod
    def test_context_manager() -> None:
        """Context manager forwards args, binds class via `as`, and stops on error."""
        with Spinner("msg", name="dots") as s:
            assert s is Spinner
            assert Spinner._spinner is not None
            assert str(Spinner._spinner.text) == "msg"
        assert Spinner._live is None

        # Bare context
        with Spinner as s:
            assert s is Spinner
            assert Spinner._live is not None
        assert Spinner._live is None

        # Stops on exception
        msg = "expected match"
        with pytest.raises(ValueError, match=msg), Spinner("working", name="dots"):
            raise ValueError(msg)
        assert Spinner._live is None

    @staticmethod
    def test_nested_context_does_not_stop_outer_spinner() -> None:
        """Inner context must not tear down a spinner started by an outer one."""
        Spinner.start("outer", name="dots")
        live = Spinner._live
        with Spinner("inner"):
            assert Spinner._depth == 2
            assert Spinner._live is live
        assert Spinner._depth == 1
        assert Spinner._live is live
        Spinner.stop()
        assert Spinner._live is None

    @staticmethod
    def test_terminate_bypasses_nesting() -> None:
        """Terminate tears down the spinner regardless of nesting depth."""
        Spinner.start("outer", name="dots")
        Spinner.start("inner")
        assert Spinner._depth == 2
        Spinner.terminate()
        assert Spinner._depth == 0
        assert Spinner._live is None

    @staticmethod
    def test_smoke_start_text_stop() -> None:
        """Integration: start, update text, stop without mocks."""
        Spinner.start("smoke test", name="dots")
        assert Spinner._spinner is not None
        assert str(Spinner._spinner.text) == "smoke test"
        Spinner.text("updated")
        assert str(Spinner._spinner.text) == "updated"
        Spinner.stop()
        assert Spinner._live is None

    @staticmethod
    def test_make_spinner_uses_custom_frames() -> None:
        """Custom spinners are built from the private registry, not Rich globals."""
        spinner = _make_spinner("xanaduai", "hi", style=None, speed=1.0)
        assert spinner.name == "xanaduai"
        assert spinner.frames == _CUSTOM_SPINNERS["xanaduai"]["frames"]
        assert spinner.interval == _CUSTOM_SPINNERS["xanaduai"]["interval"]

    @staticmethod
    def test_call_returns_context_manager() -> None:
        """Spinner() returns a per-call context object, not the class itself."""
        ctx = Spinner("x")
        assert ctx is not Spinner
        # The context object enters/exits correctly.
        with Spinner("msg", name="dots") as s:
            assert s is Spinner
            assert Spinner._live is not None
        assert Spinner._live is None

    @staticmethod
    def test_stale_pending_does_not_leak() -> None:
        """Calling Spinner(...) without entering a with block must not affect later bare contexts."""
        Spinner("orphaned message", name="dots")
        with Spinner:
            # Bare context must not pick up the orphaned args.
            assert Spinner._spinner is not None
            assert not str(Spinner._spinner.text)

    @staticmethod
    @pytest.mark.parametrize("speed", [0, -1, -0.001])
    def test_make_spinner_rejects_non_positive_speed(speed: float) -> None:
        """_make_spinner raises ValueError for zero or negative speed."""
        with pytest.raises(ValueError, match="speed must be positive"):
            _make_spinner("dots", "hi", style=None, speed=speed)

    @staticmethod
    def test_start_rollback_on_failure() -> None:
        """start() rolls back _depth and clears state if _make_spinner raises."""
        with pytest.raises(ValueError, match="speed must be positive"):
            Spinner.start("fail", name="dots", speed=0)
        assert Spinner._depth == 0
        assert Spinner._live is None
        assert Spinner._spinner is None


class TestSpinnerRegistration:
    """Test custom spinner registration and filtering."""

    @staticmethod
    def test_spinner_names_and_rich_isolation() -> None:
        """Custom spinners in SPINNER_NAMES; toggles removed; Rich globals untouched."""
        assert "xanaduai" in SPINNER_NAMES
        assert "xanaduai_ticker" in SPINNER_NAMES
        assert all("toggle" not in name for name in SPINNER_NAMES)
        # Rich's global registry is not mutated
        assert "xanaduai" not in SPINNERS
        assert "xanaduai_ticker" not in SPINNERS
        assert any("toggle" in name for name in SPINNERS)
