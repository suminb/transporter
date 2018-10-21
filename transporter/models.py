from collections import deque
from datetime import datetime
import json
import time

import click
from flask_sqlalchemy import SQLAlchemy
from geopy.distance import vincenty
from geopy.point import Point
from logbook import Logger
import requests
from sqlalchemy.dialects.postgresql import JSON

from transporter import create_app
from transporter.utils import store_route_info


db = SQLAlchemy()
JsonType = db.String().with_variant(JSON(), 'postgresql')

inf = float('inf')
log = Logger(__name__)

route_station_assoc = db.Table(
    'route_station_assoc',
    db.Column('route_id', db.Integer, db.ForeignKey('route.id')),
    db.Column('station_id', db.Integer, db.ForeignKey('station.id')),
    db.Column('sequence', db.Integer),
)

route_edge_assoc = db.Table(
    'route_edge_assoc',
    db.Column('route_id', db.Integer, db.ForeignKey('route.id')),
    db.Column('edge_id', db.Integer, db.ForeignKey('edge.id')),
)

# Many-to-many relationship between (transferable) routes
# route_route_assoc = db.Table(
#     'route_station_assoc',
#     db.Column('route_id1', db.Integer, db.ForeignKey('route.id')),
#     db.Column('route_id2', db.Integer, db.ForeignKey('route.id')),
#     db.Column('station_id', db.Integer, db.ForeignKey('station.id')),
# )


class Bound(object):
    """Represents a geographical bound."""
    def __init__(self, sw_latitude: float, sw_longitude: float,
                 ne_latitude: float, ne_longitude: float):
        self.sw = Point(latitude=sw_latitude, longitude=sw_longitude)
        self.ne = Point(latitude=ne_latitude, longitude=ne_longitude)

    def __contains__(self, item: Point):
        return self.sw_latitude <= item.latitude <= self.ne_latitude and \
            self.sw_longitude <= item.longitude <= self.ne_longitude


class GraphNode(object):
    data = None
    neighbor_cost_pairs = None

    def __init__(self, data):
        self.data = data
        self.neighbor_cost_pairs = []

    def add_neighbor(self, node):
        if node not in self.neighbors:
            self.neighbors.append(node)

    @property
    def neighbors(self):
        zipped = list(zip(*self.neighbor_cost_pairs))
        return zipped[0] if len(zipped) > 0 else []


class GraphNode_(object):
    id = None
    cost = None

    def __init__(self, id, cost):
        self.id = id
        self.cost = cost

    def __repr__(self):
        return u'<GraphNode {} ({})>'.format(self.id, self.cost)


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

    def serialize(self, attributes=[], excludes=[]):
        """
        Serialize an instance as a dictionary
        Copied from http://stackoverflow.com/questions/7102754/jsonify-a-sqlalchemy-result-set-in-flask

        :param attributes: Additional attributes to serialize
        """
        convert = dict()
        # add your coversions for things like datetime's
        # and what-not that aren't serializable.
        d = dict()
        for c in self.__table__.columns:
            if c.name not in excludes:
                v = getattr(self, c.name)
                if c.type in convert.keys() and v is not None:
                    try:
                        d[c.name] = convert[c.type](v)
                    except:
                        d[c.name] = "Error:  Failed to covert using ", str(convert[c.type])
                elif v is None:
                    d[c.name] = str()
                else:
                    d[c.name] = v

        for attr in attributes:
            d[attr] = getattr(self, attr)

        return d


class Map(object):
    @staticmethod
    def calculate_distance_for_all_vertices():
        """
        Phase 1:

        """
        pass

    @staticmethod
    def phase1(starting_point, radius: float, stations: list):
        """Given a starting point, find all vertices (stations) within a
        rectangular bound. Initially, all vertices have an infinite cost.
        """

        for station in stations:
            location = Point(
                latitude=station.latitude, longitude=station.longitude)
            distance = vincenty(starting_point, location).m

            if distance <= radius:
                station.cost = distance
            else:
                station.cost = inf

            yield station

    @staticmethod
    def calculate_distance_for_all_nodes(graph, starting_node_id: int):
        queue = deque()
        costs = {}

        for key, value in graph.items():
            node = value['node']
            # edges = list(value['edges'])

            if key != starting_node_id:
                node.cost = inf
                costs[key] = inf

            queue.append(key)

        # graph[starting_node_id]['node'].cost = 0
        costs[starting_node_id] = 0

        while len(queue) > 0:

            min_cost_node_id = queue[0]
            min_cost = costs[min_cost_node_id]
            for key in queue:
                if costs[key] < min_cost:
                    min_cost = costs[key]
                    min_cost_node_id = key

            print(min_cost_node_id, min_cost, queue)

            u = graph[min_cost_node_id]['node']
            try:
                queue.remove(min_cost_node_id)
            except ValueError:
                pass

            # adjacent_nodes = [graph[e[0]]['node'] for e in u['edges']]
            # adjacent_costs = [e[1] for e in u['edges']]

            # print(adjacent_nodes)

            # for v, c in zip(adjacent_nodes, adjacent_costs):
            for v_key, c in graph[u.id]['edges']:
                try:
                    v = graph[v_key]['node']
                except KeyError:
                    continue

                # if u.cost + c < v.cost:
                #     v.cost = u.cost + c

                if costs[u.id] + c < costs[v.id]:
                    costs[v.id] = costs[u.id] + c
                print(costs[u.id], c, costs[v.id])

        print(costs)


class Station(db.Model, CRUDMixin):
    """

    Request Example: (정류장을 거쳐가는 버스 정보)

        curl 'http://m.bus.go.kr/mBus/bus/getStationByUid.bms'
         -H 'Host: m.bus.go.kr' \
         -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0' \
         -H 'Accept: application/json, text/javascript, */*; q=0.01' \
         -H 'Accept-Language: en-US,en;q=0.5' \
         -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8;' \
         -H 'X-Requested-With: XMLHttpRequest' -H 'Referer: http://m.bus.go.kr/mBus/nearbus.bms' \
         -H 'Cookie: WMONID=Pj5S8wTXe2x; JSESSIONID=eFsTjEaatS5rpOJ5lzkyofvYO4PF1BeaJRtuSvxXTpXCoREz6prkf17gDanTE4b3.bms-info1_servlet_engine32' \
         -H 'Connection: keep-alive' -H 'Pragma: no-cache' \
         -H 'Cache-Control: no-cache' --data 'arsId=47105'

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

    routes = db.relationship(
        'Route', secondary=route_station_assoc, backref='station',
        lazy='dynamic')

    def __init__(self, id: int, number: str, name: str, latitude: float,
                 longitude: float):
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

    def __repr__(self):
        return u'<Station: {}>'.format(self.name)

    @property
    def edges(self):
        """NOTE: This is a temporary solution."""
        return Edge.query.filter(Edge.start == self.id).all()

    def fetch(self):
        from transporter.bus import STATION_URL
        resp = requests.post(STATION_URL, data=dict(arsId=self.id))
        return json.loads(resp.text)

    def get_distance_to(self, latitude, longitude):
        assert self.latitude is not None
        assert self.longitude is not None
        return vincenty(
            (latitude, longitude), (self.latitude, self.longitude)).m

    def calculate_distance_to_stations(self, stations: list):
        """Calculate the distance from a particular station to each station in
        the list.
        """
        for station in stations:
            import pdb; pdb.set_trace()

    @staticmethod
    def get_stations_in_bound(sw_latitude: float, sw_longitude: float,
                              ne_latitude: float, ne_longitude: float):
        # Pathological case:
        # SW = (0, 350), NE = (10, 10)
        return Station.query \
            .filter(sw_latitude <= Station.latitude) \
            .filter(Station.latitude <= ne_latitude) \
            .filter(sw_longitude <= Station.longitude) \
            .filter(Station.longitude <= ne_longitude)


class Edge(db.Model, CRUDMixin):
    """Connects two nodes (stations)."""

    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.Integer, db.ForeignKey('station.id'))
    end = db.Column(db.Integer, db.ForeignKey('station.id'))
    average_time = db.Column(db.Integer)

    def __repr__(self):
        return u'<Edge {} -> {}>'.format(self.start, self.end)


class Route(db.Model, CRUDMixin):
    """A collection of nodes (stations) and edges."""

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String)

    #: Route type
    type = db.Column(db.Integer)

    #: Many-to-many relationship between route and station
    stations = db.relationship(
        'Station', secondary=route_station_assoc, backref='route',
        lazy='dynamic')

    edges = db.relationship(
        'Edge', secondary=route_edge_assoc, backref='route', lazy='dynamic')

    raw = db.Column(JsonType)


@click.group()
def cli():
    pass


@cli.command()
def gdb():
    app = create_app(__name__)
    with app.app_context():
        import pdb
        pdb.set_trace()
        pass


@cli.command()
def create_db():
    """Create an empty database and tables."""
    app = create_app(__name__)
    with app.app_context():
        db.create_all()


@cli.command()
@click.argument('route_id', type=int)
def fetch_route(route_id):
    app = create_app(__name__)
    with app.app_context():
        store_route_info(route_id)


@cli.command()
def test():
    app = create_app(__name__)
    with app.app_context():
        # stations_in_boundary = Station.get_stations_in_bound(37.482436, 127.017697, 37.520295, 127.062329).all()
        #
        # stations = Map.phase1(starting_point=Point(37.497793, 127.027611), radius=500, stations=stations_in_boundary)
        #
        # # for station in stations_in_boundary:
        # #     if station.cost == float('inf'):
        # #         print(station, station.edges)
        #
        # graph = Map.build_graph(stations)
        # Map.calculate_distance_for_all_nodes(graph, 2559)

        print(list(Station.get(5378).get_bus_route_ids()))


@cli.command()
def fetch_all_routes():
    app = create_app(__name__)
    with app.app_context():
        for route_id in range(3014600, 3015000, 100):
            log.info('Fetching route {}...'.format(route_id))
            try:
                store_route_info(route_id)
            except:
                time.sleep(10)


if __name__ == '__main__':
    cli()
