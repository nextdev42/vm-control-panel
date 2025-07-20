# app/__init__.py

from flask import Flask
from flask_bootstrap import Bootstrap

def create_app():
    app = Flask(__name__)
    Bootstrap(app)

    from app.routes import main
    app.register_blueprint(main)

    return app
