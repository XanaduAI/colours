# Copyright 2025 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Colour Tests."""

import logging
import os
from collections.abc import Callable, Generator
from subprocess import run
from sys import executable
from unittest.mock import Mock, patch

import pytest
from rich.highlighter import ReprHighlighter

from colours import Colour, ColourHandler, colour_logger


@pytest.fixture
def mock_print() -> Generator[Mock, None, None]:
    """Mock Rich's print function for testing."""
    with patch("colours.main.rich_print") as rp:
        rp.__name__ = "print"
        rp.__doc__ = "This is a doc string."
        yield rp


def _messages(records: list[logging.LogRecord]) -> list[tuple[int, str]]:
    """Reduce captured records to ``(levelno, formatted message)`` pairs."""
    return [(record.levelno, record.getMessage()) for record in records]


class TestMarkup:
    """Test wrapping, highlighting, and stripping markup in plain strings."""

    @staticmethod
    def test_call_wraps_any_value_in_style_tags() -> None:
        """Calling a member wraps str(value) in that member's Rich style tags, and nests cleanly."""
        assert Colour.red("hello") == "[red]hello[/red]"
        assert Colour.BLUE(42) == "[bold deep_sky_blue1]42[/bold deep_sky_blue1]"
        assert Colour.green("") == "[green][/green]"
        assert Colour.red(Colour.blue("inner")) == "[red][deep_sky_blue1]inner[/deep_sky_blue1][/red]"

    @staticmethod
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            (
                "TypeError and syntax error: bad",
                "[bold red]TypeError[/bold red] and syntax [bold red]error:[/bold red] bad",
            ),
            ("MyCustomErrorHandler failed", "[bold red]MyCustomErrorHandler[/bold red] failed"),
            ("Everything is fine.", "Everything is fine."),
        ],
        ids=["case_insensitive_with_colon", "substring", "no_match"],
    )
    def test_red_error_highlights_words_containing_error(text: str, expected: str) -> None:
        """Every word containing 'error' (any case, with an optional trailing colon) is bolded red."""
        assert Colour.red_error(text) == expected

    @staticmethod
    def test_red_error_can_print_the_result(mock_print: Mock) -> None:
        """display=True prints the highlighted text as well as returning it."""
        assert Colour.red_error("Fatal Error", display=True) == "Fatal [bold red]Error[/bold red]"
        mock_print.assert_called_once_with("Fatal [bold red]Error[/bold red]")

    @staticmethod
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("Outer \x1b[1;35mMagenta \x1b[4mUnderlined\x1b[0m\x1b[42m no reset", "Outer Magenta Underlined no reset"),
            ("Line1\n\x1b[1A\x1b[10;20HLine2\x1b[2J\x1b[K!", "Line1\nLine2!"),
            ("Plain text string.", "Plain text string."),
        ],
        ids=["styles", "cursor_and_erase", "plain_text"],
    )
    def test_remove_ansi(text: str, expected: str) -> None:
        """ANSI style, cursor, and erase sequences are stripped; plain text is untouched."""
        assert Colour.remove_ansi(text) == expected


class TestPrint:
    """Test Colour.print and Colour.<colour>.print."""

    @staticmethod
    def test_member_print_styles_every_argument(mock_print: Mock) -> None:
        """Each positional argument, of any type, is wrapped; keyword arguments pass through."""
        Colour.red.print("count:", 42, sep=" | ", end="!\n")
        mock_print.assert_called_once_with("[red]count:[/red]", "[red]42[/red]", sep=" | ", end="!\n")

    @staticmethod
    def test_class_print_is_unstyled(mock_print: Mock) -> None:
        """Printing from the class itself forwards arguments untouched."""
        Colour.print("arg", 42, sep=", ")
        mock_print.assert_called_once_with("arg", 42, sep=", ")


class TestLogging:
    """Test the records each logging method emits."""

    @staticmethod
    def test_class_methods_log_the_message_unstyled(log_records: list[logging.LogRecord]) -> None:
        """Colour.debug/info/log pass the message and args through, leaving Rich's highlighter in charge."""
        Colour.debug("count: %d", 42)
        Colour.info("info")
        Colour.log("warning", "named level")
        Colour.log(23, "custom level")
        assert _messages(log_records) == [
            (logging.DEBUG, "count: 42"),
            (logging.INFO, "info"),
            (logging.WARNING, "named level"),
            (23, "custom level"),
        ]
        assert all("highlighter" not in vars(record) for record in log_records)

    @staticmethod
    def test_member_methods_style_only_the_message(log_records: list[logging.LogRecord]) -> None:
        """Colour.<colour>.debug/info/log wrap the message (not its args) and disable highlighting."""
        Colour.blue.debug("debug")
        Colour.red.info("count: %d", 42)
        Colour.green.log("ERROR", "named level")
        Colour.green.log(47, "custom level")
        assert _messages(log_records) == [
            (logging.DEBUG, "[deep_sky_blue1]debug[/deep_sky_blue1]"),
            (logging.INFO, "[red]count: 42[/red]"),
            (logging.ERROR, "[green]named level[/green]"),
            (47, "[green]custom level[/green]"),
        ]
        assert all(vars(record)["highlighter"] is None for record in log_records)

    @staticmethod
    def test_severity_methods_use_fixed_styles(log_records: list[logging.LogRecord]) -> None:
        """Warning is orange, error is red with error words bolded, critical is bold red; kwargs pass through."""
        exc = ValueError("boom")
        Colour.warning("Houston, we have a %s", "problem", exc_info=exc)
        Colour.error("MyError happened")
        Colour.error("something failed")
        Colour.critical("system down")
        assert _messages(log_records) == [
            (logging.WARNING, "[orange1]Houston, we have a problem[/orange1]"),
            (logging.ERROR, "[red][bold red]MyError[/bold red] happened[/red]"),
            (logging.ERROR, "[red]something failed[/red]"),
            (logging.CRITICAL, "[bold red]system down[/bold red]"),
        ]
        assert log_records[0].exc_info == (ValueError, exc, None)
        assert all(vars(record)["highlighter"] is None for record in log_records)

    @staticmethod
    def test_messages_below_the_logger_level_are_dropped(log_records: list[logging.LogRecord]) -> None:
        """Every logging method respects the logger level, up to silencing everything."""
        Colour.set_log_level("error")
        for log in (Colour.debug, Colour.blue.debug, Colour.info, Colour.blue.info, Colour.warning):
            log("dropped")
        Colour.log("info", "dropped")
        Colour.blue.log(logging.INFO, "dropped")
        assert log_records == []

        Colour.error("kept")
        Colour.critical("kept")
        assert [record.levelno for record in log_records] == [logging.ERROR, logging.CRITICAL]

        Colour.set_log_level(100)
        Colour.critical("silenced")
        assert len(log_records) == 2

    @staticmethod
    def test_user_extra_is_kept_and_may_override_the_highlighter(log_records: list[logging.LogRecord]) -> None:
        """User extra fields reach the record, and a user highlighter wins over the styled default of None."""
        highlighter = ReprHighlighter()
        extra = {"request_id": "abc"}
        Colour.info("plain", extra=extra)
        Colour.blue.log("info", "styled", extra=extra)
        Colour.warning("custom", extra={"highlighter": highlighter})
        plain, styled, custom = (vars(record) for record in log_records)
        assert plain["request_id"] == styled["request_id"] == "abc"
        assert "highlighter" not in plain
        assert styled["highlighter"] is None
        assert custom["highlighter"] is highlighter
        assert extra == {"request_id": "abc"}, "the caller's extra dict must not be mutated"


class TestLogLevels:
    """Test log level parsing and validation."""

    @staticmethod
    @pytest.mark.parametrize(
        ("level", "expected"),
        [("debug", logging.DEBUG), ("Warning", logging.WARNING), ("warn", logging.WARNING), ("15", 15)],
    )
    def test_set_log_level_accepts_names_and_numeric_strings(level: str, expected: int) -> None:
        """Level names are case-insensitive (including the deprecated 'warn'), and numeric strings are parsed."""
        Colour.set_log_level(level)
        assert colour_logger.level == expected

    @staticmethod
    @pytest.mark.parametrize(
        "call",
        [
            lambda: Colour.set_log_level("verbose"),
            lambda: Colour.log("verbose", "msg"),
            lambda: Colour.blue.log("verbose", "msg"),
            lambda: Colour.modify_log_format(stdout_filter_level="verbose"),
        ],
        ids=["set_log_level", "log", "member_log", "modify_log_format"],
    )
    def test_invalid_level_names_are_rejected(call: Callable[[], None]) -> None:
        """Unknown level names raise a ValueError that lists the valid names."""
        with pytest.raises(ValueError, match="Invalid log level 'verbose'") as excinfo:
            call()
        for name in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            assert name in str(excinfo.value)


class TestOutput:
    """Test where log output actually lands."""

    @staticmethod
    def test_records_below_warning_go_to_stdout_and_the_rest_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
        """Each record is rendered (not printed as raw markup) to exactly one stream."""
        Colour.set_log_level("debug")
        Colour.debug("debugmsg")
        Colour.blue.info("infomsg")
        Colour.warning("warnmsg")
        Colour.critical("criticalmsg")
        out, err = capsys.readouterr()
        assert "debugmsg" in out
        assert "infomsg" in out
        assert "warnmsg" in err
        assert "criticalmsg" in err
        assert "infomsg" not in err
        assert "warnmsg" not in out
        assert "criticalmsg" not in out
        assert "[deep_sky_blue1]" not in out
        assert "[orange1]" not in err

    @staticmethod
    def test_logger_level_alone_controls_verbosity(capsys: pytest.CaptureFixture[str]) -> None:
        """Lowering then raising the level takes effect, whether set via the helper or the logger itself."""
        # Rebuilding the handlers at INFO catches a stdout handler that pins its own level.
        Colour.set_log_level("info")
        Colour.modify_log_format()
        Colour.set_log_level("debug")
        Colour.debug("firstdebug")
        Colour.set_log_level("info")
        Colour.debug("seconddebug")
        Colour.logger.setLevel(logging.DEBUG)
        Colour.debug("thirddebug")
        out = capsys.readouterr().out
        assert "firstdebug" in out
        assert "seconddebug" not in out
        assert "thirddebug" in out

    @staticmethod
    def test_logger_is_the_documented_named_logger_and_does_not_propagate(caplog: pytest.LogCaptureFixture) -> None:
        """Colour.logger, colour_logger, and getLogger('xanadu.colours') agree, and records are not duplicated via root."""
        assert Colour.logger is colour_logger
        assert colour_logger is logging.getLogger("xanadu.colours")
        Colour.warning("not duplicated")
        assert caplog.records == []

    @staticmethod
    def test_modify_log_format_replaces_colour_handlers(capsys: pytest.CaptureFixture[str]) -> None:
        """The new split and display flags take effect, and non-colours handlers are left alone."""
        foreign = logging.NullHandler()
        colour_logger.addHandler(foreign)
        Colour.modify_log_format(show_level=True, stdout_filter_level="error")
        Colour.warning("warnmsg")
        Colour.error("errmsg")
        out, err = capsys.readouterr()
        assert "WARNING" in out
        assert "warnmsg" in out
        assert "ERROR" in err
        assert "errmsg" in err
        assert "warnmsg" not in err
        assert "errmsg" not in out
        assert foreign in colour_logger.handlers
        assert sum(isinstance(handler, ColourHandler) for handler in colour_logger.handlers) == 2

    @staticmethod
    def test_env_vars_set_level_and_split_at_import() -> None:
        """XANADU_COLOURS_LEVEL and XANADU_COLOURS_SPLIT configure the logger when colours is imported."""
        code = "from colours import Colour; Colour.debug('debugmsg'); Colour.warning('warnmsg'); Colour.error('errmsg')"
        res = run(
            [executable, "-c", code],
            check=True,
            text=True,
            capture_output=True,
            env=os.environ.copy() | {"XANADU_COLOURS_LEVEL": "DEBUG", "XANADU_COLOURS_SPLIT": "ERROR"},
        )
        assert "debugmsg" in res.stdout
        assert "warnmsg" in res.stdout
        assert "errmsg" in res.stderr
        assert "errmsg" not in res.stdout
