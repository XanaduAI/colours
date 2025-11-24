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
"""Simplified colours for Python terminal applications."""

import re
from enum import Enum
from typing import Any

from rich import print as rich_print


class Colour(Enum):
    """Wrap and display text using Rich colours."""

    # Normal colours
    red = "red"
    orange = "orange1"
    yellow = "yellow"
    green = "green"
    blue = "deep_sky_blue1"
    purple = "magenta"
    default = "default"

    # BOLD colours
    RED = "bold red"
    ORANGE = "bold orange1"
    YELLOW = "bold yellow"
    GREEN = "bold green"
    BLUE = "bold deep_sky_blue1"
    PURPLE = "bold magenta"

    def __call__(self, value: str) -> str:
        """Return argument as a string wrapped in colour tags."""
        return f"[{self.value}]{value}[/{self.value}]"

    def print(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        """Print the arguments wrapped in colour.

        Colour.blue.print("Hello, Blue!"), or pass arguments to Rich
        print, Colour.print(Colour.RED("RedError:"), "unmodified.").
        """
        if isinstance(self, Colour):
            rich_print(*[self(arg) for arg in args], **kwargs)
        else:
            rich_print(self, *args, **kwargs)

    # Did not add @staticmethod because this should fail with colour.blue.red_error()
    def red_error(string: str, *, display: bool = False) -> str:  # noqa: N805
        """Highlight Errors in red."""
        pattern = r"(?P<err>\w*Error\w*:?)"
        replacement = r"[bold red]\g<err>[/bold red]"
        output = re.sub(pattern, replacement, string, flags=re.IGNORECASE)
        if display:
            Color.print(output)
        return output

    @staticmethod
    def remove_ansi(string: str) -> str:
        """Remove Ansi Escape Sequences."""
        # From https://stackoverflow.com/a/14693789
        #  by https://stackoverflow.com/users/100297/martijn-pieters
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", string)


# American English alias
Color = Colour
