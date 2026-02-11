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

from colours import Color, Colour

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


@pytest.mark.parametrize(("test_input", "expected_output"), test_data, ids=test_ids)
def test_remove_ansi(test_input: str, expected_output: str):
    """Test ansi removal from strings."""
    assert Colour.remove_ansi(test_input) == expected_output


def test_enum_values():
    """Test that Enum members have the correct values."""
    assert Colour.red.value == "red"
    assert Colour.RED.value == "bold red"
    assert Colour.default.value == "default"


def test_call():
    """Test that calling an Enum member wraps the string in colour tags."""
    assert Colour.red("hello") == "[red]hello[/red]"
    assert Colour.BLUE("world") == "[bold deep_sky_blue1]world[/bold deep_sky_blue1]"


@patch("colours.main.rich_print")
def test_print_member(mock_print: Mock):
    """Test printing using an Enum member."""
    Colour.green.print("success")
    mock_print.assert_called_once_with("[green]success[/green]")


@patch("colours.main.rich_print")
def test_print_static(mock_print: Mock):
    """Test printing using the class directly (acting as static print)."""
    Colour.print("plain text")
    mock_print.assert_called_once_with("plain text")


@patch("colours.main.rich_print")
def test_print_multiple_strings(mock_print: Mock):
    """Test printing with multiple string arguments."""
    Colour.blue.print("hello", "world", "test")
    mock_print.assert_called_once_with(
        "[deep_sky_blue1]hello[/deep_sky_blue1]",
        "[deep_sky_blue1]world[/deep_sky_blue1]",
        "[deep_sky_blue1]test[/deep_sky_blue1]",
    )


@patch("colours.main.rich_print")
def test_print_mixed_types(mock_print: Mock):
    """Test printing with mixed string and non-string arguments."""
    Colour.red.print("count:", 42, "status:", True, 1.234)
    mock_print.assert_called_once_with(
        "[red]count:[/red]",
        "[red]42[/red]",
        "[red]status:[/red]",
        "[red]True[/red]",
        "[red]1.234[/red]",
    )


@patch("colours.main.rich_print")
def test_print_with_kwargs(mock_print: Mock):
    """Test printing with keyword arguments."""
    Colour.yellow.print("line1", "line2", sep=" | ", end="!\n")
    mock_print.assert_called_once_with(
        "[yellow]line1[/yellow]",
        "[yellow]line2[/yellow]",
        sep=" | ",
        end="!\n",
    )


@patch("colours.main.rich_print")
def test_print_non_string_only(mock_print: Mock):
    """Test printing with only non-string arguments."""
    Colour.purple.print(123, 456, 789)
    mock_print.assert_called_once_with("[magenta]123[/magenta]", "[magenta]456[/magenta]", "[magenta]789[/magenta]")


@patch("colours.main.rich_print")
def test_print_empty_string(mock_print: Mock):
    """Test printing with empty string."""
    Colour.green.print("")
    mock_print.assert_called_once_with("[green][/green]")


@patch("colours.main.rich_print")
def test_print_static_multiple_args(mock_print: Mock):
    """Test static print with multiple arguments and kwargs."""
    Colour.print("arg1", 42, "arg2", sep=", ", end="")
    mock_print.assert_called_once_with("arg1", 42, "arg2", sep=", ", end="")


def test_red_error():
    """Test highlighting errors in red."""
    text = "This is a ValueError."
    expected = "This is a [bold red]ValueError[/bold red]."
    assert Colour.red_error(text) == expected

    text_lower = "syntax error here"
    expected_lower = "syntax [bold red]error[/bold red] here"
    assert Colour.red_error(text_lower) == expected_lower


def test_red_error_from_instance():
    """Test highlighting errors in red.

    This usecase doesn't make sense, but it is valid.
    """
    text = "This is a ValueError."
    expected = "This is a [bold red]ValueError[/bold red]."
    assert Colour.blue.red_error(text) == expected

    text_lower = "syntax error here"
    expected_lower = "syntax [bold red]error[/bold red] here"
    assert Colour.blue.red_error(text_lower) == expected_lower


@patch("colours.main.rich_print")
def test_red_error_display(mock_print: Mock):
    """Test red_error with display=True."""
    text = "Fatal Error"
    Colour.red_error(text, display=True)
    mock_print.assert_called_once_with("Fatal [bold red]Error[/bold red]")


def test_alias():
    """Test that Color is an alias for Colour."""
    assert Color is Colour


@patch("colours.main.colour_logger")
def test_debug_log_static(mock_logger: Mock):
    """Test Colour.debug logs debug messages using logger."""
    Colour.debug("debug message")
    mock_logger.debug.assert_called_once_with("debug message")


@patch("colours.main.colour_logger")
def test_debug_log_member(mock_logger: Mock):
    """Test Colour.blue.debug logs coloured debug messages."""
    Colour.blue.debug("blue debug")
    mock_logger.debug.assert_called_once_with("[deep_sky_blue1]blue debug[/deep_sky_blue1]", extra={"highlighter": None})


@patch("colours.main.colour_logger")
def test_info_log_static(mock_logger: Mock):
    """Test Colour.info logs info messages using logger."""
    Colour.info("info message")
    mock_logger.info.assert_called_once_with("info message")


@patch("colours.main.colour_logger")
def test_info_log_member(mock_logger: Mock):
    """Test Colour.blue.info logs coloured info messages."""
    Colour.blue.info("blue info")
    mock_logger.info.assert_called_once_with("[deep_sky_blue1]blue info[/deep_sky_blue1]", extra={"highlighter": None})


@patch("colours.main.colour_logger")
def test_log_static(mock_logger: Mock):
    """Test Colour.log to create messages using logger."""
    Colour.log("notset", "notset message")
    mock_logger.log.assert_called_once_with(0, "notset message")


@patch("colours.main.colour_logger")
def test_log_member(mock_logger: Mock):
    """Test Colour.blue.log to create messages using logger."""
    Colour.blue.log("critical", "blue critical")
    mock_logger.log.assert_called_once_with(50, "[deep_sky_blue1]blue critical[/deep_sky_blue1]", extra={"highlighter": None})


@patch("colours.main.colour_logger")
def test_warning_log(mock_logger: Mock):
    """Test Colour.warning logs warning messages in orange."""
    Colour.warning("warn message")
    mock_logger.warning.assert_called_once_with("[orange1]warn message[/orange1]", extra={"highlighter": None})


@patch("colours.main.colour_logger")
def test_error_log(mock_logger: Mock):
    """Test Colour.error logs error messages in red with error highlighting."""
    Colour.error("bad error")
    expected = "[red]bad [bold red]error[/bold red][/red]"
    mock_logger.error.assert_called_once_with(expected, extra={"highlighter": None})


@patch("colours.main.colour_logger")
def test_critical_log(mock_logger: Mock):
    """Test Colour.critical logs critical messages in red with critical highlighting."""
    Colour.critical("critical error")
    expected = "[bold red]critical error[/bold red]"
    mock_logger.critical.assert_called_once_with(expected, extra={"highlighter": None})
