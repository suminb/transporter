from flask import Blueprint, render_template, request, redirect, url_for
from flask import request, render_template, redirect
from bus import Bus, Station

main_module = Blueprint(
    'main', __name__, template_folder='templates/main')


@main_module.route('/')
def index():

    bus = Bus(4940100)

    context = dict(
        station_locations=bus.get_station_locations(),
    )

    return render_template('index.html', **context)