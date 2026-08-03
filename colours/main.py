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
import operator
import os
import re
import shutil
from collections.abc import Callable
from contextlib import suppress
from enum import Enum
from functools import wraps
from random import choice
from typing import Any, overload

from rich import print as rich_print
from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler

try:
    from rich.spinner import SPINNERS
    from rich.spinner import Spinner as rich_Spinner
except ImportError:  # pragma: no cover
    from rich._spinners import SPINNERS  # noqa: PLC2701
    from rich.spinner import Spinner as rich_Spinner

width, _ = shutil.get_terminal_size()


# region ColourHandler
class ColourHandler(RichHandler):
    """A custom instance of the RichHandler class."""

    def __init__(
        self,
        show_level: bool = True,
        show_path: bool = True,
        show_time: bool = True,
        *,
        level: int = logging.NOTSET,
        stderr: bool = True,
    ) -> None:
        super().__init__(
            level=level,
            console=Console(stderr=stderr),
            markup=True,
            show_time=show_time,
            tracebacks_code_width=int(width * 0.9),
            show_path=show_path,
            show_level=show_level,
        )


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
    """Parse a log level value and return its integer representation.

    Accepts an integer, an integer-string, or a standard logging level
    name (debug, INFO, etc.). Level names are matched case-insensitively.

    Args:
        level: An integer log level, an integer-string that can be coerced to
            an integer, or a named logging level string.

    Returns:
        The integer log level.

    Raises:
        ValueError: If *level* is a non-numeric string that does not match
            any standard logging level name.

    """
    with suppress(ValueError):
        return int(level)
    with suppress(AttributeError):
        return getattr(logging, level.upper())
    valid_levels = ", ".join([k for k, v in sorted(logging.getLevelNamesMapping().items(), key=operator.itemgetter(1))])
    msg = f"Invalid log level '{level}'. Valid levels are: {valid_levels}"
    raise ValueError(msg)


def attach_split_handlers(
    logger: logging.Logger,
    logger_level: int,
    split_level: int,
    show_level: bool = False,
    show_path: bool = False,
    show_time: bool = False,
) -> None:
    """Attach a stdout/stderr pair of ColourHandlers to *logger*.

    Records below *split_level* are routed to stdout; records at or above it
    go to stderr.  *logger_level* is used to set the stdout handler's minimum
    level to ``min(logger_level, split_level)`` so that no records are lost.

    Args:
        logger: The :class:`logging.Logger` to attach handlers to.
        logger_level: The effective level of *logger*.
        split_level: Severity threshold that splits stdout from stderr.
        show_level: Forward to :class:`ColourHandler` ``show_level``.
        show_path: Forward to :class:`ColourHandler` ``show_path``.
        show_time: Forward to :class:`ColourHandler` ``show_time``.

    """
    stdout_hndlr = ColourHandler(
        show_level=show_level,
        show_path=show_path,
        show_time=show_time,
        level=min(logger_level, split_level),
        stderr=False,
    )
    stdout_hndlr.addFilter(MaxLevelFilter(split_level))
    stderr_hndlr = ColourHandler(
        show_level=show_level,
        show_path=show_path,
        show_time=show_time,
        level=split_level,
        stderr=True,
    )
    logger.addHandler(stdout_hndlr)
    logger.addHandler(stderr_hndlr)
    logger.setLevel(logger_level)


# This library requires the RichHandler to render markup correctly.
# We configure the logger at import time to guarantee Colour logging works out-of-the-box.
# Users can adjust verbosity with Colour.set_log_level() or XANADU_COLOURS_LEVEL as needed.
XANADU_COLOURS_LEVEL = _parse_log_level(os.getenv("XANADU_COLOURS_LEVEL", logging.INFO))
XANADU_COLOURS_SPLIT = _parse_log_level(os.getenv("XANADU_COLOURS_SPLIT", logging.WARNING))
LOGGER = logging.getLogger("xanadu.colours")
LOGGER.propagate = False
attach_split_handlers(LOGGER, XANADU_COLOURS_LEVEL, XANADU_COLOURS_SPLIT)


# region Colour Descriptors
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


class _LoggerDescriptor:
    """Descriptor that returns the underlying LOGGER directly, bypassing enum member wrapping."""

    def __get__(self, instance: "Colour | None", owner: type["Colour"]) -> logging.Logger:
        """Return the module-level LOGGER regardless of access context."""
        return LOGGER


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


# region Colour Enum
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

    logger = _LoggerDescriptor()

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
        parsed = _parse_log_level(level) if isinstance(level, str) else level
        LOGGER.setLevel(parsed)
        for h in LOGGER.handlers:
            if isinstance(h, ColourHandler) and not h.console.stderr and h.level > parsed:
                h.setLevel(parsed)

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
            stdout_filter_level: severity threshold at which log records switch
                from stdout to stderr.  Records below this level go to stdout;
                records at or above it go to stderr.

        Example:
            Colour.modify_log_format(show_level=True, show_time=True)

        """
        # Remove all existing handlers
        rm_hndlrs = [handler for handler in LOGGER.handlers if isinstance(handler, ColourHandler)]
        for handler in rm_hndlrs:
            LOGGER.removeHandler(handler)

        # Add new handlers with the updated format
        filter_split = _parse_log_level(stdout_filter_level)
        attach_split_handlers(LOGGER, LOGGER.level, filter_split, show_level, show_path, show_time)


# American English alias
Color = Colour


# region Spinner
# Custom XanaduAI spinner definitions. Kept in a private registry so that
# importing ``colours`` never mutates Rich's global ``SPINNERS`` dict.
_CUSTOM_SPINNERS: dict[str, dict[str, Any]] = {
    "xanaduai": {
        "interval": 120,
        "frames": [
            "|XanaduAI    |",
            "| XanaduAI   |",
            "|  XanaduAI  |",
            "|   XanaduAI |",
            "|    XanaduAI|",
            "|   XanaduAI |",
            "|  XanaduAI  |",
            "| XanaduAI   |",
        ],
    },
    "xanaduai_ticker": {
        "interval": 100,
        "frames": [
            "|XNDU      |",
            "| XNDU     |",
            "|  XNDU    |",
            "|   XNDU   |",
            "|    XNDU  |",
            "|     XNDU |",
            "|      XNDU|",
            "|U      XND|",
            "|DU      XN|",
            "|NDU      X|",
        ],
    },
}

# Names available to this library:
# - Rich's built-ins (without the hard-to-see "toggle" spinners).
# - Custom Xanadu spinners.
SPINNER_NAMES: tuple[str, ...] = tuple(
    sorted([name for name in SPINNERS if "toggle" not in name] + list(_CUSTOM_SPINNERS)),
)


def _make_spinner(name: str, text: str, *, style: str | None, speed: float) -> "rich_Spinner":
    """Build a Rich Spinner by name, sourcing custom frames without touching Rich globals."""
    if name in _CUSTOM_SPINNERS:
        # Construct with any valid built-in name, then override frames/interval
        # from our private registry. This avoids mutating rich.spinner.SPINNERS.
        spinner = rich_Spinner("dots", text, style=style, speed=speed)
        definition = _CUSTOM_SPINNERS[name]
        spinner.name = name
        spinner.frames = list(definition["frames"])
        spinner.interval = definition["interval"]
        return spinner
    return rich_Spinner(name, text, style=style, speed=speed)


class _SpinnerContext:
    """Per-call context object for parametrised ``with Spinner(...)`` blocks."""

    __slots__ = ("_cls", "_kwargs")

    def __init__(self, cls: "_SpinnerMeta", **kwargs: Any) -> None:
        self._cls = cls
        self._kwargs = kwargs

    def __enter__(self) -> "_SpinnerMeta":
        self._cls.start(**self._kwargs)
        return self._cls

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> bool:
        self._cls.stop()
        return False


class _SpinnerMeta(type):
    """Metaclass implementing the class-level singleton spinner."""

    _live: "Live | None" = None
    _spinner: "rich_Spinner | None" = None
    # Reference count of active start()/context "enters" that own the spinner.
    _depth: int = 0

    def start(cls, msg: str = "", *, name: str | None = None, style: str | None = None, speed: float = 1.0) -> None:
        """Start or nest into the active spinner. Reuses existing if already running."""
        cls._depth += 1
        if cls._live is not None:
            if msg and cls._spinner is not None:
                cls._spinner.text = str(msg)
                Colour.debug("Spinner: %s", msg)
            return
        spinner_name = name or choice(SPINNER_NAMES)
        cls._spinner = _make_spinner(spinner_name, msg, style=style, speed=speed)
        cls._live = Live(cls._spinner, refresh_per_second=20)
        cls._live.start()
        if msg:
            Colour.debug("Spinner: %s", msg)

    def _teardown(cls) -> None:
        """Stop the Live instance and clear singleton state."""
        if cls._live is not None:
            try:
                cls._live.stop()
            finally:
                cls._live = None
                cls._spinner = None

    def stop(cls) -> None:
        """Unwind one nesting level; tears down only at the outermost stop."""
        if cls._depth > 0:
            cls._depth -= 1
        if cls._depth > 0:
            return
        cls._teardown()

    def terminate(cls) -> None:
        """Force-stop the spinner regardless of nesting depth."""
        cls._depth = 0
        cls._teardown()

    def text(cls, msg: str) -> None:
        """Set the current spinner text."""
        if cls._spinner is not None:
            cls._spinner.text = msg
            Colour.debug("Spinner: %s", msg)

    def __call__(
        cls, msg: str = "", *, name: str | None = None, style: str | None = None, speed: float = 1.0
    ) -> "_SpinnerContext":
        return _SpinnerContext(cls, msg=msg, name=name, style=style, speed=speed)

    def __enter__(cls) -> "_SpinnerMeta":
        cls.start()
        return cls

    def __exit__(cls, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> bool:
        cls.stop()
        return False


class Spinner(metaclass=_SpinnerMeta):
    """Class-level singleton spinner backed by Rich Live.

    Usage: ``Spinner.start()``/``.stop()``, ``with Spinner:``, or ``with Spinner("msg"):``.
    Starts are reference-counted; only the outermost stop tears it down. Not thread-safe.
    """
