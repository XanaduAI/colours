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

import pytest

from colours import Colour

# Test cases for ANSI escape sequence removal
ansi_test_cases = {
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
