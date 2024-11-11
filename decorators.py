from functools import wraps
from flask import session, redirect, url_for, flash
from markupsafe import Markup
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
def login_required(custom_message=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                # Usa il messaggio personalizzato se fornito, altrimenti un messaggio di default
                message = custom_message or "Accesso non autorizzato. Effettua il login per continuare."
                flash(Markup(message), "warning")
                return redirect(url_for("accedi"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
