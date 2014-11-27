from numpy import mean
import psycopg2
import os


def gis(street_name):
    conn = psycopg2.connect(
        'dbname = ' + os.environ['DBNAME'] + ' user = ' + os.environ['DBUSER'] + ' port = ' + os.environ['DBPORT'])

    cur = conn.cursor()

    cur.execute("""SELECT ST_AsText(geom) FROM nodes
WHERE id IN (SELECT node_id FROM way_nodes WHERE way_id IN
(SELECT way_id FROM way_tags WHERE k LIKE 'name' AND lower(v) LIKE '""" + street_name.lower() + """'))""")

    row = cur.fetchall()
    xs, ys = [], []
    for r in row:
        cur.execute("""SELECT ST_X('""" + r[0] + """');""")
        x = cur.fetchone()[0]
        xs.append(float(x))
        cur.execute("""SELECT ST_Y('""" + r[0] + """');""")
        y = cur.fetchone()[0]
        ys.append(float(y))

    cur.close()
    conn.close()

    return mean(ys), mean(xs)
