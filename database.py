from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MySQL database connection details
DATABASE_URL = "mysql+pymysql://root:MyN3wP4ssw0rd@localhost:3306/userauth"

# Create a database engine
engine = create_engine(DATABASE_URL)

# Create a session for interactions with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
