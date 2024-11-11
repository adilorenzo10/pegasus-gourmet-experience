import re
from passlib.context import CryptContext
from sqlalchemy import Column, Date, Integer, String, ForeignKey, Time
from sqlalchemy.orm import relationship
from database import Base

# Crea un contesto di hashing usando passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Utente(Base):
    __tablename__ = 'utenti'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    cognome = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    prenotazioni = relationship("Prenotazione", back_populates="utente")

    def set_password(self, password):
        if not self.is_password_strong(password):
            raise ValueError("La password non è abbastanza robusta. Inserisci almeno 8 caratteri, una lettera maiuscola ed un numero")
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password):
        password_hash = getattr(self, 'password_hash')
        return pwd_context.verify(password, password_hash)
    
    @staticmethod
    def is_password_strong(password):
        # Verifica lunghezza e requisiti della password
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):  # Almeno una lettera maiuscola
            return False
        if not re.search(r"[0-9]", password):  # Almeno un numero
            return False
        return True
    
class Tavolo(Base):
    __tablename__ = 'tavoli'
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(Integer, nullable=False)

    prenotazioni = relationship("Prenotazione", back_populates="tavolo")

class Prenotazione(Base):
    __tablename__ = 'prenotazioni'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Date, nullable=False)
    numero_persone = Column(Integer, nullable=False)
    utente_id = Column(Integer, ForeignKey('utenti.id'))
    tavolo_id = Column(Integer, ForeignKey('tavoli.id'))
    orario_prenotabile_id = Column(Integer, ForeignKey('orari_prenotabili.id'))

    utente = relationship("Utente", back_populates="prenotazioni")
    tavolo = relationship("Tavolo", back_populates="prenotazioni")
    orario = relationship("OrarioPrenotabile", back_populates="prenotazioni")

class OrarioPrenotabile(Base):
    __tablename__ = 'orari_prenotabili'
    id = Column(Integer, primary_key=True, autoincrement=True)
    orario = Column(Time, nullable=False)

    prenotazioni = relationship("Prenotazione", back_populates="orario")
