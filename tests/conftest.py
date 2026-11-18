# Copyright 2026 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Shared test fixtures."""

import logging
from collections.abc import Generator

import pytest

from colours import colour_logger


@pytest.fixture(autouse=True)
def restore_logger() -> Generator[None, None, None]:
    """Undo any level or handler changes a test makes to the global colours logger."""
    level, handlers = colour_logger.level, colour_logger.handlers[:]
    yield
    colour_logger.setLevel(level)
    colour_logger.handlers = handlers


@pytest.fixture
def log_records() -> list[logging.LogRecord]:
    """Capture every record the colours logger emits, with the logger opened up to DEBUG."""
    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    colour_logger.setLevel(logging.DEBUG)
    colour_logger.addHandler(_Capture())
    return records
