from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_assets import Environment, Bundle
from database import SessionLocal
from models import Utente, Tavolo, Prenotazione, OrarioPrenotabile
from datetime import date, time
import sqlite3, secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configura Flask-Assets
assets = Environment(app)

# Crea un bundle per il file Sass
scss = Bundle('scss/style.scss', filters='libsass', output='css/style.css')
assets.register('scss_all', scss)


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
            #flash("Login effettuato con successo!", "success")
            return redirect(url_for("index"))
        else:
            flash("Email o password non corretti. Riprova.", "danger")
        
        # Chiudi la sessione del database
        db_session.close()

    return render_template("accedi.html")


# Registrati
@app.route("/registrati", methods=["GET", "POST"])
def registrati():
    if request.method == "POST":
        nome_ottenuto = request.form.get("nome")
        cognome_ottenuto = request.form.get("cognome")
        email_ottenuta = request.form.get("email")
        password_ottenuta = request.form.get("password")


         # Verifica se i campi obbligatori sono vuoti
        if not all([nome_ottenuto, cognome_ottenuto, email_ottenuta, password_ottenuta]):
            flash("Tutti i campi sono obbligatori.", "warning")
            return redirect(url_for("registrati"))
        
        
        # Cerca l'utente nel database
        db_session = SessionLocal()
        utente = db_session.query(Utente).filter_by(email=email_ottenuta).first()
        if not utente:
                try:
                    nuovo_utente = Utente(nome=nome_ottenuto, cognome=cognome_ottenuto, email=email_ottenuta)
                    nuovo_utente.set_password(password_ottenuta)
                    db_session.add(nuovo_utente)        
                    db_session.commit()
                    flash("La registrazione è stata completata con successo, adesso puoi accedere al sito per effettuare una prenotazione.", "success")
                    return redirect(url_for("accedi"))
                except Exception as e:
                    db_session.rollback()
                    flash(f"Errore durante la registrazione: {e}", "danger")
                finally:
                    db_session.close()
        else:
            flash("L'email inserita è già stata utilizzata. Riprova con un'altra oppure effettua l'accesso.", "danger")

                
    return render_template("registrati.html")


# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logout effettuato con successo!", "success")
    return redirect(url_for("accedi"))
