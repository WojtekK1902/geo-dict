from geo_dict.postgis.connection import connect


def gis(street_name):
    conn = connect()

    cur = conn.cursor()

    cur.execute("""SELECT ST_AsText(geom) FROM nodes 
WHERE id IN (SELECT node_id FROM way_nodes 
WHERE way_id IN (SELECT way_id FROM way_tags WHERE k LIKE 'name' AND lower(v) LIKE '""" + street_name.lower() + """')
INTERSECT
SELECT node_id FROM way_nodes 
WHERE way_id IN (SELECT way_id FROM way_tags WHERE k LIKE 'name' AND lower(v) NOT LIKE '""" + street_name.lower() +
                """'));""")
    rows = cur.fetchall()

    if rows is None:
        return None

    xs, ys = [], []
    for r in rows:
        cur.execute("""SELECT ST_X('""" + r[0] + """');""")
        x = cur.fetchone()[0]
        xs.append(float(x))
        cur.execute("""SELECT ST_Y('""" + r[0] + """');""")
        y = cur.fetchone()[0]
        ys.append(float(y))

    cur.close()
    conn.close()

    return zip(ys, xs)