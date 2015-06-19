from flask import Blueprint, render_template, request, redirect, url_for
from flask import request, render_template, redirect, jsonify
from transporter.models import Station, Route

api_module = Blueprint(
    'api', __name__, template_folder='templates/api')


@api_module.route('/nearest_stations')
def nearest_stations():

    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')

    stations = Station.get_nearby_stations(latitude, longitude)

    return jsonify(stations=stations)


@api_module.route('/route/<int:route_id>')
def route(route_id):

    route = Route.get_or_404(route_id)

    return jsonify(route=route.serialize(attributes=[], excludes=['raw']),
                   stations=[r.serialize() for r in route.stations])