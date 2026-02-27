from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import session


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


DB = Annotated[Session, Depends(get_db)]
