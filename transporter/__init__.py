from flask import Flask
import os


def create_app(name=__name__, config={},
               static_folder='static', template_folder='templates'):
    """NOTE: `db_uri` is only a temporary solution. It shall be replaced by
    something more robust."""
    app = Flask(name, static_folder=static_folder, template_folder=template_folder)
    app.secret_key = 'secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')
    app.config['DEBUG'] = True

    app.config.update(config)

    from main import main_module
    app.register_blueprint(main_module, url_prefix='/')

    return app