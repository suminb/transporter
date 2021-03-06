from datetime import datetime, timedelta
import json

from logbook import Logger
from sqlalchemy.exc import IntegrityError
import requests

from transporter import redis_store


log = Logger(__name__)
inf = float('inf')


class DictMapper(object):
    """A dictionary mapper that transforms a map to another."""

    def identity(self, value):
        return value

    def transform(self, source_dict: dict, mapper: list=None):
        target_dict = {}

        if mapper is None:
            mapper = self.mapper

        for source_key, target_key, func in mapper:
            target_dict[target_key] = func(source_dict[source_key])

        return target_dict


class NearestStationsMapper(DictMapper):

    def __init__(self):
        self.mapper = (
            # (source key), (target_key), (func)
            ('gpsY', 'latitude', float),
            ('gpsX', 'longitude', float),
            ('arsId', 'ars_id', int),
            ('stationNm', 'station_name', self.identity),
            ('dist', 'distance_from_current_location', int),
        )


class RoutesForStationMapper(DictMapper):

    def __init__(self):
        self.mapper = (
            ('busRouteId', 'route_id', int),
            ('rtNm', 'route_number', self.identity),
        )

    def transform_entry(self, source_dict: dict):
        target_dict = {}

        for source_key, target_key, func in self.mapper:
            target_dict[target_key] = func(source_dict[source_key])

        return target_dict

    def transform(self, source_dict: dict):
        target_dict = {}

        entries = source_dict['resultList']
        if entries is not None and len(entries) > 0:
            first_entry = entries[0]

            target_dict['latitude'] = first_entry['gpsY']
            target_dict['longitude'] = first_entry['gpsX']

            target_dict['entries'] = [self.transform_entry(e) for e in entries]

        return target_dict


class RouteMapper(DictMapper):

    def map_ars_id(self, ars_id: str):
        try:
            return int(ars_id)
        except ValueError:
            return None

    def transform_entry(self, source_dict: dict):
        mapper = (
            ('arsId', 'ars_id', self.map_ars_id),
            ('gpsY', 'latitude', float),
            ('gpsX', 'longitude', float),
        )
        return super(RouteMapper, self).transform(source_dict, mapper)

    def transform(self, source_dict: dict):
        target_dict = {}

        mapper = (
            ('routeType', 'route_type', int),
            ('busRouteNm', 'route_number', self.identity),
        )

        entries = source_dict['resultList']
        first_entry = entries[0]

        target_dict = super(RouteMapper, self).transform(first_entry, mapper)

        target_dict['entries'] = [self.transform_entry(e) for e in entries]

        return target_dict


def auto_fetch(url):
    def wrap(func):
        def wrapper(*args, **kwargs):
            key = '{}_{}'.format(url, args)
            data = redis_store.get(key)

            if data is None:
                log.info('Data entry for "{}" does not exist. Fetching one.'
                         .format(key))
                data = func(*args, **kwargs)
                redis_store.set(key, json.dumps(data))
            else:
                log.info('Data entry for "{}" was loaded from cache.'
                         .format(key))
                data = json.loads(data.decode('utf-8'))

            return data
        return wrapper
    return wrap


def get_nearest_stations(latitude: float, longitude: float, radius: int=300):
    """
    Request Example:

        curl 'http://m.bus.go.kr/mBus/bus/getStationByPos.bms' \
         -H 'Host: m.bus.go.kr' \
         -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0' \
         -H 'Accept: application/json, text/javascript, */*; q=0.01' \
         -H 'Accept-Language: en-US,en;q=0.5' \
         -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8;' \
         -H 'X-Requested-With: XMLHttpRequest' \
         -H 'Referer: http://m.bus.go.kr/mBus/nearbus.bms' \
         -H 'Cookie: WMONID=Pj5S8wTXe2x; JSESSIONID=j4msoXxp7Kb3T9EXKtcmmAOyAc9GpawnTv1VI981MuQNkpo86W8bFPGki47MCaEq.bms-info1_servlet_engine32' \
         -H 'Connection: keep-alive' -H 'Pragma: no-cache' \
         -H 'Cache-Control: no-cache' \
         --data 'tmX=127.1223458&tmY=37.3988069&radius=300' | iconv -f cp949 -t utf-8 | python -m json.tool  # noqa

    Response Example:

        {
            "error": {
                "errorCode": "0000",
                "errorMessage": "성공"
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
                    "stationNm": "아름마을.방아다리사거리",
                    "stationTp": "0"
                },
                ...
            ]
        }

    """
    url = 'http://m.bus.go.kr/mBus/bus/getStationByPos.bms'
    data = {'tmX': longitude, 'tmY': latitude, 'radius': radius}

    resp = requests.post(url, data=data)

    try:
        # FIXME: Handle one error at a time
        rows = json.loads(resp.text)['resultList']
    except ValueError:
        return 'Could not load data', 500

    mapper = NearestStationsMapper()

    return [mapper.transform(r) for r in rows]


@auto_fetch('http://m.bus.go.kr/mBus/bus/getStationByUid.bms')
def get_routes_for_station(ars_id):
    """Get route information that goes through a particular station."""
    station_url = 'http://m.bus.go.kr/mBus/bus/getStationByUid.bms'
    resp = requests.post(station_url, data={'arsId': ars_id})
    mapper = RoutesForStationMapper()

    return mapper.transform(json.loads(resp.text))


def get_route(route_id):
    """Given a route ID, returns route info. The route_id is not a bus number.
    """
    route_info_url = 'http://m.bus.go.kr/mBus/bus/getRouteAndPos.bms'
    resp = requests.post(route_info_url, data={'busRouteId': route_id})

    mapper = RouteMapper()

    return mapper.transform(json.loads(resp.text))


def guess_time_diff(station_info1: dict, station_info2: dict):
    time1 = datetime.strptime(station_info1['beginTm'], '%H:%M')
    time2 = datetime.strptime(station_info2['beginTm'], '%H:%M')
    time_diff = time2 - time1

    if time_diff.total_seconds() < 0:
        # Temporary workaround
        time_diff = timedelta(seconds=150)

    return time_diff.total_seconds()


def stations_with_aux_info(raw):
    buf = []
    prev_station_info = None
    for station_info in raw['resultList']:
        if prev_station_info is not None:
            time_diff = guess_time_diff(prev_station_info, station_info)
        else:
            time_diff = 3600 * 24

        buf.append({'station_id': station_info['station'],
                    'time': station_info['beginTm'],
                    'time_diff': time_diff})

        prev_station_info = station_info

    return buf


def fetch_route_raw(route_id: int):
    """Fetch raw JSON data for a particular route."""

    url = 'http://m.bus.go.kr/mBus/bus/getRouteAndPos.bms'
    data = {'busRouteId': route_id}

    resp = requests.post(url, data=data)

    return json.loads(resp.text)


def store_route_info(route_id: int):

    # In order to avoid circular import...
    from transporter.models import Edge, Station, Route, db

    raw = fetch_route_raw(route_id)

    assert len(raw['resultList']) > 0

    first_node = raw['resultList'][0]

    log.info('Fetching route info...')

    route = None
    try:
        route = Route.create(
            id=first_node['busRouteId'],
            number=first_node['busRouteNm'],
            type=first_node['routeType'],
            raw=raw,
        )
        log.info('Stored route {}'.format(route.number))

    except IntegrityError:
        db.session.rollback()
        route = Route.get(route_id)
        log.info('Already exists: route {} '.format(first_node['busRouteNm']))

    station = None
    prev_station = None
    prev_station_info = None

    for station_info in raw['resultList']:
        try:
            station_number = int(station_info['stationNo'])
        except ValueError:
            # `station_number` may be '미정차'
            station_number = None

        if station_number == 0:
            log.warn(
                'Rejecting station {0} for having a station number of zero'
                ''.format(station_info['stationNm']))
            continue

        try:
            station = Station.create(
                id=station_info['station'],
                number=station_number,
                name=station_info['stationNm'],
                latitude=station_info['gpsY'],
                longitude=station_info['gpsX'],
                commit=False
            )
            station.routes.append(route)
            db.session.commit()
            log.info('Stored station {}'.format(station))

        except IntegrityError:
            db.session.rollback()
            log.info('Already exists: station {0}'.format(
                station_info['stationNm']))

        if (prev_station is not None) and (prev_station_info is not None):
            time_diff = guess_time_diff(prev_station_info, station_info)

            try:
                edge = Edge.create(
                    start=prev_station.id,
                    end=station.id,
                    average_time=time_diff,
                    commit=False
                )
                route.edges.append(edge)
                db.session.commit()
                log.info(
                    'Stored edge from {} to {}'.format(prev_station, station))
            except IntegrityError:
                db.session.rollback()
                log.info(
                    'Could not create an edge from {} to {}'.format(
                        prev_station, station))

        prev_station = station
        prev_station_info = station_info


def build_graph(stations):

    from transporter.models import GraphNode

    graph = {}

    for station in stations:
        graph[station.id] = {
            'node': GraphNode(station.id, inf),
            'edges': set([(e.end, e.average_time) for e in station.edges])
        }

    # Filter out non-existing graph nodes
    # for key, value in graph.items():
    #     value['edges'] = filter(lambda x: x[0] in graph, value['edges'])

    return graph
