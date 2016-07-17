Installation
============

Suppose the repository has been cloned to your current working directory by
running the following command,

    git clone https://github.com/suminb/transporter.git
    cd transporter

Prepare a Python virtual environment. This is not mendatory, but it will make
things a bit easier to work with.

    virtualenv ~/.virtualenvs/transporter

Then enter the virtual environment.

    . ~/.virtualenvs/transporter/bin/activate

Install required Python packages.

    pip install -r requirements.txt

Copy `provision.sh.dist` to `provision.sh`.

    cp provision.sh.dist provision.sh

Then edit `provision.sh` to set `DB_URI` and `REDIS_URL`.

Run
===

Set up some necessary environment variables.

    . provision.sh

Run the app.

    python application.py

Then your web application will be accessible via <http://localhost:8002>. You
may change the binding address, port number and the debug mode by setting the
following environment variables.

    export HOST="0.0.0.0"
    export PORT=8002
    export DEGUG=0
