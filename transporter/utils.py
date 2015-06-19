import json
import requests


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