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

import logging
import subprocess
import sys
from collections.abc import Generator
from typing import Any
from unittest.mock import Mock

import pytest
from rich.console import Console
from rich.markup import render

from colours import LOGGER, SPINNER_NAMES, Colour, ColourHandler, Spinner
from colours.main import (
    _CUSTOM_SPINNERS,  # noqa: PLC2701
    SPINNERS,
    _make_spinner,  # noqa: PLC2701
    _terminate_spinner_at_exit,  # noqa: PLC2701
)


@pytest.fixture(autouse=True)
def reset_spinner() -> Generator[None, None, None]:
    """Ensure spinner singleton state does not leak between tests."""
    Spinner.terminate()
    Spinner._live = None
    Spinner._spinner = None
    Spinner._hooked = ()
    Spinner._depth = 0
    yield
    Spinner.terminate()
    Spinner._live = None
    Spinner._spinner = None
    Spinner._hooked = ()
    Spinner._depth = 0


def _is_running() -> bool:
    return Spinner._live is not None


def _trail(records: list[logging.LogRecord]) -> list[tuple[str, str]]:
    """Reduce captured records to ``(levelname, message)`` pairs, with the marker markup rendered away."""
    return [(record.levelname, render(record.getMessage()).plain) for record in records]


class TestSpinnerLifecycle:
    """Test starting, nesting, and stopping the singleton spinner."""

    @staticmethod
    def test_nested_starts_share_one_spinner_and_persist_each_message_once(
        log_records: list[logging.LogRecord],
    ) -> None:
        """Inner levels reuse the running spinner; only the outermost stop tears it down."""
        Spinner.start("one", name="dots")
        live = Spinner._live
        Spinner.text("two")
        with Spinner("three"):
            assert Spinner._live is live
        assert Spinner._live is live, "an inner context must not stop the outer spinner"
        assert Spinner._spinner is not None
        assert str(Spinner._spinner.text) == "three"
        Spinner.stop()
        assert not _is_running()
        assert _trail(log_records) == [("DEBUG", "✔ one"), ("DEBUG", "✔ two"), ("DEBUG", "✔ three")]

    @staticmethod
    def test_calls_on_an_inactive_spinner_are_noops(log_records: list[logging.LogRecord]) -> None:
        """Stray fail/text/stop calls do nothing and do not unbalance later nesting."""
        Spinner.fail()
        Spinner.text("ignored")
        Spinner.stop()
        Spinner.stop()
        assert not _is_running()
        assert log_records == []

        Spinner.start("outer", name="dots")
        Spinner.start("inner")
        Spinner.stop()
        assert _is_running()
        Spinner.stop()
        assert not _is_running()

    @staticmethod
    @pytest.mark.parametrize(
        ("end", "expected"),
        [("terminate", []), ("fail", [("ERROR", "✖ work")])],
    )
    def test_terminate_and_fail_ignore_nesting(
        end: str,
        expected: list[tuple[str, str]],
        log_records: list[logging.LogRecord],
    ) -> None:
        """terminate() abandons silently and fail() reports ✖; both tear down at any depth."""
        Spinner.start("work", name="dots")
        Spinner.start()
        getattr(Spinner, end)()
        assert not _is_running()
        assert _trail(log_records) == expected

        Spinner.start(name="dots")
        Spinner.stop()
        assert not _is_running(), "nesting depth must be reset"

    @staticmethod
    def test_teardown_clears_state_even_when_the_terminal_errors() -> None:
        """A failing Live.stop() propagates from stop() without leaving a stale spinner; the exit hook swallows it."""
        live = Mock()
        live.stop.side_effect = RuntimeError("console closed")
        Spinner._live, Spinner._spinner, Spinner._depth = live, Mock(), 1
        with pytest.raises(RuntimeError, match="console closed"):
            Spinner.stop()
        assert not _is_running()

        Spinner._live, Spinner._depth = live, 1
        _terminate_spinner_at_exit()
        assert not _is_running()


class TestSpinnerContext:
    """Test the ``with Spinner`` forms and failure reporting."""

    @staticmethod
    def test_context_manager_forms(log_records: list[logging.LogRecord]) -> None:
        """`with Spinner` and `with Spinner(...)` bind the class, run for the block, and skip blank messages."""
        Spinner("never entered", name="dots")
        with Spinner as s:
            assert s is Spinner
            assert Spinner._spinner is not None
            assert Spinner._spinner.name in SPINNER_NAMES
            assert not str(Spinner._spinner.text), "an un-entered Spinner(...) call must not leak into later contexts"
        assert not _is_running()

        with Spinner("msg", name="dots") as s:
            assert s is Spinner
            assert _is_running()
        assert not _is_running()
        assert _trail(log_records) == [("DEBUG", "✔ msg")]

    @staticmethod
    def test_exception_in_context_reports_failure(log_records: list[logging.LogRecord]) -> None:
        """An exception marks the current message ✖ at ERROR, in either form, and blank messages are skipped."""
        msg = "exploded"

        def _work() -> None:
            Spinner.text("Working...")
            raise ValueError(msg)

        with pytest.raises(ValueError, match=msg), Spinner("Submitting...", name="dots"):
            raise ValueError(msg)
        with pytest.raises(ValueError, match=msg), Spinner:
            _work()
        with pytest.raises(ValueError, match=msg), Spinner(name="dots"):
            raise ValueError(msg)
        assert not _is_running()
        assert _trail(log_records) == [("ERROR", "✖ Submitting..."), ("ERROR", "✖ Working...")]

    @staticmethod
    def test_nested_failure_reports_only_the_innermost_message(log_records: list[logging.LogRecord]) -> None:
        """An exception unwinds every level but reports a single ✖ for the innermost message."""
        msg = "exploded"
        with pytest.raises(ValueError, match=msg), Spinner("outer", name="dots"), Spinner("inner"):
            raise ValueError(msg)
        assert not _is_running()
        assert _trail(log_records) == [("DEBUG", "✔ outer"), ("ERROR", "✖ inner")]

    @staticmethod
    def test_persisted_messages_are_plain_text(log_records: list[logging.LogRecord]) -> None:
        """Spinner markup styles the live line only; it cannot inject styles into the log record."""
        Spinner.start("[bold]styled[/bold]", name="dots")
        Spinner.text("[red]next[/red]")
        Spinner.stop()
        tick = Colour.GREEN("✔")
        assert [record.getMessage() for record in log_records] == [f"{tick} styled", f"{tick} next"]


class TestSpinnerOptions:
    """Test spinner names, speed, and argument validation."""

    @staticmethod
    @pytest.mark.parametrize(
        ("kwargs", "error"),
        [
            ({"name": "dots", "speed": 0}, "speed must be positive"),
            ({"name": "dots", "speed": -1}, "speed must be positive"),
            ({"name": "dotz"}, "Invalid spinner name 'dotz'"),
        ],
        ids=["zero_speed", "negative_speed", "unknown_name"],
    )
    def test_invalid_arguments_leave_no_spinner_behind(
        kwargs: dict[str, Any],
        error: str,
        log_records: list[logging.LogRecord],
    ) -> None:
        """A rejected start() raises ValueError, persists nothing, and leaves nesting balanced."""
        with pytest.raises(ValueError, match=error):
            Spinner.start("doomed", **kwargs)
        assert not _is_running()
        assert log_records == []

        Spinner.start(name="dots")
        Spinner.stop()
        assert not _is_running()

    @staticmethod
    def test_spinner_names() -> None:
        """The random pool adds the custom spinners and drops Rich's toggles, which stay valid by name."""
        assert {"xanaduai", "xanaduai_ticker"} <= set(SPINNER_NAMES)
        assert not any("toggle" in name for name in SPINNER_NAMES)
        for name in (*SPINNER_NAMES, "toggle", "toggle13"):
            assert _make_spinner(name, "hi", style=None, speed=1.0).name == name
        assert "xanaduai" not in SPINNERS, "custom spinners must not be registered in Rich's global registry"

        with pytest.raises(ValueError, match="Invalid spinner name") as excinfo:
            _make_spinner("nope", "hi", style=None, speed=1.0)
        for name in (*SPINNER_NAMES, "toggle"):
            assert name in str(excinfo.value)

    @staticmethod
    @pytest.mark.parametrize("name", ["xanaduai", "xanaduai_ticker"])
    def test_custom_spinner_animates_at_its_interval_scaled_by_speed(name: str) -> None:
        """At speed=2, 1.25 intervals in, a custom spinner shows frame 2, exactly like Rich's built-ins."""
        definition = _CUSTOM_SPINNERS[name]
        spinner = _make_spinner(name, "hi", style=None, speed=2.0)
        spinner.start_time = 0.0
        elapsed = 1.25 * definition["interval"] / 1000
        assert str(spinner.render(0.0)).startswith(definition["frames"][0])
        assert str(spinner.render(elapsed)).startswith(definition["frames"][2])


class TestSpinnerTerminal:
    """Test that the spinner cooperates with logging output and restores the terminal."""

    @staticmethod
    def test_live_renders_through_the_current_stdout_handler_console() -> None:
        """Sharing the handler's Console stops log lines landing on the spinner line; it is re-resolved per start."""
        Colour.modify_log_format()
        stdout_console = next(h.console for h in LOGGER.handlers if isinstance(h, ColourHandler) and not h.console.stderr)
        Spinner.start("sharing", name="dots")
        assert Spinner._live is not None
        assert Spinner._live.console is stdout_console
        assert Spinner._live.transient, "stop() must erase the frame that the ✔ line replaces"
        Spinner.terminate()

        LOGGER.handlers = []
        Spinner.start("fallback", name="dots")
        assert Spinner._live is not None
        assert not Spinner._live.console.stderr

    @staticmethod
    def test_terminal_stderr_console_shares_the_render_hook_while_running() -> None:
        """WARNING+ records must clear the spinner line too; the hook is removed again on every stop."""
        stdout_hndlr = ColourHandler(level=logging.DEBUG, stderr=False)
        stdout_hndlr.console = Console(force_terminal=True)
        stderr_hndlr = ColourHandler(level=logging.WARNING, stderr=True)
        stderr_hndlr.console = Console(stderr=True, force_terminal=True)
        LOGGER.handlers = [stdout_hndlr, stderr_hndlr]
        before = len(stderr_hndlr.console._render_hooks)
        for _ in range(2):
            Spinner.start("working", name="dots")
            assert Spinner._hooked == (stderr_hndlr.console,)
            assert stderr_hndlr.console._render_hooks[-1] is Spinner._live
            Spinner.stop()
            assert Spinner._hooked == ()
            assert len(stderr_hndlr.console._render_hooks) == before

    @staticmethod
    def test_only_distinct_terminal_colour_handler_consoles_are_hooked() -> None:
        """Redirected streams, duplicate consoles, and non-Rich handlers are all skipped."""
        stdout_hndlr = ColourHandler(stderr=False)
        stdout_hndlr.console = Console(force_terminal=True)
        shared = Console(stderr=True, force_terminal=True)
        duplicates = [ColourHandler(), ColourHandler()]
        for hndlr in duplicates:
            hndlr.console = shared
        redirected = ColourHandler()
        redirected.console = Console(stderr=True, force_terminal=False)
        LOGGER.handlers = [logging.StreamHandler(), stdout_hndlr, *duplicates, redirected]
        Spinner.start("working", name="dots")
        assert Spinner._hooked == (shared,)

    @staticmethod
    def test_spinner_left_running_at_exit_is_persisted() -> None:
        """A real interpreter exit runs the hook, which persists the trailing message."""
        code = (
            "import logging; from colours import LOGGER, Spinner; "
            "LOGGER.setLevel(logging.DEBUG); Spinner.start('never stopped', name='dots')"
        )
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30, check=True)
        assert "✔ never stopped" in out.stdout

    @staticmethod
    @pytest.mark.parametrize("attr", ["last_exc", "last_value"])
    def test_exit_hook_reports_success_or_failure(
        attr: str,
        log_records: list[logging.LogRecord],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A clean exit persists ✔; exiting via a traceback (sys.last_exc on 3.12+, sys.last_value on 3.11) reports ✖."""
        monkeypatch.delattr(sys, "last_exc", raising=False)
        monkeypatch.delattr(sys, "last_value", raising=False)
        Spinner.start("finished", name="dots")
        _terminate_spinner_at_exit()
        assert not _is_running()

        monkeypatch.setattr(sys, attr, RuntimeError("boom"), raising=False)
        Spinner.start("crashed", name="dots")
        _terminate_spinner_at_exit()
        assert not _is_running()
        assert _trail(log_records) == [("DEBUG", "✔ finished"), ("ERROR", "✖ crashed")]
