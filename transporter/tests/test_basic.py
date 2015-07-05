from . import app


def __test_pages(app):
    testapp = app.test_client()
    pages = ('/')

    for page in pages:
        resp = testapp.get(page)
        assert resp.status_code == 200


def test_nearest_stations_mapper():
    from transporter.utils import NearestStationsMapper

    source_dict = {
        "arsId": "0",
        "dist": "153",
        "gpsX": "127.12347574483393",
        "gpsY": "37.39985681895763",
        "posX": "210931.81833",
        "posY": "433403.53304",
        "stationId": "52913",
        "stationNm": "\uc544\ub984\ub9c8\uc744.\ubc29\uc544\ub2e4\ub9ac\uc0ac\uac70\ub9ac",
        "stationTp": "0"
    }

    mapper = NearestStationsMapper()
    target_dict = mapper.transform(source_dict)

    assert 'latitude' in target_dict
    assert 'longitude' in target_dict
    assert 'ars_id' in target_dict
    assert 'station_name' in target_dict
    assert 'distance_from_current_location' in target_dict

    assert isinstance(target_dict['latitude'], float)
    assert isinstance(target_dict['longitude'], float)
    assert isinstance(target_dict['ars_id'], int)
    assert isinstance(target_dict['station_name'], str)
    assert isinstance(target_dict['distance_from_current_location'], int)


def __test_routes_for_station_mapper():
    from transporter.utils import RoutesForStationMapper

    # source = ...

    mapper = StationMapper()
    target_dict = mapper.transform(source_dict)

    assert 'route_id' in target_dict


def test_route_mapper():
    from transporter.utils import RouteMapper

    source_dict = {
        "arsId": "47171",
        "beginTm": "04:30",
        "busRouteId": "4940100",
        "busRouteNm": "9401",
        "busType": "N",
        "direction": "\uc11c\uc6b8\uc5ed",
        "existYn": "N",
        "fullSectDist": "0",
        "gpsX": "127.10610729246586",
        "gpsY": "37.34227547211239",
        "lastTm": "23:00",
        "routeType": "6",
        "sectSpd": "0",
        "sectSpdCol": "SpeedRed",
        "section": "0",
        "seq": "1",
        "station": "35680",
        "stationNm": "\uad6c\ubbf8\ub3d9\ucc28\uace0\uc9c0\uc55e",
        "stationNo": "47171",
        "transYn": "N",
        "trnstnid": "36839"
    }

    mapper = RouteMapper()
    target_dict = mapper.transform(source_dict)

    assert 'latitude' in target_dict
    assert 'longitude' in target_dict
