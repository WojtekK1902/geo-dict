from geo_dict.postgis.connection import connect


def gis(node_name1, node_name2):
    conn = connect()

    cur = conn.cursor()

    cur.execute("SELECT ST_Transform(geom, 26986) FROM nodes WHERE id IN "
                "(SELECT node_id FROM node_tags WHERE k LIKE 'name' AND lower(v) LIKE '{0}');".format(node_name1))
    point1 = cur.fetchone()[0]

    cur.execute("SELECT ST_Transform(geom, 26986) FROM nodes WHERE id IN "
                "(SELECT node_id FROM node_tags WHERE k LIKE 'name' AND lower(v) LIKE '{0}');".format(node_name2))
    point2 = cur.fetchone()[0]

    cur.execute("SELECT ST_X('{0}');".format(point1))
    x1 = cur.fetchone()[0]
    cur.execute("SELECT ST_Y('{0}');".format(point1))
    y1 = cur.fetchone()[0]
    cur.execute("SELECT ST_X('{0}');".format(point2))
    x2 = cur.fetchone()[0]
    cur.execute("SELECT ST_Y('{0}');".format(point2))
    y2 = cur.fetchone()[0]

    cur.execute("SELECT ST_GeomFromText('SRID=26986;LINESTRING({0} {1}, {2} {3})');".format(x1, y1, x2, y2))
    line = cur.fetchone()[0]

    cur.execute("SELECT ST_AsText(geom) FROM nodes WHERE "
                "ST_Distance(ST_Line_Interpolate_Point('{0}', ST_Line_Locate_Point('{0}', ST_Transform(geom, 26986))), "
                "ST_Transform(geom, 26986)) < 20;".format(line))
    rows = cur.fetchall()

    xs, ys = [], []
    for r in rows:
        cur.execute("SELECT ST_X('{0}');".format(r[0]))
        x = cur.fetchone()[0]
        xs.append(float(x))
        cur.execute("SELECT ST_Y('{0}');".format(r[0]))
        y = cur.fetchone()[0]
        ys.append(float(y))

    cur.close()
    conn.close()

    return zip(ys, xs)