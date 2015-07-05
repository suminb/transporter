from datetime import datetime, timedelta
from logbook import Logger
from sqlalchemy.exc import IntegrityError
import json
import requests


log = Logger(__name__)
inf = float('inf')


class DictMapper(object):
    """A dictionary mapper that transforms a map to another."""

    source_dict = None
    target_dict = None

    def identity(self, value):
        return value

    def transform(self):
        raise NotImplementedError()

class NearestStationsMapper(DictMapper):

    def __init__(self):
        self.mapper = (
            # (source key), (target_key), (func)
            ('gpsY', 'latitude', float),
            ('gpsX', 'longitude', float),
            ('stationId', 'station_id', int),
            ('stationNm', 'station_name', self.identity),
            ('dist', 'distance_from_current_location', int),
        )

    def transform(self, source_dict: dict):
        target_dict = {}
        for source_key, target_key, func in self.mapper:
            target_dict[target_key] = func(source_dict[source_key])

        return target_dict



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
            time_diff = 3600*24

        buf.append(dict(station_id=station_info['station'],
                        time=station_info['beginTm'],
                        time_diff=time_diff))

        prev_station_info = station_info

    return buf


def fetch_route_raw(route_id: int):
    """Fetch raw JSON data for a particular route."""

    url = 'http://m.bus.go.kr/mBus/bus/getRouteAndPos.bms'
    data = dict(busRouteId=route_id)

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
            log.warn('Rejecting station {} for having a station number of zero'.format(station_info['stationNm']))
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
            log.info('Already exists: station {}'.format(station_info['stationNm']))

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
                log.info('Stored edge from {} to {}'.format(prev_station, station))
            except IntegrityError:
                db.session.rollback()
                log.info('Could not create an edge from {} to {}'.format(prev_station, station))

        prev_station = station
        prev_station_info = station_info

def build_graph(stations):

    from transporter.models import GraphNode

    graph = {}

    for station in stations:
        graph[station.id] = dict(
            node=GraphNode(station.id, inf),
            edges=set([(e.end, e.average_time) for e in station.edges])
        )

    # Filter out non-existing graph nodes
    # for key, value in graph.items():
    #     value['edges'] = filter(lambda x: x[0] in graph, value['edges'])

    return graph
