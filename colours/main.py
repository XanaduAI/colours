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

import logging
import logging.config
import re
import shutil
from collections.abc import Callable
from enum import Enum
from typing import Any, overload

from rich import print as rich_print
from rich.logging import RichHandler

width, _ = shutil.get_terminal_size(fallback=(128, 32))


class ColourHandler(RichHandler):
    """A custom instance of the RichHandler class."""

    def __init__(self) -> None:
        super().__init__(
            show_time=False,
            tracebacks_code_width=int(width * 0.9),
            markup=True,
            show_path=False,
            show_level=False,
        )


config: dict[str, Any] = {
    "loggers": {
        "colours": {
            "level": logging.INFO,
            "handlers": ["colours"],
            "propagate": False,
        }
    },
    "handlers": {
        "colours": {
            "()": ColourHandler,
        }
    },
    "version": 1,
    "disable_existing_loggers": False,
}
logging.config.dictConfig(config)
colour_logger = logging.getLogger("colours")


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
            return lambda *args, **kwargs: rich_print(*args, **kwargs)  # noqa: PLW0108
        return lambda *args, **kwargs: rich_print(*map(instance, args), **kwargs)


class _PredefinedLogDescriptor:
    """Descriptor to handle both static and instance log methods for a given log level."""

    def __init__(self, level: str):
        self.level = level

    @overload
    def __get__(self, instance: None, owner: type["Colour"]) -> Callable[..., None]: ...

    @overload
    def __get__(self, instance: "Colour", owner: type["Colour"]) -> Callable[..., None]: ...

    def __get__(self, instance: "Colour | None", owner: type["Colour"]) -> Callable[..., None]:
        """Return appropriate log function based on access context."""
        log_method = getattr(colour_logger, self.level)
        if instance is None:
            return lambda *args, **kwargs: log_method(*args, **kwargs)  # noqa: PLW0108
        return lambda *args, **kwargs: log_method(
            *map(instance, args),
            **({"extra": {"highlighter": None} | kwargs.pop("extra", {})} | kwargs),
        )


class _VersatileLogDescriptor:
    """Descriptor for versatile log method that takes level as first argument."""

    @overload
    def __get__(self, instance: None, owner: type["Colour"]) -> Callable[..., None]: ...

    @overload
    def __get__(self, instance: "Colour", owner: type["Colour"]) -> Callable[..., None]: ...

    def __get__(self, instance: "Colour | None", owner: type["Colour"]) -> Callable[..., None]:
        """Return appropriate log function based on access context."""
        if instance is None:
            return lambda level, *args, **kwargs: colour_logger.log(
                getattr(logging, level.upper()) if isinstance(level, str) else level,
                *args,
                **kwargs,
            )
        return lambda level, *args, **kwargs: colour_logger.log(
            getattr(logging, level.upper()) if isinstance(level, str) else level,
            *map(instance, args),
            **({"extra": {"highlighter": None} | kwargs.pop("extra", {})} | kwargs),
        )


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
    italic = "italic"

    # BOLD colours
    RED = "bold red"
    ORANGE = "bold orange1"
    YELLOW = "bold yellow"
    GREEN = "bold green"
    BLUE = "bold deep_sky_blue1"
    PURPLE = "bold magenta"
    DEFAULT = "bold default"
    BOLD = "bold default"  # noqa: PIE796, alias
    ITALIC = "bold italic"

    def __call__(self, string: Any) -> str:
        """Return argument as a string wrapped in colour tags."""
        return f"[{self.value}]{string}[/{self.value}]"

    print = _PrintDescriptor()
    info = _PredefinedLogDescriptor("info")
    debug = _PredefinedLogDescriptor("debug")
    log = _VersatileLogDescriptor()

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
    def warning(*args: Any, **kwargs: Any) -> None:
        """Warning logs are always displayed in orange."""
        kwargs: dict = {"extra": {"highlighter": None} | kwargs.pop("extra", {})} | kwargs
        colour_logger.warning(*map(Colour.orange, args), **kwargs)

    @staticmethod
    def error(*args: Any, **kwargs: Any) -> None:
        """Error logs are always displayed in red."""
        kwargs: dict = {"extra": {"highlighter": None} | kwargs.pop("extra", {})} | kwargs
        colour_logger.error(*map(Colour.red_error, map(Colour.red, args)), **kwargs)

    @staticmethod
    def critical(*args: Any, **kwargs: Any) -> None:
        """Critical logs are always displayed in BOLD RED."""
        kwargs: dict = {"extra": {"highlighter": None} | kwargs.pop("extra", {})} | kwargs
        colour_logger.critical(*map(Colour.RED, args), **kwargs)

    @staticmethod
    def remove_ansi(string: str) -> str:
        """Remove Ansi Escape Sequences."""
        # From https://stackoverflow.com/a/14693789
        #  by https://stackoverflow.com/users/100297/martijn-pieters
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", string)


# American English alias
Color = Colour
