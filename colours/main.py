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
from collections.abc import Callable
from enum import Enum
from typing import Any, overload

from rich import print as rich_print


class _PrintDescriptor:
    """Descriptor to handle both static and instance print methods.

    When accessed from Colour class (Colour.print), returns rich_print directly.
    When accessed from Colour instance (Colour.blue.print), returns a function
    that wraps string arguments in colour tags before printing.
    """

    @overload
    def __get__(self, instance: None, owner: type["Colour"]) -> Callable[..., None]: ...

    @overload
    def __get__(self, instance: "Colour", owner: type["Colour"]) -> Callable[..., None]: ...

    def __get__(self, instance: "Colour | None", owner: type["Colour"]) -> Callable[..., None]:
        """Return appropriate print function based on access context."""
        if instance is None:
            # Called on class: Colour.print(...)
            return rich_print

        # Called on instance: Colour.blue.print(...)
        colour: Colour = instance

        def print_colored(*args: Any, **kwargs: Any) -> None:
            rich_print(*[colour(arg) for arg in args], **kwargs)

        return print_colored


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

    def __call__(self, string: Any) -> str:
        """Return argument as a string wrapped in colour tags."""
        return f"[{self.value}]{string}[/{self.value}]"

    print = _PrintDescriptor()

    @staticmethod
    def red_error(string: str, *, display: bool = False) -> str:
        """Highlight Errors in red."""
        pattern = r"(?P<err>\w*Error\w*:?)"
        replacement = r"[bold red]\g<err>[/bold red]"
        output: str = re.sub(pattern, replacement, string, flags=re.IGNORECASE)
        if display:
            rich_print(output)
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
