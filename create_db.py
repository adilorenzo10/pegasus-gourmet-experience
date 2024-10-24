from database import engine, Base
from models import Utente, Prenotazione, Tavolo, OrarioPrenotabile

# Crea tutte le tabelle nel database
Base.metadata.create_all(bind=engine)
