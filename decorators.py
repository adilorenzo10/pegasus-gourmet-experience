# decorators.py
from functools import wraps
from flask import session, redirect, url_for, flash
from database import SessionLocal

# Decoratore per gestire la sessione del database
def with_db_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        db_session = SessionLocal()
        try:
            return func(db_session, *args, **kwargs)
        finally:
            db_session.close()
    return wrapper


# Decoratore per proteggere le route con login richiesto
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Per favore, effettua l'accesso per visualizzare questa pagina.", "warning")
            return redirect(url_for("accedi"))
        return func(*args, **kwargs)
    return wrapper
