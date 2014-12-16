from geo_dict.postgis.connection import connect


def gis(node_name):
    conn = connect()

    cur = conn.cursor()

    cur.execute("SELECT ST_AsText(geom) FROM nodes WHERE id IN "
                "(SELECT node_id FROM node_tags WHERE k LIKE 'name' AND lower(v) LIKE '{0}');".format(node_name))

    row = cur.fetchall()
    xs, ys = [], []
    for r in row:
        cur.execute("SELECT ST_X('{0}');".format(r[0]))
        x = cur.fetchone()[0]
        xs.append(float(x))
        cur.execute("SELECT ST_Y('{0}');".format(r[0]))
        y = cur.fetchone()[0]
        ys.append(float(y))

    cur.close()
    conn.close()

    return zip(ys, xs)

