from collections import deque

from flask import Blueprint, request, jsonify
from logbook import Logger

from transporter.models import GraphNode
from transporter.utils import get_nearest_stations, get_routes_for_station, \
    get_route


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
            log.warn('Node for station {} does not exist (start)'
                     .format(edge.start))
        elif edge.end not in nodes:
            log.warn('Node for station {} does not exist (end)'
                     .format(edge.start))
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


@api_module.route('/station/<int:ars_id>/routes')
def routes_for_station(ars_id):
    return jsonify(routes=get_routes_for_station(ars_id))


@api_module.route('/nearest_stations')
def nearest_stations():

    latitude = request.args['latitude']
    longitude = request.args['longitude']

    stations = get_nearest_stations(latitude, longitude)
    routes = [get_routes_for_station(s['ars_id']) for s in stations]

    entries = sum([r['entries'] for r in routes if len(r) > 0], [])
    routes = [get_route(x['route_id']) for x in entries]

    return jsonify(stations=stations, routes=routes)


@api_module.route('/route/<int:route_id>')
def route(route_id):

    route = get_route(route_id)
    return jsonify(route)
