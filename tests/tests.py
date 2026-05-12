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
from unittest.mock import Mock, patch

import pytest

from colours import Color, Colour, ColourHandler
from colours.main import LOGGER, MaxLevelFilter, _parse_log_level  # noqa: PLC2701


@pytest.fixture
def mock_print():
    """Mock Rich's print function for testing."""
    with patch("colours.main.rich_print") as rp:
        rp.__name__ = "print"
        rp.__doc__ = "This is a doc string."
        yield rp


@pytest.fixture
def mock_logger():
    """Mock the logger for testing."""
    with patch("colours.main.LOGGER") as lg:
        lg.isEnabledFor.return_value = True
        yield lg


@pytest.fixture
def mock_handler_class():
    """Mock the logger for testing."""
    with patch("colours.main.ColourHandler") as ch:
        yield ch


# Test cases for ANSI escape sequence removal
ansi_test_cases: dict[str, dict[str, str]] = {
    # --- SGR (Select Graphic Rendition) ---
    "simple_color": {
        "input": "\x1b[31mHello, Red World!\x1b[0m",
        "expected": "Hello, Red World!",
    },
    "bold": {"input": "\x1b[1mBold Text\x1b[0m", "expected": "Bold Text"},
    "underline": {
        "input": "This is \x1b[4mUnderlined\x1b[0m text.",
        "expected": "This is Underlined text.",
    },
    "background_color": {
        "input": "Normal \x1b[42mGreen Background\x1b[0m Normal",
        "expected": "Normal Green Background Normal",
    },
    "multiple_attributes": {
        "input": "\x1b[1;34mBold Blue Text\x1b[0m",
        "expected": "Bold Blue Text",
    },
    "combined_fore_back": {
        "input": "\x1b[31;47mRed on White\x1b[0m",
        "expected": "Red on White",
    },
    "mixed_styles": {
        "input": "\x1b[32mGreen\x1b[0m and \x1b[1;33mBold Yellow\x1b[0m.",
        "expected": "Green and Bold Yellow.",
    },
    "nested_or_adjacent_styles": {
        "input": "Outer \x1b[35mMagenta \x1b[4mUnderlined\x1b[0m\x1b[35m Magenta\x1b[0m Outer",
        "expected": "Outer Magenta Underlined Magenta Outer",
    },
    "no_reset_at_end": {
        "input": "\x1b[36mCyan text goes on",
        "expected": "Cyan text goes on",
    },
    "starts_with_code": {
        "input": "\x1b[90mGray Text\x1b[0m",  # 90 is bright black / gray
        "expected": "Gray Text",
    },
    # --- Cursor Control & Erasing (Usually removed entirely) ---
    "cursor_position": {
        "input": "Before\x1b[10;20HAfter",  # Move cursor to row 10, column 20
        "expected": "BeforeAfter",
    },
    "cursor_up": {
        "input": "Line1\n\x1b[1ALine2",  # Move cursor up 1 line
        "expected": "Line1\nLine2",
    },
    "erase_screen": {
        "input": "Top\x1b[2JBottom",  # Erase entire screen
        "expected": "TopBottom",
    },
    "erase_line": {
        "input": "Start\x1b[KEnd",  # Erase from cursor to end of line
        "expected": "StartEnd",
    },
    # --- Edge Cases ---
    "only_codes": {"input": "\x1b[1m\x1b[31m\x1b[4m\x1b[0m", "expected": ""},
    "empty_string": {"input": "", "expected": ""},
    "no_codes": {"input": "Plain text string.", "expected": "Plain text string."},
    "interspersed_codes": {
        "input": "T\x1b[31me\x1b[0m\x1b[1ms\x1b[0m\x1b[4mt\x1b[0m",
        "expected": "Test",
    },
}
# Extract data into the format required by parametrize
test_data = ((data["input"], data["expected"]) for data in ansi_test_cases.values())
# List of descriptive IDs for each test case
test_ids = list(ansi_test_cases.keys())


class TestUtils:
    """Test the Colour utility methods."""

    @pytest.mark.parametrize(("test_input", "expected_output"), test_data, ids=test_ids)
    @staticmethod
    def test_remove_ansi(test_input: str, expected_output: str) -> None:
        """Test ansi removal from strings."""
        assert Colour.remove_ansi(test_input) == expected_output

    @staticmethod
    def test_call() -> None:
        """Test that calling an Enum member wraps the string in colour tags."""
        assert Colour.red("hello") == "[red]hello[/red]"
        assert Colour.BLUE("world") == "[bold deep_sky_blue1]world[/bold deep_sky_blue1]"

    @staticmethod
    def test_red_error() -> None:
        """Test highlighting errors in red."""
        text = "This is a ValueError."
        expected = "This is a [bold red]ValueError[/bold red]."
        assert Colour.red_error(text) == expected

        text_lower = "syntax error here"
        expected_lower = "syntax [bold red]error[/bold red] here"
        assert Colour.red_error(text_lower) == expected_lower

    @staticmethod
    def test_red_error_from_instance() -> None:
        """Test highlighting errors in red.

        This usecase doesn't make sense, but it is valid.
        """
        text = "This is a ValueError."
        expected = "This is a [bold red]ValueError[/bold red]."
        assert Colour.blue.red_error(text) == expected

        text_lower = "syntax error here"
        expected_lower = "syntax [bold red]error[/bold red] here"
        assert Colour.blue.red_error(text_lower) == expected_lower

    @staticmethod
    def test_red_error_display(mock_print: Mock) -> None:
        """Test red_error with display=True."""
        text = "Fatal Error"
        Colour.red_error(text, display=True)
        mock_print.assert_called_once_with("Fatal [bold red]Error[/bold red]")

    @staticmethod
    def test_alias() -> None:
        """Test that Color is an alias for Colour."""
        assert Color is Colour


class TestPrint:
    """Test the Colour.print and Colour.<colour>.print methods."""

    @staticmethod
    def test_print_member(mock_print: Mock) -> None:
        """Test printing using an Enum member."""
        Colour.green.print("success")
        mock_print.assert_called_once_with("[green]success[/green]")

    @staticmethod
    def test_print_static(mock_print: Mock) -> None:
        """Test printing using the class directly (acting as static print)."""
        Colour.print("plain text")
        mock_print.assert_called_once_with("plain text")

    @staticmethod
    def test_print_multiple_strings(mock_print: Mock) -> None:
        """Test printing with multiple string arguments."""
        Colour.blue.print("hello", "world", "test")
        mock_print.assert_called_once_with(
            "[deep_sky_blue1]hello[/deep_sky_blue1]",
            "[deep_sky_blue1]world[/deep_sky_blue1]",
            "[deep_sky_blue1]test[/deep_sky_blue1]",
        )

    @staticmethod
    def test_print_mixed_types(mock_print: Mock) -> None:
        """Test printing with mixed string and non-string arguments."""
        Colour.red.print("count:", 42, "status:", True, 1.234)
        mock_print.assert_called_once_with(
            "[red]count:[/red]",
            "[red]42[/red]",
            "[red]status:[/red]",
            "[red]True[/red]",
            "[red]1.234[/red]",
        )

    @staticmethod
    def test_print_with_kwargs(mock_print: Mock) -> None:
        """Test printing with keyword arguments."""
        Colour.yellow.print("line1", "line2", sep=" | ", end="!\n")
        mock_print.assert_called_once_with(
            "[yellow]line1[/yellow]",
            "[yellow]line2[/yellow]",
            sep=" | ",
            end="!\n",
        )

    @staticmethod
    def test_print_non_string_only(mock_print: Mock) -> None:
        """Test printing with only non-string arguments."""
        Colour.purple.print(123, 456, 789)
        mock_print.assert_called_once_with("[magenta]123[/magenta]", "[magenta]456[/magenta]", "[magenta]789[/magenta]")

    @staticmethod
    def test_print_empty_string(mock_print: Mock) -> None:
        """Test printing with empty string."""
        Colour.green.print("")
        mock_print.assert_called_once_with("[green][/green]")

    @staticmethod
    def test_print_static_multiple_args(mock_print: Mock) -> None:
        """Test static print with multiple arguments and kwargs."""
        Colour.print("arg1", 42, "arg2", sep=", ", end="")
        mock_print.assert_called_once_with("arg1", 42, "arg2", sep=", ", end="")


class TestLogs:
    """Test the Colour logging methods."""

    @staticmethod
    def test_debug_log_static(mock_logger: Mock) -> None:
        """Test Colour.debug respects log level filtering."""
        # At default INFO level (20), debug messages (level 10) should be filtered
        mock_logger.isEnabledFor.return_value = False
        Colour.debug("filtered debug")
        mock_logger.debug.assert_not_called()

        # When log level allows debug messages
        mock_logger.isEnabledFor.return_value = True
        Colour.debug("visible debug")
        mock_logger.debug.assert_called_once_with("visible debug")

    @staticmethod
    def test_debug_log_member(mock_logger: Mock) -> None:
        """Test Colour.blue.debug respects log level filtering."""
        # At default INFO level (20), debug messages (level 10) should be filtered
        mock_logger.isEnabledFor.return_value = False
        Colour.blue.debug("filtered debug")
        mock_logger.debug.assert_not_called()

        # When log level allows debug messages
        mock_logger.isEnabledFor.return_value = True
        Colour.blue.debug("visible debug")
        mock_logger.debug.assert_called_once_with("[deep_sky_blue1]visible debug[/deep_sky_blue1]", extra={"highlighter": None})

    @staticmethod
    def test_info_log_static(mock_logger: Mock) -> None:
        """Test Colour.info logs info messages using logger."""
        Colour.info("info message")
        mock_logger.info.assert_called_once_with("info message")

    @staticmethod
    def test_info_log_member(mock_logger: Mock) -> None:
        """Test Colour.blue.info logs coloured info messages."""
        Colour.blue.info("blue info")
        mock_logger.info.assert_called_once_with("[deep_sky_blue1]blue info[/deep_sky_blue1]", extra={"highlighter": None})

    @staticmethod
    def test_log_static(mock_logger: Mock) -> None:
        """Test Colour.log to create messages using logger."""
        Colour.log("notset", "notset message")
        mock_logger.log.assert_called_once_with(0, "notset message")

    @staticmethod
    def test_log_member(mock_logger: Mock) -> None:
        """Test Colour.blue.log to create messages using logger."""
        Colour.blue.log("critical", "blue critical")
        mock_logger.log.assert_called_once_with(
            50, "[deep_sky_blue1]blue critical[/deep_sky_blue1]", extra={"highlighter": None}
        )

    @staticmethod
    def test_warning_log(mock_logger: Mock) -> None:
        """Test Colour.warning logs warning messages in orange."""
        Colour.warning("warn message")
        mock_logger.warning.assert_called_once_with("[orange1]warn message[/orange1]", extra={"highlighter": None})

    @staticmethod
    def test_error_log(mock_logger: Mock) -> None:
        """Test Colour.error logs error messages in red with error highlighting."""
        Colour.error("bad error")
        expected = "[red]bad [bold red]error[/bold red][/red]"
        mock_logger.error.assert_called_once_with(expected, extra={"highlighter": None})

    @staticmethod
    def test_critical_log(mock_logger: Mock) -> None:
        """Test Colour.critical logs critical messages in red with critical highlighting."""
        Colour.critical("critical error")
        expected = "[bold red]critical error[/bold red]"
        mock_logger.critical.assert_called_once_with(expected, extra={"highlighter": None})

    @staticmethod
    def test_changing_log_level(mock_logger: Mock) -> None:
        """Test that setting the log level above critical causes no logs to display."""
        # When log level is very high (100), isEnabledFor returns False, so no logging occurs
        mock_logger.isEnabledFor.return_value = False
        Colour.set_log_level(100)
        Colour.debug("a message")
        Colour.red.debug("a message")
        Colour.log("info", "a message")
        Colour.red.log("info", "a message")
        Colour.warning("a message")
        Colour.error("a message")
        Colour.critical("a message")

        # Verify no logging methods were called
        mock_logger.debug.assert_not_called()
        mock_logger.log.assert_not_called()
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_logger.critical.assert_not_called()

        # Reset and test with low log level
        mock_logger.reset_mock()
        mock_logger.isEnabledFor.return_value = True
        Colour.set_log_level(1)
        Colour.debug("a message")
        Colour.red.debug("a message")
        Colour.log("info", "a message")
        Colour.red.log("info", "a message")
        Colour.warning("a message")
        Colour.error("a message")
        Colour.critical("a message")

        # Verify all logging methods were called
        assert mock_logger.debug.call_count == 2
        assert mock_logger.log.call_count == 2
        assert mock_logger.warning.call_count == 1
        assert mock_logger.error.call_count == 1
        assert mock_logger.critical.call_count == 1


class TestLogLevelValidation:
    """Test log level validation and error handling."""

    @staticmethod
    def test_set_log_level_invalid_string() -> None:
        """Test that invalid log level strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid log level 'INVALID'"):
            Colour.set_log_level("INVALID")

    @staticmethod
    def test_set_log_level_valid_string() -> None:
        """Test that valid log level strings are accepted."""
        # These should not raise
        for level_str in ["notset", "debug", "info", "warning", "error", "critical"]:
            Colour.set_log_level(level_str)

    @staticmethod
    def test_log_method_invalid_level_string() -> None:
        """Test that Colour.log with invalid string level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log level 'invalid'"):
            Colour.log("invalid", "test message")

    @staticmethod
    def test_log_method_valid_level_strings() -> None:
        """Test that Colour.log accepts valid level strings."""
        # These should not raise
        for level_str in ["notset", "debug", "info", "warning", "error", "critical"]:
            Colour.log(level_str, "test message")

    @staticmethod
    def test_colour_member_log_invalid_level_string() -> None:
        """Test that Colour.<colour>.log with invalid string level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log level 'invalid'"):
            Colour.blue.log("invalid", "test message")

    @staticmethod
    def test_set_log_level_with_int() -> None:
        """Test that integer log levels work correctly."""
        # These should not raise
        for level_int in range(100):
            Colour.set_log_level(level_int)


class TestExtraParameterHandling:
    """Test that extra parameters passed to logging methods are preserved."""

    @staticmethod
    def test_info_preserves_extra_dict(mock_logger: Mock) -> None:
        """Test that Colour.info (static path) passes extra through unchanged and does not inject highlighter."""
        Colour.info("message", extra={"user_id": 123, "request_id": "abc"})

        call_args = mock_logger.info.call_args
        assert call_args is not None
        extra = call_args.kwargs.get("extra", {})
        assert extra.get("user_id") == 123
        assert extra.get("request_id") == "abc"
        # Static path does NOT inject highlighter — the key should be absent entirely.
        assert "highlighter" not in extra

    @staticmethod
    def test_user_overrides_extra_dict(mock_logger: Mock) -> None:
        """Test that a user-supplied highlighter overrides the instance-path default of None."""
        # Must use the instance path (Colour.blue.info) — that is where the merge
        # {"highlighter": None} | user_extra happens and user values must win.
        Colour.blue.info("message", extra={"user_id": 123, "highlighter": "changed"})

        call_args = mock_logger.info.call_args
        assert call_args is not None
        extra = call_args.kwargs.get("extra", {})
        assert extra.get("user_id") == 123
        assert extra.get("highlighter") == "changed"

    @staticmethod
    def test_coloured_info_preserves_extra_dict(mock_logger: Mock) -> None:
        """Test that Colour.<colour>.info preserves entire extra dict."""
        Colour.blue.info("message", extra={"user_id": 456})

        call_args = mock_logger.info.call_args
        assert call_args is not None
        extra = call_args.kwargs.get("extra", {})
        assert extra.get("user_id") == 456
        assert extra.get("highlighter") is None

    @staticmethod
    def test_warning_preserves_extra_dict(mock_logger: Mock) -> None:
        """Test that Colour.warning preserves entire extra dict."""
        Colour.warning("message", extra={"alert_id": "xyz"})

        call_args = mock_logger.warning.call_args
        assert call_args is not None
        extra = call_args.kwargs.get("extra", {})
        assert extra.get("alert_id") == "xyz"
        assert extra.get("highlighter") is None

    @staticmethod
    def test_error_preserves_extra_dict(mock_logger: Mock) -> None:
        """Test that Colour.error preserves entire extra dict."""
        Colour.error("message", extra={"error_code": 500})

        call_args = mock_logger.error.call_args
        assert call_args is not None
        extra = call_args.kwargs.get("extra", {})
        assert extra.get("error_code") == 500
        assert extra.get("highlighter") is None

    @staticmethod
    def test_critical_preserves_extra_dict(mock_logger: Mock) -> None:
        """Test that Colour.critical preserves entire extra dict."""
        Colour.critical("message", extra={"severity": "high"})

        call_args = mock_logger.critical.call_args
        assert call_args is not None
        extra = call_args.kwargs.get("extra", {})
        assert extra.get("severity") == "high"
        assert extra.get("highlighter") is None

    @staticmethod
    def test_log_preserves_extra_dict(mock_logger: Mock) -> None:
        """Test that Colour.log (static path) passes extra through unchanged and does not inject highlighter."""
        Colour.log("info", "message", extra={"trace_id": "123abc"})

        call_args = mock_logger.log.call_args
        assert call_args is not None
        extra = call_args.kwargs.get("extra", {})
        assert extra.get("trace_id") == "123abc"
        # Static path does NOT inject highlighter — the key should be absent entirely.
        assert "highlighter" not in extra

    @staticmethod
    def test_coloured_log_preserves_extra_dict(mock_logger: Mock) -> None:
        """Test that Colour.<colour>.log preserves entire extra dict."""
        Colour.red.log("error", "message", extra={"request_id": "789def"})

        call_args = mock_logger.log.call_args
        assert call_args is not None
        extra = call_args.kwargs.get("extra", {})
        assert extra.get("request_id") == "789def"
        assert extra.get("highlighter") is None


class TestModifyLogFormat:
    """Test the modify_log_format method."""

    @staticmethod
    def test_modify_log_format_all_options(mock_handler_class: Mock, mock_logger: Mock) -> None:
        """Test modify_log_format with all options enabled."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        mock_logger.handlers = []
        mock_logger.level = 20  # INFO level

        Colour.modify_log_format(show_level=True, show_path=True, show_time=True)

        call_kwargs = mock_handler_class.call_args.kwargs
        assert call_kwargs["show_level"] is True
        assert call_kwargs["show_path"] is True
        assert call_kwargs["show_time"] is True

    @staticmethod
    def test_modify_log_format_removes_old_handlers(mock_logger: Mock) -> None:
        """Test that modify_log_format only removes ColourHandlers."""
        old_handler1 = Mock()
        old_handler2 = Mock()
        colour_handler = ColourHandler()
        mock_logger.handlers = [colour_handler, colour_handler, old_handler1, old_handler2]
        mock_logger.level = 20  # INFO level

        Colour.modify_log_format(show_level=True)

        # Verify that both the ColourHandlers were removed, then one was re-added.
        assert mock_logger.removeHandler.call_count == 2
        mock_logger.removeHandler.assert_called_with(colour_handler)
        assert mock_logger.addHandler.call_count == 2


class TestParseLogLevel:
    """Test the _parse_log_level helper."""

    @staticmethod
    @pytest.mark.parametrize(
        ("level", "expected"),
        [
            ("debug", logging.DEBUG),
            ("INFO", logging.INFO),
            ("Warning", logging.WARNING),
            ("critical", logging.CRITICAL),
            ("notset", logging.NOTSET),
            (10, 10),
            (0, 0),
            ("10", 10),
            ("-1", -1),
        ],
    )
    def test_valid_levels(level: str | int, expected: int) -> None:
        """Test valid string, integer, and numeric-string inputs."""
        assert _parse_log_level(level) == expected

    @staticmethod
    @pytest.mark.parametrize("bad", ["INVALID", "foobar", "debu", ""])
    def test_invalid_string_raises(bad: str) -> None:
        """Test that unrecognised strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid log level"):
            _parse_log_level(bad)

    @staticmethod
    def test_deprecated_warn_alias_is_valid() -> None:
        """Test that 'warn' is accepted because deprecated logging.WARN exists."""
        assert _parse_log_level("warn") == logging.WARNING

    @staticmethod
    def test_error_message_lists_standard_level_names() -> None:
        """Test that the ValueError message contains all standard level names."""
        with pytest.raises(ValueError, match="Invalid log level") as exc_info:
            _parse_log_level("garbage")
        msg = str(exc_info.value)
        for name in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NOTSET"]:
            assert name in msg


class TestMaxLevelFilter:
    """Test MaxLevelFilter boundary conditions."""

    @staticmethod
    @pytest.mark.parametrize(
        ("record_level", "max_level", "expected"),
        [
            (logging.INFO, logging.WARNING, True),  # below -> pass
            (logging.WARNING, logging.WARNING, False),  # at -> block
            (logging.ERROR, logging.WARNING, False),  # above -> block
            (logging.NOTSET, logging.DEBUG, True),  # NOTSET passes any positive max
            (logging.NOTSET, 0, False),  # NOTSET blocked when max is 0
        ],
    )
    def test_filter(record_level: int, max_level: int, expected: bool) -> None:
        """Test pass/block behavior at and around max_level."""
        f = MaxLevelFilter(max_level)
        record = logging.LogRecord("test", record_level, "", 0, "msg", (), None)
        assert f.filter(record) is expected


class TestColourHandler:
    """Test ColourHandler constructor."""

    @staticmethod
    def test_defaults() -> None:
        """Test default level is NOTSET, stderr=True, and markup is enabled."""
        h = ColourHandler()
        assert h.level == logging.NOTSET
        assert h.console.stderr is True
        assert h.markup is True

    @staticmethod
    def test_custom_level_and_stderr_flag() -> None:
        """Test that level and stderr flag are forwarded correctly."""
        h = ColourHandler(level=logging.ERROR, stderr=False)
        assert h.level == logging.ERROR
        assert h.console.stderr is False

    @staticmethod
    def test_show_flags_accepted() -> None:
        """Test that all show_* flag combinations construct without error."""
        ColourHandler(show_level=True, show_path=True, show_time=True)
        ColourHandler(show_level=False, show_path=False, show_time=False)


class TestEnvironmentVariables:
    """Test XANADU_COLOURS_LEVEL and XANADU_COLOURS_SPLIT env var parsing."""

    @staticmethod
    @patch.dict("os.environ", {"XANADU_COLOURS_LEVEL": "DEBUG", "XANADU_COLOURS_SPLIT": "ERROR"})
    def test_env_vars_are_parsed() -> None:
        """Test that both env vars are correctly resolved by _parse_log_level."""
        assert _parse_log_level(os.environ["XANADU_COLOURS_LEVEL"]) == logging.DEBUG
        assert _parse_log_level(os.environ["XANADU_COLOURS_SPLIT"]) == logging.ERROR

    @staticmethod
    @patch.dict("os.environ", {"XANADU_COLOURS_LEVEL": "INVALID_LEVEL"})
    def test_invalid_env_var_raises() -> None:
        """Test that an invalid env var value raises ValueError on parse."""
        with pytest.raises(ValueError, match="Invalid log level"):
            _parse_log_level(os.environ["XANADU_COLOURS_LEVEL"])


class TestModifyLogFormatDetailed:
    """Detailed tests for modify_log_format."""

    @staticmethod
    def test_creates_stdout_and_stderr_handlers(mock_handler_class: Mock, mock_logger: Mock) -> None:
        """Test that exactly two handlers with correct defaults are created and registered."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        mock_logger.handlers = []
        mock_logger.level = logging.INFO

        Colour.modify_log_format()

        assert mock_handler_class.call_count == 2
        stdout_call = mock_handler_class.call_args_list[0]
        assert stdout_call.kwargs["stderr"] is False
        assert stdout_call.kwargs["show_level"] is False
        assert stdout_call.kwargs["level"] == min(logging.INFO, logging.WARNING)
        stderr_call = mock_handler_class.call_args_list[1]
        assert stderr_call.kwargs["stderr"] is True
        assert stderr_call.kwargs["level"] == logging.WARNING
        assert mock_logger.addHandler.call_count == 2

    @staticmethod
    @pytest.mark.parametrize(
        ("logger_level", "split_level", "expected_stdout_level"),
        [
            (logging.ERROR, logging.WARNING, logging.WARNING),  # logger > split -> stdout gets split
            (logging.DEBUG, logging.WARNING, logging.DEBUG),  # logger < split -> stdout gets logger
        ],
    )
    def test_stdout_level_is_min_of_logger_and_split(
        mock_handler_class: Mock,
        mock_logger: Mock,
        logger_level: int,
        split_level: int,
        expected_stdout_level: int,
    ) -> None:
        """Test that stdout handler level equals min(logger.level, split_level)."""
        mock_handler_class.return_value = Mock()
        mock_logger.handlers = []
        mock_logger.level = logger_level

        Colour.modify_log_format(stdout_filter_level=split_level)

        assert mock_handler_class.call_args_list[0].kwargs["level"] == expected_stdout_level

    @staticmethod
    def test_filter_level_as_string(mock_handler_class: Mock, mock_logger: Mock) -> None:
        """Test that stdout_filter_level accepts string level names."""
        mock_handler_class.return_value = Mock()
        mock_logger.handlers = []
        mock_logger.level = logging.INFO

        Colour.modify_log_format(stdout_filter_level="error")

        assert mock_handler_class.call_args_list[1].kwargs["level"] == logging.ERROR

    @staticmethod
    def test_invalid_filter_level_raises(mock_logger: Mock) -> None:
        """Test that an invalid stdout_filter_level raises ValueError."""
        mock_logger.handlers = []
        mock_logger.level = logging.INFO
        with pytest.raises(ValueError, match="Invalid log level"):
            Colour.modify_log_format(stdout_filter_level="not_a_level")

    @staticmethod
    def test_stdout_handler_gets_max_level_filter(mock_handler_class: Mock, mock_logger: Mock) -> None:
        """Test that the stdout handler receives a MaxLevelFilter matching the split level."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler
        mock_logger.handlers = []
        mock_logger.level = logging.INFO

        Colour.modify_log_format(stdout_filter_level=logging.ERROR)

        mock_handler.addFilter.assert_called_once()
        added = mock_handler.addFilter.call_args[0][0]
        assert isinstance(added, MaxLevelFilter)
        assert added.max_level == logging.ERROR

    @staticmethod
    def test_show_flags_forwarded_to_both_handlers(mock_handler_class: Mock, mock_logger: Mock) -> None:
        """Test that show_level/path/time flags are forwarded to both stdout and stderr handlers."""
        mock_handler_class.return_value = Mock()
        mock_logger.handlers = []
        mock_logger.level = logging.INFO

        Colour.modify_log_format(show_level=True, show_path=True, show_time=True)

        for call in mock_handler_class.call_args_list:
            assert call.kwargs["show_level"] is True
            assert call.kwargs["show_path"] is True
            assert call.kwargs["show_time"] is True

    @staticmethod
    def test_only_colour_handlers_removed(mock_logger: Mock) -> None:
        """Test that non-ColourHandler handlers survive the format change."""
        foreign = logging.StreamHandler()
        colour = ColourHandler()
        mock_logger.handlers = [foreign, colour]
        mock_logger.level = logging.INFO

        Colour.modify_log_format()

        mock_logger.removeHandler.assert_called_once_with(colour)


class TestColourEnumMembers:
    """Test Colour enum member values and structure."""

    @staticmethod
    @pytest.mark.parametrize(
        ("member", "expected_value"),
        [
            ("red", "red"),
            ("orange", "orange1"),
            ("yellow", "yellow"),
            ("green", "green"),
            ("blue", "deep_sky_blue1"),
            ("purple", "magenta"),
            ("default", "default"),
            ("italic", "italic"),
            ("RED", "bold red"),
            ("ORANGE", "bold orange1"),
            ("YELLOW", "bold yellow"),
            ("GREEN", "bold green"),
            ("BLUE", "bold deep_sky_blue1"),
            ("PURPLE", "bold magenta"),
            ("DEFAULT", "bold default"),
            ("BOLD", "bold default"),
            ("ITALIC", "bold italic"),
        ],
    )
    def test_member_values(member: str, expected_value: str) -> None:
        """Test each enum member has the correct Rich markup value."""
        assert Colour[member].value == expected_value

    @staticmethod
    def test_member_count() -> None:
        """Test the total number of unique enum members (BOLD aliases DEFAULT, plus logger)."""
        assert len(set(Colour.__members__.values())) == 17

    @staticmethod
    def test_logger_attribute() -> None:
        """Test that Colour.logger is an enum member whose value is the module LOGGER."""
        assert isinstance(Colour.logger, Colour)
        assert Colour.logger.value is LOGGER


class TestCallEdgeCases:
    """Test __call__ with non-standard argument types."""

    @staticmethod
    @pytest.mark.parametrize("value", [None, 42, 1.23, True, [1, 2, 3]])
    def test_call_with_non_string(value: object) -> None:
        """Test that __call__ uses str() on any value."""
        assert Colour.red(value) == f"[red]{value}[/red]"

    @staticmethod
    def test_call_with_empty_string() -> None:
        """Test that empty string produces empty-content tags."""
        assert Colour.red("") == "[red][/red]"

    @staticmethod
    def test_call_with_nested_colour_tags() -> None:
        """Test that nested colour tags are preserved verbatim."""
        inner = Colour.blue("inner")
        assert Colour.red(inner) == "[red][deep_sky_blue1]inner[/deep_sky_blue1][/red]"


class TestRedErrorEdgeCases:
    """Test red_error edge cases beyond the baseline TestUtils coverage."""

    @staticmethod
    def test_no_error_in_string() -> None:
        """Test that strings without error patterns are returned unchanged."""
        text = "Everything is fine."
        assert Colour.red_error(text) == text

    @staticmethod
    def test_multiple_errors_and_colon() -> None:
        """Test multiple error words and the error-with-colon pattern."""
        result = Colour.red_error("TypeError and ValueError: bad input")
        assert "[bold red]TypeError[/bold red]" in result
        assert "[bold red]ValueError:[/bold red]" in result

    @staticmethod
    def test_error_substring() -> None:
        """Test that words containing 'error' as a substring are matched."""
        assert "[bold red]MyCustomErrorHandler[/bold red]" in Colour.red_error("MyCustomErrorHandler")

    @staticmethod
    def test_empty_string() -> None:
        """Test that empty string returns empty string."""
        assert Colour.red_error("") == ""  # noqa: PLC1901


class TestWarningErrorCriticalBehavior:
    """Test colouring, arg forwarding, and level-gating for warning/error/critical."""

    @staticmethod
    @pytest.mark.parametrize(
        ("method", "log_attr"),
        [("warning", "warning"), ("error", "error"), ("critical", "critical")],
    )
    def test_disabled_when_level_not_enabled(mock_logger: Mock, method: str, log_attr: str) -> None:
        """Test that no log call is made when the level is disabled."""
        mock_logger.isEnabledFor.return_value = False
        getattr(Colour, method)("msg")
        getattr(mock_logger, log_attr).assert_not_called()

    @staticmethod
    def test_warning_wraps_orange_and_forwards_args(mock_logger: Mock) -> None:
        """Test warning wraps in orange and forwards positional args and exc_info."""
        Colour.warning("Houston, we have a %s", "problem", exc_info=True)
        args, kwargs = mock_logger.warning.call_args
        assert args[0] == "[orange1]Houston, we have a %s[/orange1]"
        assert args[1] == "problem"
        assert kwargs["exc_info"] is True

    @staticmethod
    def test_error_wraps_red_with_error_highlight(mock_logger: Mock) -> None:
        """Test error wraps in red and applies bold-red highlighting to error words."""
        Colour.error("MyError happened")
        msg = mock_logger.error.call_args[0][0]
        assert "[red]" in msg
        assert "[bold red]MyError[/bold red]" in msg

    @staticmethod
    def test_error_without_error_word(mock_logger: Mock) -> None:
        """Test error wrapping when the message contains no error-pattern word."""
        Colour.error("something failed")
        assert mock_logger.error.call_args[0][0] == "[red]something failed[/red]"

    @staticmethod
    def test_critical_wraps_bold_red(mock_logger: Mock) -> None:
        """Test critical wraps in bold red."""
        Colour.critical("system down")
        assert mock_logger.critical.call_args[0][0] == "[bold red]system down[/bold red]"


class TestLogWithIntegerLevel:
    """Test Colour.log and instance .log with integer levels."""

    @staticmethod
    def test_log_static_with_int(mock_logger: Mock) -> None:
        """Test Colour.log passes an integer level directly to LOGGER.log."""
        Colour.log(logging.WARNING, "message")
        mock_logger.log.assert_called_once_with(logging.WARNING, "message")

    @staticmethod
    def test_log_member_with_int(mock_logger: Mock) -> None:
        """Test instance .log wraps the message and passes the integer level."""
        Colour.green.log(logging.ERROR, "msg")
        mock_logger.log.assert_called_once_with(logging.ERROR, "[green]msg[/green]", extra={"highlighter": None})


class TestPrintDescriptorBehavior:
    """Test _PrintDescriptor static vs instance dispatch."""

    @staticmethod
    def test_static_print_is_rich_print(mock_print: Mock) -> None:
        """Test that Colour.print is rich_print itself, not a wrapper."""
        assert Colour.print is mock_print


class TestLogForwardingWithMultipleArgs:
    """Test that format-string args are forwarded to the logger without modification."""

    @staticmethod
    def test_info_static_with_format_args(mock_logger: Mock) -> None:
        """Test Colour.info forwards format args untouched."""
        Colour.info("count: %d, name: %s", 42, "test")
        mock_logger.info.assert_called_once_with("count: %d, name: %s", 42, "test")

    @staticmethod
    def test_info_member_with_format_args(mock_logger: Mock) -> None:
        """Test instance .info wraps only the message string, not the format args."""
        Colour.red.info("count: %d", 42)
        assert mock_logger.info.call_args[0] == ("[red]count: %d[/red]", 42)

    @staticmethod
    def test_log_member_with_format_args(mock_logger: Mock) -> None:
        """Test instance .log wraps message and forwards level and format args."""
        Colour.blue.log("warning", "count: %d", 5)
        assert mock_logger.log.call_args[0] == (logging.WARNING, "[deep_sky_blue1]count: %d[/deep_sky_blue1]", 5)


class TestSetLogLevel:
    """Test that Colour.set_log_level correctly mutates the LOGGER level."""

    @staticmethod
    def test_default_resets_to_info() -> None:
        """Test that calling with no args sets the level to INFO."""
        Colour.set_log_level(logging.CRITICAL)
        Colour.set_log_level()
        assert LOGGER.level == logging.INFO

    @staticmethod
    def test_string_and_int_levels_take_effect() -> None:
        """Test that string and integer levels are each applied to the logger."""
        Colour.set_log_level("debug")
        assert LOGGER.level == logging.DEBUG
        Colour.set_log_level(42)
        assert LOGGER.level == 42
        Colour.set_log_level()  # reset


class TestLoggerInitialization:
    """Test the logger state established at import time."""

    @staticmethod
    def test_logger_identity_and_propagation() -> None:
        """Test logger name and that propagation is disabled."""
        assert LOGGER.name == "xanadu.colours"
        assert LOGGER.propagate is False

    @staticmethod
    def test_has_stdout_and_stderr_colour_handlers() -> None:
        """Test that at least one stdout and one stderr ColourHandler are attached."""
        colour_handlers = [h for h in LOGGER.handlers if isinstance(h, ColourHandler)]
        assert any(not h.console.stderr for h in colour_handlers), "No stdout ColourHandler found"
        assert any(h.console.stderr for h in colour_handlers), "No stderr ColourHandler found"

    @staticmethod
    def test_stdout_handler_has_max_level_filter() -> None:
        """Test that the stdout handler has exactly one MaxLevelFilter."""
        stdout = next(h for h in LOGGER.handlers if isinstance(h, ColourHandler) and not h.console.stderr)
        assert len([f for f in stdout.filters if isinstance(f, MaxLevelFilter)]) == 1

    @staticmethod
    def test_all_exports() -> None:
        """Test that __all__ declares exactly the expected public names."""
        import colours  # noqa: PLC0415

        assert set(colours.__all__) == {"LOGGER", "Color", "Colour", "ColourHandler"}


class TestExtraParameterEdgeCases:
    """Test highlighter injection and user-extra merging across all logging paths."""

    @staticmethod
    def test_static_path_does_not_inject_extra(mock_logger: Mock) -> None:
        """Test that Colour.info (static path) passes no extra kwarg to the logger."""
        Colour.info("msg")
        assert "extra" not in mock_logger.info.call_args.kwargs

    @staticmethod
    def test_member_path_injects_highlighter(mock_logger: Mock) -> None:
        """Test that instance .info injects extra={'highlighter': None}."""
        Colour.red.info("msg")
        assert mock_logger.info.call_args.kwargs["extra"] == {"highlighter": None}

    @staticmethod
    def test_warning_error_critical_inject_highlighter(mock_logger: Mock) -> None:
        """Test that warning/error/critical each inject highlighter=None."""
        Colour.warning("w")
        assert mock_logger.warning.call_args.kwargs["extra"]["highlighter"] is None
        Colour.error("e")
        assert mock_logger.error.call_args.kwargs["extra"]["highlighter"] is None
        Colour.critical("c")
        assert mock_logger.critical.call_args.kwargs["extra"]["highlighter"] is None

    @staticmethod
    def test_user_extra_is_merged_and_highlighter_defaults_to_none(mock_logger: Mock) -> None:
        """Test that user extra keys are preserved alongside the default highlighter."""
        Colour.warning("msg", extra={"request_id": "abc"})
        extra = mock_logger.warning.call_args.kwargs["extra"]
        assert extra["request_id"] == "abc"
        assert extra["highlighter"] is None

    @staticmethod
    def test_user_can_override_highlighter(mock_logger: Mock) -> None:
        """Test that a user-supplied highlighter value overrides the None default."""
        Colour.warning("msg", extra={"highlighter": "custom"})
        assert mock_logger.warning.call_args.kwargs["extra"]["highlighter"] == "custom"

    @staticmethod
    @pytest.mark.usefixtures("mock_logger")
    def test_original_extra_not_mutated() -> None:
        """Test that the caller's extra dict is not modified in place."""
        original = {"key": "val"}
        snapshot = original.copy()
        Colour.warning("msg", extra=original)
        assert original == snapshot
