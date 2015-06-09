from . import app


def test_pages(app):
    testapp = app.test_client()
    pages = ('/')

    for page in pages:
        resp = testapp.get(page)
        assert resp.status_code == 200
