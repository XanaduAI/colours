# Colours

An Enum wrapper around [Rich](https://github.com/Textualize/rich) colours for simplified colour formatting in Python terminal applications.

## Overview

`colours` provides an elegant Enum-based interface for adding colours to your terminal output using Rich's powerful styling capabilities. It simplifies colour formatting by providing predefined colour schemes and convenient methods for printing coloured text without overloading the builtin `print`.

## Installation

```bash
pip install colours
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
Color.print(Colour.red("This is red text"), Colour.GREEN("This is bold green text"))

# Use the print method
Colour.blue.print("This is blue text", Colour.YELLOW("with bold yellow text"))
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

# Mix coloured arguments
Colour.print(Colour.RED("Error:"), "Something went wrong")

# Highlight errors in text automatically
error_msg = "ValueError: invalid input"
highlighted = Colour.red_error(error_msg)
print(highlighted)  # "ValueError" will be highlighted in red

# Remove ANSI escape sequences
clean_text = Colour.remove_ansi(coloured_string)

# Rainbow colours
normal = [c for c in Colour if "bold" not in c.value and c.value != "default"]
for c in normal:
    c.print("Hello")
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
from colours import Colour  # British spelling
from colours import Color   # American spelling
```

## Development

### Project Structure

```
colours/
├── colours/
│   ├── __init__.py
│   └── main.py
├── pyproject.toml
└── README.md
```

### Building from Source

```bash
pip install build
python -m build
```

## Credits

Built using [Rich](https://github.com/Textualize/rich) by Textualize.
