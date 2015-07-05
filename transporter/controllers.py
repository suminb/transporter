from flask import request, redirect
from transporter import create_app

app = create_app(__name__)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)