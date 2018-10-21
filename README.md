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


Auxiliary Services
==================

We need a Redis server. It is recommended to use fully-managed Redis service
for production, but it is sufficient to run a Redis server with Docker for
development purposes.

    docker run -d -p 6379:6379 -p 6380:6380 redis

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
