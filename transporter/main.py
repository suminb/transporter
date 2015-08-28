from flask import Blueprint, render_template, request, redirect, url_for
from flask import request, render_template, redirect

main_module = Blueprint(
    'main', __name__, template_folder='transporter/templates')


@main_module.route('/')
def index():
    context = dict(
    )
    return render_template('index.html', **context)
