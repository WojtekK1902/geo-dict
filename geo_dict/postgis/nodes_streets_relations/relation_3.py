from numpy import mean

from geo_dict.postgis.connection import connect
from helpers.helpers import process_street


def gis(street_name, node_name):
    conn = connect()

    cur = conn.cursor()

    way1 = process_street(street_name)

    # polygon is created from the street and node

    cur.execute("""SELECT ST_Transform(geom, 26986) FROM nodes
WHERE id IN (SELECT node_id FROM node_tags WHERE k LIKE 'name' AND lower(v) LIKE '""" + node_name.lower() + """')""")
    point1 = cur.fetchone()[0]
    cur.execute("""SELECT ST_X('""" + point1 + """');""")
    point1_x = cur.fetchone()[0]
    cur.execute("""SELECT ST_Y('""" + point1 + """');""")
    point1_y = cur.fetchone()[0]

    points_way1 = ""
    for n in way1:
        cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(n) + """;""")
        point = cur.fetchone()[0]
        cur.execute("""SELECT ST_X(ST_AsText(ST_Transform('""" + point + """',26986)));""")
        x = cur.fetchone()[0]
        cur.execute("""SELECT ST_Y(ST_AsText(ST_Transform('""" + point + """',26986)));""")
        y = cur.fetchone()[0]
        points_way1 += str(x) + ' ' + str(y) + ', '

    points = str(point1_x) + ' ' + str(point1_y) + ', ' + points_way1 + str(point1_x) + ' ' + str(point1_y)

    cur.execute(
        """SELECT ST_AsText(geom) FROM nodes
WHERE ST_Within(ST_Transform(geom, 26986), ST_GeomFromText('SRID=26986;POLYGON((""" + points + """))'));""")
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

    return mean(ys), mean(xs)