from flask.ext.sqlalchemy import SQLAlchemy
import click

db = SQLAlchemy()


class CRUDMixin(object):
    """Copied from https://realpython.com/blog/python/python-web-applications-with-flask-part-ii/
    """  # noqa

    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    @classmethod
    def create(cls, commit=True, **kwargs):
        instance = cls(**kwargs)

        if hasattr(instance, 'timestamp') \
                and getattr(instance, 'timestamp') is None:
            instance.timestamp = datetime.utcnow()

        return instance.save(commit=commit)

    @classmethod
    def get(cls, id):
        return cls.query.get(id)

    # We will also proxy Flask-SqlAlchemy's get_or_44
    # for symmetry
    @classmethod
    def get_or_404(cls, id):
        return cls.query.get_or_404(id)

    @classmethod
    def exists(cls, **kwargs):
        row = cls.query.filter_by(**kwargs).first()
        return row is not None

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()


class Station(db.Model, CRUDMixin):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    latitude = db.Column(db.Float(precision=53))
    longitude = db.Column(db.Float(precision=53))


@click.group()
def cli():
    pass


@cli.command()
def create_db():
    """Create an empty database and tables."""
    from transporter import create_app
    app = create_app(__name__)
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    cli()