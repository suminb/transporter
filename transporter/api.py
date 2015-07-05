from flask import Blueprint, render_template, request, redirect, url_for
from flask import request, render_template, redirect, jsonify
from logbook import Logger
from collections import deque
from transporter.models import Route, Station, GraphNode
from transporter.utils import get_nearest_stations, build_graph

api_module = Blueprint(
    'api', __name__, template_folder='templates/api')

log = Logger(__name__)
inf = float('inf')


def build_nodes_for_route(route):
    """Build graph nodes for a route"""
    nodes = {}
    for station in route.stations:
        nodes[station.id] = GraphNode(station)

    for edge in route.edges:
        if edge.start not in nodes:
            log.warn('Node for station {} does not exist (start)'.format(edge.start))
        elif edge.end not in nodes:
            log.warn('Node for station {} does not exist (end)'.format(edge.start))
        else:
            nodes[edge.start].add_neighbor(nodes[edge.end])

    return nodes


def calculate_costs(nodes):
    cost = {}
    prev = {}
    queue = deque()

    source = route.stations[0].id
    cost[source] = 0
    prev[source] = None

    for node in nodes.values():
        if node.data.id != source:
            cost[node.data.id] = inf
            prev[node.data.id] = None
        queue.append(node)

    while len(queue) > 0:
        # u := vertex in Q with min cost[u]
        min_cost_node_id = queue[0].data.id
        min_cost = cost[min_cost_node_id]
        for node in queue:
            if cost[node.data.id] < min_cost:
                min_cost = cost[node.data.id]
                min_cost_node_id = node.data.id

        # Remove u from Q
        u = nodes[min_cost_node_id]
        try:
            queue.remove(nodes[min_cost_node_id])
        except ValueError:
            pass

        for v, c in u.neighbor_cost_pairs:
            if cost[u.data.id] + c < cost[v.data.id]:
                cost[v.data.id] = cost[u.data.id] + c
                prev[v.data.id] = u


@api_module.route('/station/<int:station_id>/routes')
def station_routes(station_id):
    """Request all routes that go through a given station."""

    station = Station.get_or_404(station_id)

    return jsonify(station=station.serialize(),
                   routes=[r.serialize(excludes=['raw']) for r in station.routes])


@api_module.route('/nearest_stations')
def nearest_stations():

    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')

    stations = get_nearest_stations(latitude, longitude)

    return jsonify(stations=stations)


@api_module.route('/route/<int:route_id>')
def route(route_id):

    route = Route.get_or_404(route_id)

    nodes = build_nodes_for_route(route)

    return jsonify(route=route.serialize(attributes=[], excludes=['raw']),
                   stations=[x.serialize() for x in route.stations],
                   edges=[x.serialize() for x in route.edges])
