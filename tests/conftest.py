import pytest

from transporter import create_app, redis_store


@pytest.fixture(scope='function')
def app(request):
    """Session-wide test `Flask` application."""
    settings_override = {
        'TESTING': True,
        # 'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
    }
    app = create_app(__name__, config=settings_override,
                     template_folder='../templates')

    redis_store.init_app(app)

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


# @pytest.fixture(scope='session')
# def db(app, request):
#     """Session-wide test database."""
#     if os.path.exists(TESTDB_PATH):
#         os.unlink(TESTDB_PATH)
#
#     def teardown():
#         _db.drop_all()
#         os.unlink(TESTDB_PATH)
#
#     _db.app = app
#     _db.create_all()
#
#     request.addfinalizer(teardown)
#     return _db
