from typing import Annotated

from fastapi import Path

# PostgreSQL refuses a larger integer, which would turn into a 500.
MAX_INTEGER = 2**31 - 1

DatabaseId = Annotated[int, Path(ge=1, le=MAX_INTEGER)]
