# Colours

An Enum wrapper around [Rich](https://github.com/Textualize/rich) colours for simplified colour formatting in Python terminal applications.

## Overview

`colours` provides an elegant Enum-based interface for adding colours to your terminal output using Rich's powerful styling capabilities. It simplifies colour formatting by providing predefined colour schemes and convenient methods for printing coloured text without overloading the builtin `print`.

## Installation

```bash
pip install git+https://github.com/XanaduAI/colours.git
```

## Requirements

- Python >= 3.10
- rich >= 13.9.4

## Features

- **Enum-based API**: Clean, type-safe colour definitions.
- **Multiple colour options**: red, orange, yellow, green, blue, purple.
- **Bold variants**: Uppercase enum values provide bold styling.
- **Italicized option**: Italics option available for italicized styling.
- **Flexible colour nesting**: Multiple ways to apply colours to text.
- **Utility functions**: Error highlighting and ANSI escape sequence removal.
- **Rich print integration**: Leverages Rich's powerful terminal formatting.
- **Rich logging integration**: Leverages Rich's log formatting to print colourful logs to the console.
- **Stdout/stderr log routing**: Messages below `WARNING` go to stdout; `WARNING` and above go to stderr.
- **Environment variable configuration**: Set `XANADU_COLOURS_LEVEL` and `XANADU_COLOURS_SPLIT` to configure logging at startup without code changes.
- **Logger access**: Direct access to the colours logger via `Colour.logger` or `from colours import LOGGER`.
    - Pre-configured with `RichHandler` and `INFO` level.
    - Can be customized for advanced usage.

## Usage

### Available Colours

**Normal colours:**
- `Colour.red`
- `Colour.orange`
- `Colour.yellow`
- `Colour.green`
- `Colour.blue`
- `Colour.purple`
- `Colour.default`
- `Colour.italic`

**Bold colours (uppercase):**
- `Colour.RED`
- `Colour.ORANGE`
- `Colour.YELLOW`
- `Colour.GREEN`
- `Colour.BLUE`
- `Colour.PURPLE`
- `Colour.DEFAULT`
- `Colour.BOLD`
- `Colour.ITALIC`

### Basic Printing

Text can be printed straight to the console using the `.print` method which can be called on either
the `Colour` class itself, or on a colour member of it.
There are also **BOLD**, _italic_, and ***bold italic*** options.
```python
from colours import Colour

# Use as a callable to wrap text in colour tags.
Colour.print(Colour.red("This is red text"), Colour.GREEN("This is bold green text"))

# Use the print method, mix coloured arguments.
Colour.blue.print("This is blue text", Colour.YELLOW("with bold yellow text"))

# Note: if the base print is a BOLD colour, the mixed colours will also be BOLD, even if it isn't specified.
Colour.PURPLE.print("This is bold purple text", Colour.orange("with bold orange text"))

# Basic BOLD, italic, and bold-italic options.
Colour.print(Colour.BOLD("This is bold text,"), Colour.italic("this is italicized,"), Colour.ITALIC("and this is BOLD and italicized."))
```

### Basic Logging

Messages can also be logged using the configured `colours` logger. Logged messages can be coloured
using the callable wrap or coloured automatically in orange, red, and bold-red when using
`Colour.warning`, `Colour.error`, and `Colour.critical` respectively. Additional customizations
can be made using the `Colour.log` method by providing the appropriate logging level.
The default logging level for the `colours` logger is set as `INFO` or `20`.

Log records are automatically routed by severity: messages below `WARNING` are written to **stdout**,
while `WARNING` and above are written to **stderr**. This threshold can be changed at startup via the
`XANADU_COLOURS_SPLIT` environment variable (see Advanced Logging).

As usual, it is best practice to use the built-in string interpolation provided by the logging
module rather than f-strings. This approach defers string formatting until it is necessary,
improving performance. If you were to use f-strings or concatenation, the string would be
constructed even if the log level is set higher than the message level, leading to unnecessary overhead.
```python
from colours import Colour

# Basic debug logging, will not display be default.
Colour.debug("This is a standard debug log with a %s.", Colour.blue("hint of blue"))

# Basic info logging.
Colour.purple.info("This is a purple info log, also with a %s.", Colour.blue("hint of blue"))

# Basic warning logging.
Colour.warning("This is an orange warning log, customized with a %s.", Colour.blue("hint of blue"))

# Basic error logging. Words that contain "error" will be bolded for emphasis.
Colour.error("Error: This is a red error log, customized with a %s.", Colour.blue("hint of blue with the nested error being bold red"))

# Basic critical logging.
Colour.critical("This is bold red critical log, customized with a %s.", Colour.blue("hint of bold blue"))
```

### Advanced Printing

```python
from colours import Colour, Color  # Both spellings supported

# Reset text to the default terminal colour value.
Colour.RED.print("BoldRedError:", Colour.default("written in the \"default\" colour, probably white or black."))

# Highlight errors in text automatically for displaying.
error_msg = "ValueError: invalid input"
highlighted = Colour.red_error(error_msg)
Color.print(highlighted)  # "ValueError" will be highlighted in red
# You can also print/display it immediately.
Colour.red_error(error_msg, display = True)

# Remove ANSI escape sequences
ansi_text = "\x1b[31mHello, Red World!\x1b[0m"
clean_text = Colour.remove_ansi(ansi_text)
assert clean_text == "Hello, Red World!" # True

# Rainbow colours
clrs = [c for c in Colour if c != Colour.logger and not any(attr in c.value for attr in ["bold", "default", "italic"])]
message = "Hello! This is a message written in cycling rainbow colours for each word.".split()
n = len(clrs)
Colour.print(*(clrs[i % n](word) for i, word in enumerate(message)))
```

### Advanced Logging

```python
from colours import Colour

# If you need to modify the logging level to increase or decrease verbosity, simply set the level like so:
Colour.set_log_level("debug")

# You can also get the logger directly and set it directly.
# Option 1: Get it yourself
import logging
colour_logger = logging.getLogger("xanadu.colours")
colour_logger.setLevel(logging.DEBUG)

# Option 2: Use exported logger
from colours import LOGGER
LOGGER.setLevel(logging.DEBUG)

# Option 3: Access logger directly from the Colour enum
Colour.logger.setLevel(logging.DEBUG)

# Any custom log can be given by using the `Colour.log` method and choosing the logging level.
value = 123
Colour.log("debug", "This is a basic debug log with a custom value: %s.", value)
Colour.blue.log(logging.DEBUG, "This is a blue debug log (logging.DEBUG == 10).")

custom_level = 11
Colour.blue.log(custom_level, "This is a blue custom_level log.")

Colour.green.log("critical", Colour.ITALIC("This is a bold italicized green critical log."))

# Logs can also be silenced by setting a higher logging level.
colour_logger.setLevel(100)
Colour.critical("Silence even critical logs.")

# Modify the display format and stdout/stderr split threshold.
# By default, records below WARNING go to stdout and WARNING+ go to stderr.
Colour.modify_log_format(show_level=True, show_time=True, stdout_filter_level=logging.ERROR)
# Now INFO/DEBUG/WARNING go to stdout, ERROR+ go to stderr.
```

The logging level and stdout/stderr split threshold can also be set **before importing** the library
via environment variables:

```bash
# Set the initial log level (default: INFO).
export XANADU_COLOURS_LEVEL=DEBUG

# Set the level at which logs switch from stdout to stderr (default: WARNING).
export XANADU_COLOURS_SPLIT=ERROR
```

## API Reference

### Colour Enum

#### Common Methods

- `__call__(value: Any) -> str`: Wraps the value in colour tags.
- `red_error(string: str) -> str`: Static method to highlight error patterns in red.
- `remove_ansi(string: str) -> str`: Static method to remove ANSI escape sequences.

#### Print Methods
- `print(*args, **kwargs)`: Prints coloured text using Rich print.

#### Logging Methods
- `debug(*args, **kwargs)`: Logs a debug statement to the console, not visible by default.
- `info(*args, **kwargs)`: Logs an info statement to the console, is visible by default.
- `warning(*args, **kwargs)`: Always logs warning statements in orange.
- `error(*args, **kwargs)`: Always logs error statements in red, highlighting with **bold** words containing `error`.
- `critical(*args, **kwargs)`: Always logs critical statements in BOLD RED.
- `log(level, *args, **kwargs)`: Flexible logging statements for additional customizations.

#### Configuration Methods
- `set_log_level(level: int | str)`: Sets the logging verbosity level globally.
- `modify_log_format(show_level, show_path, show_time, *, stdout_filter_level)`: Adjusts handler display options and the level at which logs are routed from stdout to stderr.

#### Logger Attribute
- `logger`: Direct reference to the underlying `logging.Logger` instance (`xanadu.colours`). Equivalent to `from colours import LOGGER`.

#### Environment Variables
- `XANADU_COLOURS_LEVEL`: Sets the initial log level at import time (default: `INFO`).
- `XANADU_COLOURS_SPLIT`: Sets the level at which log records switch from stdout to stderr at import time (default: `WARNING`).

## Alias

Both `Colour` and `Color` are available for your preferred spelling:

```python
from colours import Colour  # Canadian spelling
from colours import Color   # American spelling
```

## Development

### Building from Source

To build the latest version of `colours` first clone the repository through the Code tab above or
```bash
git clone https://github.com/XanaduAI/colours.git
```
We use `uv` to develop `colours`. If you do not have `uv` installed, you can follow their OS-specific instructions [here](https://docs.astral.sh/uv/getting-started/installation/).
Once you have `uv`, you can install `colours` with the following:

```bash
uv sync
```

This will install `colours` as well as all dev dependencies to a new virtual environment in `.venv`.

## Credits

Built using [Rich](https://github.com/Textualize/rich) by Textualize.
