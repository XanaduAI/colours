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
from unittest.mock import Mock, patch

import pytest
from rich.spinner import Spinner as RichSpinner

from colours.main import _CUSTOM_SPINNERS, SPINNER_NAMES, SPINNERS, Spinner  # noqa: PLC2701


@pytest.fixture(autouse=True)
def reset_spinner() -> Generator[None, None, None]:
    """Ensure spinner singleton state does not leak between tests."""
    Spinner._live = None
    Spinner._spinner = None
    Spinner._depth = 0
    Spinner._pending = None
    yield
    Spinner._live = None
    Spinner._spinner = None
    Spinner._depth = 0
    Spinner._pending = None


class TestSpinner:
    """Test spinner singleton behavior."""

    @staticmethod
    def test_start_does_not_create_new_spinner_if_already_active() -> None:
        """Start should not create a second spinner when one is already active."""
        active_live = Mock()
        Spinner._live = active_live

        with patch("colours.main.rich_Spinner") as spinner_cls, patch("colours.main.Live") as live_cls:
            Spinner.start("working")

        spinner_cls.assert_not_called()
        live_cls.assert_not_called()
        assert Spinner._live is active_live

    @staticmethod
    def test_start_updates_text_if_already_active() -> None:
        """Start should update text when called again with a new message."""
        renderable = RichSpinner("dots", "Task A")
        live = Mock()
        Spinner._live = live
        Spinner._spinner = renderable

        with patch("colours.main.rich_Spinner") as spinner_cls, patch("colours.main.Live") as live_cls:
            Spinner.start("Task B")

        spinner_cls.assert_not_called()
        live_cls.assert_not_called()
        assert Spinner.text == "Task B"

    @staticmethod
    def test_start_creates_spinner_and_live() -> None:
        """Start should construct and start a new Rich Live spinner."""
        live = Mock()
        spinner = Mock()

        with (
            patch("colours.main.choice", return_value="dots") as choice_func,
            patch("colours.main._make_spinner", return_value=spinner) as make_spinner,
            patch("colours.main.Live", return_value=live) as live_cls,
        ):
            Spinner.start("loading", style="green", speed=2.0)

        choice_func.assert_called_once()
        spinner_names = choice_func.call_args.args[0]
        assert "xanaduai" in spinner_names
        assert all("toggle" not in name for name in spinner_names)
        make_spinner.assert_called_once_with("dots", "loading", style="green", speed=2.0)
        live_cls.assert_called_once_with(spinner, refresh_per_second=20)
        live.start.assert_called_once_with()
        assert Spinner._live is live

    @staticmethod
    def test_stop_stops_and_clears_live() -> None:
        """Stop should stop the live instance and clear singleton state."""
        live = Mock()
        Spinner._live = live

        Spinner.stop()

        live.stop.assert_called_once_with()
        assert Spinner._live is None

    @staticmethod
    def test_text_property_getter_and_setter() -> None:
        """The text property should proxy to the underlying Rich spinner."""
        renderable = RichSpinner("dots", "hello")
        live = Mock()
        Spinner._live = live
        Spinner._spinner = renderable

        assert Spinner.text == "hello"
        Spinner.text = "updated"
        assert Spinner.text == "updated"

    @staticmethod
    def test_text_returns_empty_if_spinner_inactive() -> None:
        """The text property should be an empty string when no spinner is active."""
        assert not Spinner.text

    @staticmethod
    def test_context_manager_starts_and_stops() -> None:
        """Using Spinner as a context manager should call start then stop."""
        with patch.object(Spinner, "start") as start, patch.object(Spinner, "stop") as stop, Spinner:
            pass

        start.assert_called_once_with()
        stop.assert_called_once_with()

    @staticmethod
    def test_context_manager_with_message_starts_and_stops() -> None:
        """Using Spinner(message, ...) should pass args through to start."""
        with (
            patch.object(Spinner, "start") as start,
            patch.object(Spinner, "stop") as stop,
            Spinner("Initial message...", name="dots", style="green", speed=1.5),
        ):
            pass

        start.assert_called_once_with(message="Initial message...", name="dots", style="green", speed=1.5)
        stop.assert_called_once_with()

    @staticmethod
    def test_stop_noop_when_inactive() -> None:
        """Stop should not raise when no spinner is active."""
        Spinner.stop()  # should not raise
        assert Spinner._live is None

    @staticmethod
    def test_stop_clears_live_even_if_stop_raises() -> None:
        """Stop should clear _live and _spinner even if Live.stop() raises."""
        live = Mock()
        live.stop.side_effect = RuntimeError("console closed")
        Spinner._live = live
        Spinner._spinner = Mock()

        with pytest.raises(RuntimeError, match="console closed"):
            Spinner.stop()

        assert Spinner._live is None
        assert Spinner._spinner is None

    @staticmethod
    def test_start_with_explicit_name() -> None:
        """Start should use the provided name instead of random choice."""
        live = Mock()
        spinner = Mock()

        with (
            patch("colours.main.choice") as choice_func,
            patch("colours.main.rich_Spinner", return_value=spinner) as spinner_cls,
            patch("colours.main.Live", return_value=live),
        ):
            Spinner.start("loading", name="dots", style="green", speed=2.0)

        choice_func.assert_not_called()
        spinner_cls.assert_called_once_with("dots", "loading", style="green", speed=2.0)

    @staticmethod
    def test_context_manager_stops_on_exception() -> None:
        """Spinner should stop even if an exception occurs inside the context."""
        msg = "expected"
        with (
            patch.object(Spinner, "start"),
            patch.object(Spinner, "stop") as stop,
            pytest.raises(ValueError, match=msg),
            Spinner("working"),
        ):
            raise ValueError(msg)
        stop.assert_called_once_with()

    @staticmethod
    def test_smoke_start_stop() -> None:
        """Integration test: actually start and stop a spinner without mocks."""
        Spinner.start("smoke test", name="dots")
        assert Spinner._live is not None
        assert Spinner.text == "smoke test"
        Spinner.stop()
        assert Spinner._live is None

    @staticmethod
    def test_context_manager_binds_class_via_as() -> None:
        """`with Spinner(...) as s` should bind the Spinner class, not None."""
        with patch.object(Spinner, "start"), patch.object(Spinner, "stop"), Spinner("msg") as s:
            assert s is Spinner

    @staticmethod
    def test_bare_context_manager_binds_class_via_as() -> None:
        """`with Spinner as s` should bind the Spinner class, not None."""
        with patch.object(Spinner, "start"), patch.object(Spinner, "stop"), Spinner as s:
            assert s is Spinner

    @staticmethod
    def test_nested_context_does_not_stop_outer_spinner() -> None:
        """An inner context must not tear down a spinner started by an outer one."""
        live = Mock()
        with patch("colours.main._make_spinner", return_value=Mock()), patch("colours.main.Live", return_value=live):
            Spinner.start("outer")
            assert Spinner._depth == 1
            with Spinner("inner"):
                assert Spinner._depth == 2
                assert Spinner._live is live  # reused, not recreated
            # Inner exit must NOT stop the outer spinner.
            assert Spinner._depth == 1
            assert Spinner._live is live
            live.stop.assert_not_called()
            Spinner.stop()  # outermost stop tears it down
            assert Spinner._depth == 0
            live.stop.assert_called_once_with()
        assert Spinner._live is None

    @staticmethod
    def test_stop_when_inactive_does_not_go_negative() -> None:
        """Extra stop calls must not drive the nesting depth negative."""
        Spinner.stop()
        Spinner.stop()
        assert Spinner._depth == 0

    @staticmethod
    def test_make_spinner_uses_custom_frames() -> None:
        """Custom spinners are built from the private registry, not Rich globals."""
        from colours.main import _CUSTOM_SPINNERS, _make_spinner  # noqa: PLC0415, PLC2701

        spinner = _make_spinner("xanaduai", "hi", style=None, speed=1.0)
        assert spinner.name == "xanaduai"
        assert spinner.frames == _CUSTOM_SPINNERS["xanaduai"]["frames"]
        assert spinner.interval == _CUSTOM_SPINNERS["xanaduai"]["interval"]

    @staticmethod
    def test_direct_instantiation_is_forbidden() -> None:
        """Spinner is a singleton; constructing it via () enters a context, never an instance."""
        # Calling Spinner(...) returns the class (for `with`), not a new instance.
        assert Spinner("x") is Spinner
        Spinner._pending = None  # cleanup stashed args


class TestSpinnerRegistration:
    """Test custom spinner registration and filtering."""

    @staticmethod
    def test_custom_spinners_registered() -> None:
        """Custom XanaduAI spinners should be present in the library's name list."""
        assert "xanaduai" in SPINNER_NAMES
        assert "xanaduai_ticker" in SPINNER_NAMES
        assert "xanaduai" in _CUSTOM_SPINNERS
        assert "xanaduai_ticker" in _CUSTOM_SPINNERS

    @staticmethod
    def test_toggle_spinners_removed() -> None:
        """Toggle spinners should be filtered out of the library's name list."""
        assert all("toggle" not in spinner_name for spinner_name in SPINNER_NAMES)

    @staticmethod
    def test_rich_global_registry_untouched() -> None:
        """Importing colours must not mutate Rich's global SPINNERS registry."""
        # Custom spinners are NOT injected into Rich's global dict.
        assert "xanaduai" not in SPINNERS
        assert "xanaduai_ticker" not in SPINNERS
        # Rich's own toggle spinners are left in place.
        assert any("toggle" in spinner_name for spinner_name in SPINNERS)
