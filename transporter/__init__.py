import os

from flask import Flask
from flask_redis import FlaskRedis


__version__ = '0.9.1'
redis_store = FlaskRedis()

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'templates')


def create_app(name=__name__, config={},
               static_folder='transporter/static',
               template_folder=template_dir):
    """NOTE: `db_uri` is only a temporary solution. It shall be replaced by
    something more robust."""
    app = Flask(name, static_folder=static_folder,
                template_folder=template_folder)
    app.secret_key = 'secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')
    app.config['REDIS_URL'] = os.environ.get('REDIS_URL')
    app.config['DEBUG'] = True

    app.config.update(config)

    redis_store.init_app(app)

    from transporter.models import db
    db.init_app(app)

    from transporter.main import main_module
    from transporter.api import api_module
    app.register_blueprint(main_module, url_prefix='/')
    app.register_blueprint(api_module, url_prefix='/api')

    return app
