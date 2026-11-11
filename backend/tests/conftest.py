"""Keep unit tests on disposable local SQLite even when a developer has Neon configured."""

import os

os.environ["DATABASE_URL"] = " "
