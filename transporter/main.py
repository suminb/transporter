from flask import Blueprint, render_template, request, redirect, url_for
from flask import request, render_template, redirect
from transporter.bus import Bus, Station

main_module = Blueprint(
    'main', __name__, template_folder='templates/main')


@main_module.route('/')
def index():

    bus_ids = [4940100, 4940110, 90000250, 90000039, 90000216, 90000198, 90000333, 90000340, 90000159]
    buses = map(Bus, bus_ids)
    station_locations_of_buses = [b.get_station_locations() for b in buses]

    context = dict(
        buses=buses,
        station_locations_of_buses=station_locations_of_buses,
    )

    return render_template('index.html', **context)