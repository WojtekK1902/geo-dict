from geo_dict.postgis.connection import connect


def gis(street_name1, street_name2):
    conn = connect()

    cur = conn.cursor()

    cur.execute("""SELECT ST_AsText(geom) FROM nodes
WHERE id = (SELECT node_id FROM way_nodes WHERE way_id IN
(SELECT way_id FROM way_tags WHERE k LIKE 'name' AND lower(v) LIKE '""" + street_name1.lower() + """')
AND node_id IN
(SELECT node_id FROM way_nodes WHERE way_id IN
(SELECT way_id FROM way_tags WHERE k LIKE 'name' AND lower(v) LIKE '""" + street_name2.lower() + "')) LIMIT 1);")
    row = cur.fetchone()

    if row is None:
        return None

    cur.execute("""SELECT ST_X('""" + row[0] + """');""")
    x = cur.fetchone()[0]
    cur.execute("""SELECT ST_Y('""" + row[0] + """');""")
    y = cur.fetchone()[0]

    cur.close()
    conn.close()

    return [(float(y), float(x))]