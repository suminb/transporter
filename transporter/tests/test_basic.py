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


def test_station_mapper():
    from transporter.utils import StationMapper

    source_dict = {
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
    }

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
