import os

from transporter import create_app


application = create_app(__name__)


if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8002))
    debug = bool(os.environ.get('DEBUG', False))
    application.run(host, port=port, debug=debug)
