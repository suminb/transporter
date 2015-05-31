from geopy.distance import vincenty

import requests
import json

BUS_ROUTE_LIST_URL = 'http://m.bus.go.kr/mBus/bus/getBusRouteList.bms'
BUS_ROUTE_INFO_URL = 'http://m.bus.go.kr/mBus/bus/getRouteAndPos.bms'
STATION_URL = 'http://m.bus.go.kr/mBus/bus/getStationByUid.bms'

# 버스 정류장 번호로 검색
# m.bus.go.kr/mBus/bus.bms?search=01003

def auto_fetch(func):
    """A class method descriptor that calls fetch() if self.cached_data is not available."""
    def wrapper(self, *args, **kwargs):
        if self.cached_data is None:
            self.fetch()
        return func(self, *args, **kwargs)
    return wrapper


class Map(object):
    def get_nearest_station(self, latitude, longitude):
        pass


class Station(object):
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
    cached_data = None

    latitude = None
    longitude = None

    def __init__(self, id):
        self.id = id

    def fetch(self):
        resp = requests.post(STATION_URL, data=dict(arsId=self.id))
        self.cached_data = json.loads(resp.text)

        return self.cached_data

    @auto_fetch
    def get_bus_route_ids(self):
        for bus_info in self.cached_data['resultList']:
            yield bus_info['busRouteId']

    def get_distance_to(self, latitude, longitude):
        assert self.latitude is not None
        assert self.longitude is not None
        return vincenty((latitude, longitude), (self.latitude, self.longitude)).m

    @staticmethod
    def get_stations_nearby(latitude, longitude):
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
        pass



class Bus(object):
    """

    busType: 차량유형 (0:일반버스, 1:저상버스, 2:굴절버스)
    routeType: 노선 유형 (1:공항, 3:간선, 4:지선, 5:순환, 6:광역, 7:인천, 8:경기, 9:폐지, 0:공용)

    Request Example: (버스 노선 정보)

        curl 'http://m.bus.go.kr/mBus/bus/getRouteAndPos.bms' -H 'Host: m.bus.go.kr' \
        -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0'\
        -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' \
        --compressed -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8;' \
        -H 'X-Requested-With: XMLHttpRequest' -H 'Referer: http://m.bus.go.kr/mBus/nearbus.bms' \
        -H 'Cookie: WMONID=Pj5S8wTXe2x; JSESSIONID=eFsTjEaatS5rpOJ5lzkyofvYO4PF1BeaJRtuSvxXTpXCoREz6prkf17gDanTE4b3.bms-info1_servlet_engine32' \
        -H 'Connection: keep-alive' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' --data 'busRouteId=4940100'

    Example Response:

        {
            "error": {
                "errorCode": "0000",
                "errorMessage": "\uc131\uacf5"
            },
            "resultList": [
                {
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
                },
            ]
        }

    """
    cached_data = None

    def __init__(self, id):
        self.id = id

    def fetch(self):
        resp = requests.post(BUS_ROUTE_INFO_URL, data=dict(busRouteId=self.id))
        self.cached_data = json.loads(resp.text)

        return self.cached_data

    @auto_fetch
    def get_station_ids(self):
        for station_info in self.cached_data['resultList']:
            yield station_info['arsId']

    @auto_fetch
    def get_station_locations(self):
        for station_info in self.cached_data['resultList']:
            # (latitude, longitude)
            yield [float(station_info['gpsY']), float(station_info['gpsX'])]

    @auto_fetch
    def get_current_position(self):
        raise NotImplementedError()


if __name__ == '__main__':
    station = Station(47105)
    bus = Bus(4940100)
    print(list(map(int, station.get_bus_route_ids())))
    #print(list(bus.get_station_positions()))