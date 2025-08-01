from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = "badilika_hii_kuwa_siri_ya_kipekee"

    from app.routes import main
    app.register_blueprint(main)

    return app
