from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Crea l'engine per collegarsi al database sqlite3
DATABASE_URL = "sqlite:///./mydatabase.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Crea la base da cui erediteranno i modelli
Base = declarative_base()

# Configura la sessione del database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
