import requests
import json

BUS_ROUTE_LIST_URL = 'http://m.bus.go.kr/mBus/bus/getBusRouteList.bms'
BUS_ROUTE_INFO_URL = 'http://m.bus.go.kr/mBus/bus/getRouteAndPos.bms'
STATION_URL = 'http://m.bus.go.kr/mBus/bus/getStationByUid.bms'

# 버스 정류장 번호로 검색
# m.bus.go.kr/mBus/bus.bms?search=01003

# curl 'http://m.bus.go.kr/mBus/bus/getNearRouteByPos.bms' -H 'Host: m.bus.go.kr' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8;' -H 'X-Requested-With: XMLHttpRequest' -H 'Referer: http://m.bus.go.kr/mBus/nearbusNm.bms' -H 'Cookie: WMONID=Pj5S8wTXe2x; JSESSIONID=8rzUEsHINJK1ae1JcZH2XgAqv48TqoAujnXEU7u9NjiFoY236Jh43N6rMxj768za.bms-info1_servlet_engine32; mCookie=ARSID%3A01224%3A%uCC3D%uACBD%uAD81%3A%7CARSID%3A01224%3A%uCC3D%uACBD%uAD81%3A; c_latvalue=37.388745899999996; c_longvalue=127.1223352' -H 'Connection: keep-alive' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' --data 'tmX=127.1223352&tmY=37.388745899999996&radius=300'
# curl 'http://m.bus.go.kr/mBus/bus/getArrInfoByRoute.bms' -H 'Host: m.bus.go.kr' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8;' -H 'X-Requested-With: XMLHttpRequest' -H 'Referer: http://m.bus.go.kr/mBus/bus.bms?search=01224' -H 'Cookie: WMONID=Pj5S8wTXe2x; JSESSIONID=8rzUEsHINJK1ae1JcZH2XgAqv48TqoAujnXEU7u9NjiFoY236Jh43N6rMxj768za.bms-info1_servlet_engine32; mCookie=ARSID%3A01224%3A%uCC3D%uACBD%uAD81%3A%7CARSID%3A01224%3A%uCC3D%uACBD%uAD81%3A' -H 'Connection: keep-alive' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' --data 'stId=1363&busRouteId=3015100&ord=9'
# curl 'http://m.bus.go.kr/mBus/bus/getRouteInfo.bms' -H 'Host: m.bus.go.kr' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8;' -H 'X-Requested-With: XMLHttpRequest' -H 'Referer: http://m.bus.go.kr/mBus/bus.bms?search=01224' -H 'Cookie: WMONID=Pj5S8wTXe2x; JSESSIONID=8rzUEsHINJK1ae1JcZH2XgAqv48TqoAujnXEU7u9NjiFoY236Jh43N6rMxj768za.bms-info1_servlet_engine32; mCookie=ARSID%3A01224%3A%uCC3D%uACBD%uAD81%3A%7CARSID%3A01224%3A%uCC3D%uACBD%uAD81%3A' -H 'Connection: keep-alive' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' --data 'busRouteId=3015100'
# curl 'http://m.bus.go.kr/mBus/bus/getRouteAndPos.bms' -H 'Host: m.bus.go.kr' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8;' -H 'X-Requested-With: XMLHttpRequest' -H 'Referer: http://m.bus.go.kr/mBus/nearbusNm.bms' -H 'Cookie: WMONID=Pj5S8wTXe2x; JSESSIONID=8rzUEsHINJK1ae1JcZH2XgAqv48TqoAujnXEU7u9NjiFoY236Jh43N6rMxj768za.bms-info1_servlet_engine32; mCookie=ARSID%3A01224%3A%uCC3D%uACBD%uAD81%3A%7CARSID%3A01224%3A%uCC3D%uACBD%uAD81%3A; c_latvalue=37.3887716; c_longvalue=127.1222976' -H 'Connection: keep-alive' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' --data 'busRouteId=4940100'

def auto_fetch(fetch_func, storage_var):
    def auto_fetch_inner(func):
        """A class method decorator that calls fetch() if self.cached_data is not available."""
        def wrapper(self, *args, **kwargs):
            # if self.cached_data is None:
            #     self.fetch()

            if getattr(self, storage_var) is None:
                setattr(self, storage_var, fetch_func())

            return func(self, *args, **kwargs)
        return wrapper
    return auto_fetch_inner


class Map(object):
    pass


class Bus(object):

    station_ids = None
    station_locations = None

    def __init__(self, id):
        self.id = id

    def fetch(self):
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
        resp = requests.post(BUS_ROUTE_INFO_URL, data=dict(busRouteId=self.id))
        self.cached_data = json.loads(resp.text)

        return self.cached_data

    @auto_fetch(fetch, 'station_ids')
    def get_station_ids(self):
        for station_info in self.cached_data['resultList']:
            yield station_info['arsId']

    @auto_fetch(fetch, 'station_locations')
    def get_station_locations(self):
        for station_info in self.cached_data['resultList']:
            # (latitude, longitude)
            yield [float(station_info['gpsY']), float(station_info['gpsX'])]

    def get_current_position(self):
        raise NotImplementedError()