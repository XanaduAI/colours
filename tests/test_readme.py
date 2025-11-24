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

import re
from pathlib import Path

import pytest


def test_readme_code_blocks():
    """Extract and run Python code blocks from README.md to ensure they are valid."""
    readme_path = Path(__file__).parents[1] / "README.md"
    if not readme_path.exists():
        pytest.skip("README.md not found")

    content = readme_path.read_text(encoding="utf-8")

    # Regex to find python code blocks
    code_blocks = re.findall(r"```python\n(.*?)```", content, re.DOTALL)

    for block in code_blocks:
        # Execute the code block with its own scope
        exec(block, {"__name__": "__main__"})  # noqa: S102
