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
import re
import shutil
from collections.abc import Callable
from enum import Enum
from typing import Any, overload

from rich import print as rich_print
from rich.logging import RichHandler

width, _ = shutil.get_terminal_size(fallback=(80, 32))


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


# This library requires the RichHandler to render markup correctly.
# We configure the logger at import time to guarantee Colour logging works out-of-the-box.
# Users can adjust verbosity with Colour.set_log_level() as needed.
colour_logger = logging.getLogger("xanadu.colours")
colour_logger.addHandler(ColourHandler())
colour_logger.setLevel(logging.INFO)
colour_logger.propagate = False


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
            return rich_print

        def colour_print(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
            rich_print(*map(instance, args), **kwargs)

        colour_print.__name__ = rich_print.__name__
        colour_print.__doc__ = rich_print.__doc__
        return colour_print


class _PredefinedLogDescriptor:
    """Descriptor to handle both static and instance log methods for a given log level."""

    def __init__(self, level: str):
        self.level: str = str(level)
        self.loglevel: int = getattr(logging, self.level.upper())

    @overload
    def __get__(self, instance: None, owner: type["Colour"]) -> Callable[..., None]: ...

    @overload
    def __get__(self, instance: "Colour", owner: type["Colour"]) -> Callable[..., None]: ...

    def __get__(self, instance: "Colour | None", owner: type["Colour"]) -> Callable[..., None]:
        """Return appropriate log function based on access context."""
        log_method = getattr(colour_logger, self.level)
        doc_string = f"""Log 'msg % args' with severity '{self.level.upper()}'.\n
To pass exception information, use the keyword argument exc_info with a true value, e.g.
Colour{"." + instance.value if instance is not None else ""}.{self.level}("Houston, we have a %s", "problem", exc_info=True)"""
        if instance is None:

            def log_func(msg: str, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
                if colour_logger.isEnabledFor(self.loglevel):
                    log_method(msg, *args, **kwargs)

            log_func.__name__ = self.level
            log_func.__doc__ = doc_string
            return log_func

        def log_func(msg: str, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            if colour_logger.isEnabledFor(self.loglevel):
                log_method(instance(msg), *args, **({"extra": {"highlighter": None} | kwargs.pop("extra", {})} | kwargs))

        log_func.__name__ = self.level
        log_func.__doc__ = doc_string
        return log_func


class _VersatileLogDescriptor:
    """Descriptor for versatile log method that takes level as first argument."""

    @overload
    def __get__(self, instance: None, owner: type["Colour"]) -> Callable[..., None]: ...

    @overload
    def __get__(self, instance: "Colour", owner: type["Colour"]) -> Callable[..., None]: ...

    def __get__(self, instance: "Colour | None", owner: type["Colour"]) -> Callable[..., None]:
        """Return appropriate log function based on access context."""
        doc_string = f"""Log 'msg % args' with the integer severity 'level'.\n
To pass exception information, use the keyword argument exc_info with a true value, e.g.
Colour{"." + instance.value if instance is not None else ""}.log(level, "We have a %s", "mysterious problem", exc_info=True)"""
        if instance is None:

            def log(level: int | str, msg: str, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
                loglevel: int = getattr(logging, level.upper()) if isinstance(level, str) else level
                if colour_logger.isEnabledFor(loglevel):
                    colour_logger.log(
                        loglevel,
                        msg,
                        *args,
                        **kwargs,
                    )

            log.__doc__ = doc_string
            return log

        def log(level: int | str, msg: str, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            loglevel: int = getattr(logging, level.upper()) if isinstance(level, str) else level
            if colour_logger.isEnabledFor(loglevel):
                colour_logger.log(
                    loglevel,
                    instance(msg),
                    *args,
                    **({"extra": {"highlighter": None} | kwargs.pop("extra", {})} | kwargs),
                )

        log.__doc__ = doc_string
        return log


class Colour(Enum):
    """Wrap, print, or, log text using Rich colours."""

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
    def warning(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log 'msg % args' with severity 'WARNING'.

        Warning logs are always displayed in orange.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        Colour.warning("Houston, we have a %s", "bit of a problem", exc_info=True)
        """
        if colour_logger.isEnabledFor(logging.WARNING):
            colour_logger.warning(
                Colour.orange(msg),
                *args,
                **({"extra": {"highlighter": None} | kwargs.pop("extra", {})} | kwargs),
            )

    @staticmethod
    def error(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log 'msg % args' with severity 'ERROR'.

        Error logs are always displayed in red.
        Words that contain "error" (not case sensitive) will be bolded for emphasis.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        Colour.error("Houston, we have a %s", "major problem", exc_info=True)
        """
        if colour_logger.isEnabledFor(logging.ERROR):
            colour_logger.error(
                Colour.red_error(Colour.red(msg)),
                *args,
                **({"extra": {"highlighter": None} | kwargs.pop("extra", {})} | kwargs),
            )

    @staticmethod
    def critical(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log 'msg % args' with severity 'CRITICAL'.

        Critical logs are always displayed in BOLD RED.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        Colour.critical("Houston, we have a %s", "major disaster", exc_info=True)
        """
        if colour_logger.isEnabledFor(logging.CRITICAL):
            colour_logger.critical(
                Colour.RED(msg),
                *args,
                **({"extra": {"highlighter": None} | kwargs.pop("extra", {})} | kwargs),
            )

    @staticmethod
    def remove_ansi(string: str) -> str:
        """Remove Ansi Escape Sequences."""
        # From https://stackoverflow.com/a/14693789
        #  by https://stackoverflow.com/users/100297/martijn-pieters
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", string)

    @staticmethod
    def set_log_level(level: int | str = logging.INFO) -> None:
        """Set the logging level of the colours logger."""
        level: int = getattr(logging, level.upper()) if isinstance(level, str) else level
        logging.getLogger("xanadu.colours").setLevel(level)


# American English alias
Color = Colour
