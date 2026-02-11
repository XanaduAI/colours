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

from unittest.mock import Mock, patch

import pytest

from colours import Color, Colour, ColourHandler


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
        """Test that Colour.info preserves entire extra dict."""
        Colour.info("message", extra={"user_id": 123, "request_id": "abc"})

        # Verify the extra dict contains both user fields and the highlighter
        call_args = mock_logger.info.call_args
        assert call_args is not None
        extra = call_args.kwargs.get("extra", {})
        assert extra.get("user_id") == 123
        assert extra.get("request_id") == "abc"
        assert extra.get("highlighter") is None

    @staticmethod
    def test_user_overrides_extra_dict(mock_logger: Mock) -> None:
        """Test that Colour.info preserves entire extra dict."""
        Colour.info("message", extra={"user_id": 123, "highlighter": "changed"})

        # Verify the extra dict contains both user fields and the highlighter
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
        """Test that Colour.log preserves entire extra dict."""
        Colour.log("info", "message", extra={"trace_id": "123abc"})

        call_args = mock_logger.log.call_args
        assert call_args is not None
        extra = call_args.kwargs.get("extra", {})
        assert extra.get("trace_id") == "123abc"
        assert extra.get("highlighter") is None

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
    @patch("colours.main.ColourHandler")
    def test_modify_log_format_all_options(mock_handler_class: Mock) -> None:
        """Test modify_log_format with all options enabled."""
        mock_handler = Mock()
        mock_handler_class.return_value = mock_handler

        Colour.modify_log_format(show_level=True, show_path=True, show_time=True)

        call_kwargs = mock_handler_class.call_args.kwargs
        assert call_kwargs["show_level"] is True
        assert call_kwargs["show_path"] is True
        assert call_kwargs["show_time"] is True

    @staticmethod
    @patch("colours.main.LOGGER")
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
        mock_logger.addHandler.assert_called_once()
