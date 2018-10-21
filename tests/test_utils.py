from transporter.utils import get_route


def test_get_route():
    route_info = get_route(100100508)
    assert 'entries' in route_info
    assert len(route_info['entries']) > 0
    for route_entry in route_info['entries']:
        assert route_entry['ars_id'] is None or \
            isinstance(route_entry['ars_id'], int)
        assert 0.0 <= route_entry['latitude'] < 90.0
        assert 0.0 <= route_entry['longitude'] < 180.0
