from numpy import mean

from geo_dict.postgis.connection import connect


def gis(node_name1, node_name2):
    conn = connect()

    cur = conn.cursor()

    cur.execute("""SELECT ST_Transform(geom, 26986) FROM nodes
WHERE id IN (SELECT node_id FROM node_tags WHERE k LIKE 'name' AND lower(v) LIKE '""" + node_name1.lower() + """')""")
    point1 = cur.fetchone()[0]
    cur.execute("""SELECT ST_Transform(geom, 26986) FROM nodes
WHERE id IN (SELECT node_id FROM node_tags WHERE k LIKE 'name' AND lower(v) LIKE '""" + node_name2.lower() + """')""")
    point2 = cur.fetchone()[0]

    cur.execute("""SELECT ST_X('""" + point1 + """')""")
    x1 = cur.fetchone()[0]
    cur.execute("""SELECT ST_Y('""" + point1 + """')""")
    y1 = cur.fetchone()[0]
    cur.execute("""SELECT ST_X('""" + point2 + """')""")
    x2 = cur.fetchone()[0]
    cur.execute("""SELECT ST_Y('""" + point2 + """')""")
    y2 = cur.fetchone()[0]

    cur.execute(
        """SELECT ST_GeomFromText('SRID=26986;LINESTRING(""" + str(x1) + ' ' + str(y1) + ', ' + str(x2) + ' ' + str(y2)
        + """)');""")
    line = cur.fetchone()[0]

    cur.execute(
        """SELECT ST_AsText(geom) FROM nodes WHERE ST_Distance(ST_Line_Interpolate_Point('""" + line +
        """', ST_Line_Locate_Point('""" + line + """', ST_Transform(geom, 26986))), ST_Transform(geom, 26986)) < 20;""")
    rows = cur.fetchall()

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