from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import settings

engine = create_engine(settings.DATABASE_URL, echo=True)

session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
