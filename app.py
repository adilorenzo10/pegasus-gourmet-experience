from flask import Flask, render_template
from database import SessionLocal
from models import Utente, Tavolo, Prenotazione, OrarioPrenotabile
from datetime import date, time
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add_user")
def add_user():
    # Creazione di una nuova sessione
    session = SessionLocal()
    try:
        # Creare un nuovo utente
        nuovo_utente = Utente(nome="Mario Rossi", email="mario.rossi@example.com")
        nuovo_utente.set_password("password_sicura")
        
        # Aggiungere il nuovo utente al database
        session.add(nuovo_utente)
        
        # Confermare le modifiche
        session.commit()
        return "Utente aggiunto con successo!"
    except Exception as e:
        # In caso di errore, annulla la transazione
        session.rollback()
        return f"Errore durante l'inserimento: {e}"
    finally:
        # Chiudere la sessione
        session.close()