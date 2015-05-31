from transporter import create_app
from transporter.bus import auto_fetch
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from geopy.distance import vincenty
from datetime import datetime
import click
import requests
import json

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
    """

    Request Example: (정류장을 거쳐가는 버스 정보)

        curl 'http://m.bus.go.kr/mBus/bus/getStationByUid.bms' -H 'Host: m.bus.go.kr' \
         -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0' \
         -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' \
         --compressed -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8;' \
         -H 'X-Requested-With: XMLHttpRequest' -H 'Referer: http://m.bus.go.kr/mBus/nearbus.bms' \
         -H 'Cookie: WMONID=Pj5S8wTXe2x; JSESSIONID=eFsTjEaatS5rpOJ5lzkyofvYO4PF1BeaJRtuSvxXTpXCoREz6prkf17gDanTE4b3.bms-info1_servlet_engine32' \
         -H 'Connection: keep-alive' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' --data 'arsId=47105'

    Response Example:

        {
            "error": {
                "errorCode": "0000",
                "errorMessage": "\uc131\uacf5"
            },
            "resultList": [
                {
                    "adirection": "\uc11c\uc6b8\uc5ed",
                    "arrmsg1": "\uc6b4\ud589\uc885\ub8cc",
                    "arrmsg2": "\uc6b4\ud589\uc885\ub8cc",
                    "arsId": "47105",
                    "busRouteId": "4940100",
                    "busType1": "0",
                    "busType2": "0",
                    "firstTm": "04:30 ",
                    "gpsX": "127.12427817794831",
                    "gpsY": "37.38864576988937",
                    "isArrive1": "0",
                    "isArrive2": "0",
                    "isFullFlag1": "0",
                    "isFullFlag2": "0",
                    "isLast1": "-2",
                    "isLast2": "-2",
                    "lastTm": "23:00 ",
                    "nextBus": " ",
                    "plainNo1": "\uc11c\uc6b875\uc0ac1094",
                    "plainNo2": "\uc11c\uc6b875\uc0ac1094",
                    "posX": "211004.5",
                    "posY": "432159.5",
                    "rerdieDiv1": "1",
                    "rerdieDiv2": "1",
                    "rerideNum1": "20",
                    "rerideNum2": "5",
                    "routeType": "6",
                    "rtNm": "9401",
                    "sectNm": "\uc0c8\ub9c8\uc744\uc5f0\uc218\uc6d0\uc785\uad6c~\uc774\ub9e4\ucd0c\ud55c\uc2e0.\uc11c\ud604\uc5ed.AK",
                    "sectOrd1": "0",
                    "sectOrd2": "0",
                    "stId": "6848",
                    "stNm": "\uc774\ub9e4\ucd0c\ud55c\uc2e0.\uc11c\ud604\uc5ed.AK\ud504\ub77c\uc790",
                    "staOrd": "20",
                    "stationNm1": "\uc0c8\ub9c8\uc744\uc5f0\uc218\uc6d0\uc785\uad6c",
                    "stationNm2": "\uc911\uc559\uacf5\uc6d0.\uc0db\ubcc4\ub9c8\uc744.\ub77c\uc774\ud504\uc544\ud30c\ud2b8",
                    "stationTp": "0",
                    "term": "4",
                    "traSpd1": "0",
                    "traSpd2": "28",
                    "traTime1": "5",
                    "traTime2": "283",
                    "vehId1": "0",
                    "vehId2": "0"
                },
                ...
            ]
        }
    """
    #: Cached data
    bus_route_ids = None

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String)
    latitude = db.Column(db.Float(precision=53))
    longitude = db.Column(db.Float(precision=53))

    def __init__(self, id: int, number: str, name: str, latitude: float, longitude: float):
        """

        :param id:
        :param number: A station number or '미정차'
        :param name:
        :param latitude:
        :param longitude:
        :return:
        """
        self.id = id
        self.number = number
        self.name = name
        self.latitude = latitude
        self.longitude = longitude

    def fetch(self):
        from transporter.bus import STATION_URL
        resp = requests.post(STATION_URL, data=dict(arsId=self.id))
        return json.loads(resp.text)

    @auto_fetch(fetch, 'bus_route_ids')
    def get_bus_route_ids(self):
        for bus_info in self.cached_data['resultList']:
            yield bus_info['busRouteId']

    def get_distance_to(self, latitude, longitude):
        assert self.latitude is not None
        assert self.longitude is not None
        return vincenty((latitude, longitude), (self.latitude, self.longitude)).m

    @staticmethod
    def get_nearby_stations(latitude: float, longitude: float, radius: int=500):
        """
        Request Example:

             curl 'http://m.bus.go.kr/mBus/bus/getStationByPos.bms' -H 'Host: m.bus.go.kr' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8;' -H 'X-Requested-With: XMLHttpRequest' -H 'Referer: http://m.bus.go.kr/mBus/nearbus.bms' -H 'Cookie: WMONID=Pj5S8wTXe2x; JSESSIONID=j4msoXxp7Kb3T9EXKtcmmAOyAc9GpawnTv1VI981MuQNkpo86W8bFPGki47MCaEq.bms-info1_servlet_engine32' -H 'Connection: keep-alive' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' --data 'tmX=127.1223458&tmY=37.3988069&radius=300' | iconv -f cp949 -t utf-8 | python -m json.tool

        Response Example:

            {
                "error": {
                    "errorCode": "0000",
                    "errorMessage": "\uc131\uacf5"
                },
                "resultList": [
                    {
                        "arsId": "0",
                        "dist": "153",
                        "gpsX": "127.12347574483393",
                        "gpsY": "37.39985681895763",
                        "posX": "210931.81833",
                        "posY": "433403.53304",
                        "stationId": "52913",
                        "stationNm": "\uc544\ub984\ub9c8\uc744.\ubc29\uc544\ub2e4\ub9ac\uc0ac\uac70\ub9ac",
                        "stationTp": "0"
                    },
                    ...
                ]
            }

        """
        url = 'http://m.bus.go.kr/mBus/bus/getStationByPos.bms'
        data = dict(tmX=longitude, tmY=latitude, radius=radius)

        resp = requests.post(url, data=data)

        return json.loads(resp.text)['resultList']


class Route(object):
    @staticmethod
    def get_stations(route_id: int):
        """Get all stations belonging to a particular route."""
        url = 'http://m.bus.go.kr/mBus/bus/getRouteAndPos.bms'
        data = dict(busRouteId=route_id)

        resp = requests.post(url, data=data)

        for station_info in json.loads(resp.text)['resultList']:
            try:
                station_number = int(station_info['stationNo'])
            except ValueError:
                # `station_number` may be '미정차'
                station_number = None

            yield Station(id=station_info['station'],
                          number=station_number,
                          name=station_info['stationNm'],
                          latitude=station_info['gpsY'],
                          longitude=station_info['gpsX'])

@click.group()
def cli():
    pass


@cli.command()
def create_db():
    """Create an empty database and tables."""
    app = create_app(__name__)
    with app.app_context():
        db.create_all()


@cli.command()
def cache_stations():
    app = create_app(__name__)
    with app.app_context():
        for station in Route.get_stations(4940300):
            try:
                station.save()
            except IntegrityError:
                db.session.rollback()


if __name__ == '__main__':
    cli()