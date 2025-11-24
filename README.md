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

- **Enum-based API**: Clean, type-safe colour definitions
- **Multiple colour options**: red, orange, yellow, green, blue, purple
- **Bold variants**: Uppercase enum values provide bold styling
- **Flexible printing**: Multiple ways to apply colours to text
- **Utility functions**: Error highlighting and ANSI escape sequence removal
- **Rich integration**: Leverages Rich's powerful terminal formatting

## Usage

### Basic Usage

```python
from colours import Colour

# Use as a callable to wrap text in colour tags
Colour.print(Colour.red("This is red text"), Colour.GREEN("This is bold green text"))

# Use the print method, mix coloured arguments
Colour.blue.print("This is blue text", Colour.YELLOW("with bold yellow text"))

# Note: if the base print is a BOLD colour, the mixed colours will also be BOLD, even if it isn't specified.
Colour.PURPLE.print("This is bold purple text", Colour.orange("with bold orange text"))
```

### Available Colours

**Normal colours:**
- `Colour.red`
- `Colour.orange`
- `Colour.yellow`
- `Colour.green`
- `Colour.blue`
- `Colour.purple`
- `Colour.default`

**Bold colours (uppercase):**
- `Colour.RED`
- `Colour.ORANGE`
- `Colour.YELLOW`
- `Colour.GREEN`
- `Colour.BLUE`
- `Colour.PURPLE`

### Advanced Usage

```python
from colours import Colour, Color  # Both spellings supported

# Reset text to the default terminal colour value.
Colour.RED.print("BoldRedError:", Colour.default("written in the default colour, probably white or black."))

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
clrs = [c for c in Colour if "bold" not in c.value and c.value != "default"]
message = "Hello! This is a message written in cycling rainbow colours for each word.".split()
n = len(clrs)
Colour.print(*(clrs[i % n](word) for i, word in enumerate(message)))
```

## API Reference

### Colour Enum

#### Methods

- `__call__(value: Any) -> str`: Wraps the value in colour tags
- `print(*args, **kwargs)`: Prints coloured text using Rich print
- `red_error(string: str) -> str`: Static method to highlight error patterns in red
- `remove_ansi(string: str) -> str`: Static method to remove ANSI escape sequences

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
