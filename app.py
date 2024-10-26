from flask import Flask, flash, redirect, render_template, request, session, url_for
from database import SessionLocal
from models import Utente, Tavolo, Prenotazione, OrarioPrenotabile
from datetime import date, time
import sqlite3, secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


# Homepage
@app.route("/")
def index():
    return render_template("index.html")

# Accedi
@app.route("/accedi", methods=["GET", "POST"])
def accedi():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        db_session = SessionLocal()
        
        # Cerca l'utente nel database
        utente = db_session.query(Utente).filter_by(email=email).first()
        if utente and utente.check_password(password):
            # Login corretto, salva l'ID dell'utente nella sessione
            session["user_id"] = utente.id
            flash("Login effettuato con successo!", "success")
            return redirect(url_for("index"))
        else:
            flash("Email o password non corretti. Riprova.", "danger")
        
        # Chiudi la sessione del database
        db_session.close()

    return render_template("accedi.html")


# Registrati
@app.route("/registrati")
def registrati():
    return render_template("registrati.html")

# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logout effettuato con successo!", "success")
    return redirect(url_for("accedi"))


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