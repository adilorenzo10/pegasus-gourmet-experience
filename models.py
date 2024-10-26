import bcrypt
from sqlalchemy import Column, Date, Integer, String, ForeignKey, Time
from sqlalchemy.orm import relationship
from database import Base

class Utente(Base):
    __tablename__ = 'utenti'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    prenotazioni = relationship("Prenotazione", back_populates="utente")

    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


class Tavolo(Base):
    __tablename__ = 'tavoli'
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(Integer, nullable=False)

    prenotazioni = relationship("Prenotazione", back_populates="tavolo")


class Prenotazione(Base):
    __tablename__ = 'prenotazioni'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Date, nullable=False)
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
