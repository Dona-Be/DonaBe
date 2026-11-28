from typing import Annotated

from fastapi import Path

from src.domain.limits import MAX_INTEGER

DatabaseId = Annotated[int, Path(ge=1, le=MAX_INTEGER)]
