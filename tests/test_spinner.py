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

import atexit
import logging
from collections.abc import Generator
from unittest.mock import Mock

import pytest
from rich.console import Console

from colours import Colour
from colours.main import (
    _CUSTOM_SPINNERS,  # noqa: PLC2701
    LOGGER,
    SPINNER_NAMES,
    SPINNERS,
    ColourHandler,
    Spinner,
    _make_spinner,  # noqa: PLC2701
    _spinner_console,  # noqa: PLC2701
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


class TestSpinnerTerminalIntegrity:
    """Test that the spinner cooperates with logging and restores the terminal."""

    @staticmethod
    def test_live_shares_console_with_stdout_handler() -> None:
        """Live must render through the stdout ColourHandler's Console instance.

        A separate Console bypasses Rich's live-render hook, which appends log
        text directly onto the spinner's line.
        """
        stdout_console = next(h.console for h in LOGGER.handlers if isinstance(h, ColourHandler) and not h.console.stderr)
        Spinner.start("sharing", name="dots")
        try:
            assert Spinner._live is not None
            assert Spinner._live.console is stdout_console
        finally:
            Spinner.terminate()

    @staticmethod
    def test_spinner_console_resolves_live_and_falls_back() -> None:
        """Resolves the current stdout handler, and falls back when none is attached."""
        stdout_handler = next(h for h in LOGGER.handlers if isinstance(h, ColourHandler) and not h.console.stderr)
        assert _spinner_console() is stdout_handler.console

        original = LOGGER.handlers[:]
        try:
            LOGGER.handlers = []
            fallback = _spinner_console()
            assert not fallback.stderr
        finally:
            LOGGER.handlers = original

    @staticmethod
    def test_spinner_console_is_resolved_per_start() -> None:
        """modify_log_format replaces handlers, so the console must not be cached."""
        Colour.modify_log_format()
        new_console = next(h.console for h in LOGGER.handlers if isinstance(h, ColourHandler) and not h.console.stderr)
        Spinner.start("after reformat", name="dots")
        try:
            assert Spinner._live is not None
            assert Spinner._live.console is new_console
        finally:
            Spinner.terminate()

    @staticmethod
    def test_atexit_hook_is_registered() -> None:
        """The exit hook must be registered so the cursor is never left hidden."""
        before = atexit._ncallbacks()
        atexit.unregister(_terminate_spinner_at_exit)
        after = atexit._ncallbacks()
        atexit.register(_terminate_spinner_at_exit)  # restore
        assert after == before - 1, "_terminate_spinner_at_exit was not registered with atexit"

    @staticmethod
    def test_atexit_hook_terminates_running_spinner() -> None:
        """A spinner left running at exit is torn down."""
        Spinner.start("never stopped", name="dots")
        assert Spinner._live is not None
        _terminate_spinner_at_exit()
        assert Spinner._live is None
        assert Spinner._depth == 0

    @staticmethod
    def test_atexit_hook_suppresses_teardown_errors() -> None:
        """Interpreter shutdown may break streams; the hook must never raise."""
        live = Mock()
        live.stop.side_effect = RuntimeError("stream closed")
        Spinner._live = live
        Spinner._depth = 1
        _terminate_spinner_at_exit()
        assert Spinner._live is None


class TestSpinnerStderrHook:
    """Test that the stderr console shares the spinner's live-render hook.

    Live only hooks its own console, so without this, WARNING+ records are written
    without clearing the spinner's line and get appended onto it.
    """

    @staticmethod
    @pytest.fixture
    def terminal_handlers() -> Generator[tuple[ColourHandler, ColourHandler], None, None]:
        """Swap in a stdout/stderr ColourHandler pair whose consoles report as terminals."""
        original = LOGGER.handlers[:]
        stdout_hndlr = ColourHandler(level=logging.DEBUG, stderr=False)
        stderr_hndlr = ColourHandler(level=logging.WARNING, stderr=True)
        for hndlr in (stdout_hndlr, stderr_hndlr):
            hndlr.console = Console(stderr=hndlr.console.stderr, force_terminal=True)
        LOGGER.handlers = [stdout_hndlr, stderr_hndlr]
        try:
            yield stdout_hndlr, stderr_hndlr
        finally:
            LOGGER.handlers = original

    @staticmethod
    def test_hook_pushed_onto_stderr_console_and_popped(
        terminal_handlers: tuple[ColourHandler, ColourHandler],
    ) -> None:
        """The stderr console gets the hook while running, and loses it on teardown."""
        _, stderr_hndlr = terminal_handlers
        before = len(stderr_hndlr.console._render_hooks)

        Spinner.start("working", name="dots")
        try:
            assert Spinner._hooked == (stderr_hndlr.console,)
            assert stderr_hndlr.console._render_hooks[-1] is Spinner._live
            assert len(stderr_hndlr.console._render_hooks) == before + 1
        finally:
            Spinner.terminate()

        assert Spinner._hooked == ()
        assert len(stderr_hndlr.console._render_hooks) == before

    @staticmethod
    def test_live_console_is_never_double_hooked(
        terminal_handlers: tuple[ColourHandler, ColourHandler],
    ) -> None:
        """Live already hooks its own console; it must not be hooked twice."""
        stdout_hndlr, _ = terminal_handlers
        Spinner.start("working", name="dots")
        try:
            assert stdout_hndlr.console not in Spinner._hooked
            assert Spinner._live is not None
            assert Spinner._live.console is stdout_hndlr.console
        finally:
            Spinner.terminate()

    @staticmethod
    def test_hooks_do_not_accumulate_across_cycles(
        terminal_handlers: tuple[ColourHandler, ColourHandler],
    ) -> None:
        """Repeated start/stop cycles must not leak render hooks."""
        _, stderr_hndlr = terminal_handlers
        before = len(stderr_hndlr.console._render_hooks)
        for _ in range(3):
            Spinner.start("working", name="dots")
            Spinner.stop()
        assert len(stderr_hndlr.console._render_hooks) == before
        assert Spinner._hooked == ()

    @staticmethod
    def test_non_terminal_console_is_not_hooked() -> None:
        """Control sequences must never be written into a redirected (non-tty) stream."""
        original = LOGGER.handlers[:]
        stdout_hndlr = ColourHandler(level=logging.DEBUG, stderr=False)
        stderr_hndlr = ColourHandler(level=logging.WARNING, stderr=True)
        stdout_hndlr.console = Console(force_terminal=True)
        stderr_hndlr.console = Console(stderr=True, force_terminal=False)
        LOGGER.handlers = [stdout_hndlr, stderr_hndlr]
        try:
            Spinner.start("working", name="dots")
            assert Spinner._hooked == ()
            assert not stderr_hndlr.console.is_terminal
        finally:
            Spinner.terminate()
            LOGGER.handlers = original

    @staticmethod
    def test_duplicate_consoles_are_hooked_once() -> None:
        """Two handlers sharing one console must not get the hook pushed twice."""
        original = LOGGER.handlers[:]
        shared = Console(stderr=True, force_terminal=True)
        stdout_hndlr = ColourHandler(level=logging.DEBUG, stderr=False)
        stdout_hndlr.console = Console(force_terminal=True)
        dupes = [ColourHandler(level=logging.WARNING, stderr=True) for _ in range(2)]
        for hndlr in dupes:
            hndlr.console = shared
        LOGGER.handlers = [stdout_hndlr, *dupes]
        try:
            Spinner.start("working", name="dots")
            assert Spinner._hooked == (shared,)
        finally:
            Spinner.terminate()
            LOGGER.handlers = original

    @staticmethod
    def test_non_colour_handlers_are_ignored() -> None:
        """Plain logging handlers have no Rich console and must be skipped."""
        original = LOGGER.handlers[:]
        stdout_hndlr = ColourHandler(level=logging.DEBUG, stderr=False)
        stdout_hndlr.console = Console(force_terminal=True)
        stderr_hndlr = ColourHandler(level=logging.WARNING, stderr=True)
        stderr_hndlr.console = Console(stderr=True, force_terminal=True)
        LOGGER.handlers = [logging.StreamHandler(), stdout_hndlr, stderr_hndlr]
        try:
            Spinner.start("working", name="dots")
            assert Spinner._hooked == (stderr_hndlr.console,)
        finally:
            Spinner.terminate()
            LOGGER.handlers = original


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
