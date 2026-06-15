
from app.services.osm_polygon_importer import (
    _parse_polygon_from_overpass,
    _compute_bbox_and_centroid,
    _build_overpass_query,
)


class TestParsePolygonFromOverpass:
    def test_way_geometry(self):
        data = {
            "elements": [
                {
                    "type": "way",
                    "id": 1,
                    "geometry": [
                        {"lat": 60.0, "lon": 30.0},
                        {"lat": 60.1, "lon": 30.1},
                        {"lat": 60.2, "lon": 30.0},
                        {"lat": 60.0, "lon": 30.0},
                    ],
                }
            ]
        }
        rings = _parse_polygon_from_overpass(data)
        assert rings is not None
        assert len(rings) == 1
        assert len(rings[0]) == 4
        assert rings[0][0] == [30.0, 60.0]

    def test_relation_outer_members(self):
        data = {
            "elements": [
                {
                    "type": "relation",
                    "id": 1,
                    "members": [
                        {
                            "role": "outer",
                            "geometry": [
                                {"lat": 60.0, "lon": 30.0},
                                {"lat": 60.1, "lon": 30.1},
                                {"lat": 60.0, "lon": 30.0},
                            ],
                        }
                    ],
                }
            ]
        }
        rings = _parse_polygon_from_overpass(data)
        assert rings is not None
        assert len(rings) == 1

    def test_no_elements_returns_none(self):
        rings = _parse_polygon_from_overpass({"elements": []})
        assert rings is None

    def test_closed_ring_not_duplicated(self):
        data = {
            "elements": [
                {
                    "type": "way",
                    "id": 1,
                    "geometry": [
                        {"lat": 60.0, "lon": 30.0},
                        {"lat": 60.1, "lon": 30.1},
                        {"lat": 60.0, "lon": 30.0},
                    ],
                }
            ]
        }
        rings = _parse_polygon_from_overpass(data)
        assert rings is not None
        assert rings[0][0] == rings[0][-1]

    def test_picks_largest_way(self):
        data = {
            "elements": [
                {
                    "type": "way",
                    "id": 1,
                    "geometry": [
                        {"lat": 60.0, "lon": 30.0},
                        {"lat": 60.1, "lon": 30.0},
                        {"lat": 60.0, "lon": 30.0},
                    ],
                },
                {
                    "type": "way",
                    "id": 2,
                    "geometry": [
                        {"lat": 61.0, "lon": 31.0},
                        {"lat": 61.1, "lon": 31.1},
                        {"lat": 61.2, "lon": 31.0},
                        {"lat": 61.3, "lon": 31.2},
                        {"lat": 61.0, "lon": 31.0},
                    ],
                },
            ]
        }
        rings = _parse_polygon_from_overpass(data)
        assert rings is not None
        assert len(rings) >= 1


class TestComputeBboxAndCentroid:
    def test_basic(self):
        rings = [[[30.0, 60.0], [31.0, 60.0], [31.0, 61.0], [30.0, 61.0], [30.0, 60.0]]]
        lat_min, lat_max, lon_min, lon_max, c_lat, c_lon = _compute_bbox_and_centroid(rings)
        assert lat_min == 60.0
        assert lat_max == 61.0
        assert lon_min == 30.0
        assert lon_max == 31.0
        assert 60.3 < c_lat < 60.5
        assert 30.3 < c_lon < 30.5


class TestBuildOverpassQuery:
    def test_query_contains_name(self):
        q = _build_overpass_query("Тест", 59.0, 29.0, 61.0, 33.0)
        assert "Тест" in q
        assert "natural" in q
        assert "out geom" in q

    def test_query_contains_bbox(self):
        q = _build_overpass_query("Test", 59.0, 29.0, 61.0, 33.0)
        assert "59.0,29.0,61.0,33.0" in q
