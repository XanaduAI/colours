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
"""Colour README Tests."""

import linecache
import re
from pathlib import Path

import pytest

README_PATH = Path(__file__).parents[1] / "README.md"


@pytest.mark.skipif(condition=(not README_PATH.exists()), reason="README.md not found")
def test_readme_code_blocks():
    """Extract and run Python code blocks from README.md to ensure they are valid."""
    content = README_PATH.read_text(encoding="utf-8")

    # Regex to find python code blocks
    for i, match in enumerate(re.finditer(r"```python\n(.*?)```", content, re.DOTALL), start=1):
        block = match.group(1)
        readme_line = content[: match.start()].count("\n") + 2  # line after ```python
        filename = f"README.md (block {i}, line {readme_line})"

        # Register source with linecache so tracebacks display the actual code lines
        lines = block.splitlines(keepends=True)
        linecache.cache[filename] = (len(block), None, lines, filename)

        # Execute the code block with its own scope
        exec(compile(block, filename, "exec"), {"__name__": "__main__"})  # noqa: S102
