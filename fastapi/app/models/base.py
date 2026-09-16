from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

class Base(DeclarativeBase):
    pass

engine = create_engine(url=os.getenv('DB_URL'), echo=True)
session_maker = sessionmaker(bind=engine)

def get_session():
    session = session_maker()
    try: 
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
    