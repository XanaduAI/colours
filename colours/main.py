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
import os
import re
import shutil
from collections.abc import Callable
from contextlib import suppress
from enum import Enum
from functools import wraps
from typing import Any, overload

from rich import print as rich_print
from rich.console import Console
from rich.logging import RichHandler

width, _ = shutil.get_terminal_size()


class ColourHandler(RichHandler):
    """A custom instance of the RichHandler class."""

    def __init__(
        self,
        show_level: bool = False,
        show_path: bool = False,
        show_time: bool = False,
        *,
        level: int = logging.NOTSET,
        stderr: bool = True,
    ) -> None:
        super().__init__(
            console=Console(stderr=stderr),
            markup=True,
            show_time=show_time,
            tracebacks_code_width=int(width * 0.9),
            show_path=show_path,
            show_level=show_level,
        )
        self.setLevel(level)


class MaxLevelFilter(logging.Filter):
    """Reject log records at or above *max_level*.

    Attached to the stdout handler so that WARNING and above are never
    duplicated on stdout—they are handled exclusively by the stderr handler.
    """

    def __init__(self, max_level: int) -> None:
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        """Determine if the specified record is to be logged.

        Returns True if the record should be logged, or False otherwise.
        If deemed appropriate, the record may be modified in-place.
        """
        return record.levelno < self.max_level


def _parse_log_level(level: str | int) -> int:
    """Parse a string log level and raise ValueError if invalid.

    Args:
        level: A string log level name (e.g., 'DEBUG', 'INFO').

    Returns:
        The integer log level.

    Raises:
        ValueError: If the string level name is not a valid logging level.

    """
    with suppress(ValueError):
        return int(level)
    with suppress(AttributeError):
        return getattr(logging, level.upper())
    valid_levels = ", ".join(
        sorted(
            [name for name in dir(logging) if name.isupper() and isinstance(getattr(logging, name), int)],
            key=lambda attr: getattr(logging, attr),
        )
    )
    msg = f"Invalid log level '{level}'. Valid levels are: {valid_levels}"
    raise ValueError(msg)


# This library requires the RichHandler to render markup correctly.
# We configure the logger at import time to guarantee Colour logging works out-of-the-box.
# Users can adjust verbosity with Colour.set_log_level() or XANADU_COLOURS_LEVEL as needed.
LOGGER = logging.getLogger("xanadu.colours")
XANADU_COLOURS_LEVEL = _parse_log_level(os.getenv("XANADU_COLOURS_LEVEL", logging.INFO))
XANADU_COLOURS_SPLIT = _parse_log_level(os.getenv("XANADU_COLOURS_SPLIT", logging.WARNING))
_stdout_hndlr = ColourHandler(level=XANADU_COLOURS_LEVEL, stderr=False)
_stdout_hndlr.addFilter(MaxLevelFilter(XANADU_COLOURS_SPLIT))
_stderr_hndlr = ColourHandler(level=max(XANADU_COLOURS_LEVEL, XANADU_COLOURS_SPLIT), stderr=True)
LOGGER.addHandler(_stdout_hndlr)
LOGGER.addHandler(_stderr_hndlr)
LOGGER.setLevel(XANADU_COLOURS_LEVEL)
LOGGER.propagate = False


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

        @wraps(rich_print)
        def colour_print(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
            rich_print(*map(instance, args), **kwargs)

        return colour_print


class _PredefinedLogDescriptor:
    """Descriptor to handle both static and instance log methods for a given log level."""

    def __init__(self, level: str):
        self.level: str = level
        self.loglevel: int = _parse_log_level(level)

    @overload
    def __get__(self, instance: None, owner: type["Colour"]) -> Callable[..., None]: ...

    @overload
    def __get__(self, instance: "Colour", owner: type["Colour"]) -> Callable[..., None]: ...

    def __get__(self, instance: "Colour | None", owner: type["Colour"]) -> Callable[..., None]:
        """Return appropriate log function based on access context."""
        log_method = getattr(LOGGER, self.level)
        if instance is None:

            @wraps(log_method)
            def log_func(msg: str, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
                if LOGGER.isEnabledFor(self.loglevel):
                    log_method(msg, *args, **kwargs)

            return log_func

        @wraps(log_method)
        def log_func(msg: str, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            if LOGGER.isEnabledFor(self.loglevel):
                log_method(instance(msg), *args, **{**kwargs, "extra": {"highlighter": None} | kwargs.get("extra", {})})

        return log_func


class _VersatileLogDescriptor:
    """Descriptor for versatile log method that takes level as first argument."""

    @overload
    def __get__(self, instance: None, owner: type["Colour"]) -> Callable[..., None]: ...

    @overload
    def __get__(self, instance: "Colour", owner: type["Colour"]) -> Callable[..., None]: ...

    def __get__(self, instance: "Colour | None", owner: type["Colour"]) -> Callable[..., None]:
        """Return appropriate log function based on access context."""
        if instance is None:

            @wraps(LOGGER.log)
            def log(level: int | str, msg: str, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
                # Use instance method to get proper error handling
                loglevel: int = _parse_log_level(level) if isinstance(level, str) else level
                if LOGGER.isEnabledFor(loglevel):
                    LOGGER.log(
                        loglevel,
                        msg,
                        *args,
                        **kwargs,
                    )

            return log

        @wraps(LOGGER.log)
        def log(level: int | str, msg: str, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            loglevel: int = _parse_log_level(level) if isinstance(level, str) else level
            if LOGGER.isEnabledFor(loglevel):
                LOGGER.log(
                    loglevel,
                    instance(msg),
                    *args,
                    **{**kwargs, "extra": {"highlighter": None} | kwargs.get("extra", {})},
                )

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

    logger = LOGGER

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
        if LOGGER.isEnabledFor(logging.WARNING):
            LOGGER.warning(
                Colour.orange(msg),
                *args,
                **{**kwargs, "extra": {"highlighter": None} | kwargs.get("extra", {})},
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
        if LOGGER.isEnabledFor(logging.ERROR):
            LOGGER.error(
                Colour.red_error(Colour.red(msg)),
                *args,
                **{**kwargs, "extra": {"highlighter": None} | kwargs.get("extra", {})},
            )

    @staticmethod
    def critical(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log 'msg % args' with severity 'CRITICAL'.

        Critical logs are always displayed in BOLD RED.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        Colour.critical("Houston, we have a %s", "major disaster", exc_info=True)
        """
        if LOGGER.isEnabledFor(logging.CRITICAL):
            LOGGER.critical(
                Colour.RED(msg),
                *args,
                **{**kwargs, "extra": {"highlighter": None} | kwargs.get("extra", {})},
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
        """Set the logging level of the colours logger.

        Args:
            level: An integer log level or string name (e.g., 'DEBUG', 'INFO').
                   Defaults to logging.INFO (20).

        Raises:
            ValueError: If a string level name is not a valid logging level.

        Note:
            This affects ALL log calls library-wide and in any client code
            using the `xanadu.colours` logger. This is a global setting.

        """
        LOGGER.setLevel(_parse_log_level(level) if isinstance(level, str) else level)

    @staticmethod
    def modify_log_format(
        show_level: bool = False,
        show_path: bool = False,
        show_time: bool = False,
        *,
        stdout_filter_level: str | int = logging.WARNING,
    ) -> None:
        """Modify how the logs are displayed.

        Args:
            show_level: shows the log level (DEBUG, INFO, etc.).
            show_path: shows where the log was generated from.
            show_time: shows the local time when the log was generated.
            stdout_filter_level: set STDOUT/STDERR set the filter cuttoff.

        Example:
            Colour.modify_log_format(show_level=True, show_time=True)

        """
        # Remove all existing handlers
        rm_hndlrs = [handler for handler in LOGGER.handlers if isinstance(handler, ColourHandler)]
        for handler in rm_hndlrs:
            LOGGER.removeHandler(handler)

        # Add a new handler with the updated format
        filter_split = _parse_log_level(stdout_filter_level)
        stdout_hndlr = ColourHandler(
            show_level=show_level,
            show_path=show_path,
            show_time=show_time,
            level=min(LOGGER.level, filter_split),
            stderr=False,
        )
        stdout_hndlr.addFilter(MaxLevelFilter(filter_split))
        stderr_hndlr = ColourHandler(level=filter_split, stderr=True)
        LOGGER.addHandler(stdout_hndlr)
        LOGGER.addHandler(stderr_hndlr)


# American English alias
Color = Colour
