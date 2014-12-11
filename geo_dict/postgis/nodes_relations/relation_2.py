from geo_dict.postgis.connection import connect


def gis(node_name):
    conn = connect()

    cur = conn.cursor()

    cur.execute("""SELECT geom FROM nodes
WHERE id IN (SELECT node_id FROM node_tags WHERE k LIKE 'name' AND lower(v) LIKE '""" + node_name.lower() + """')""")

    row = cur.fetchall()

    xs, ys = [], []
    for r in row:
        # SRID needs to be changed to 2163 - http://forum.geonames.org/gforum/posts/list/727.page
        # http://www.nationalatlas.gov/articles/mapping/a_projections.html
        cur.execute("""SELECT id FROM nodes WHERE ST_DWithin(ST_Transform(geom, 2163), ST_Transform('""" + r[0]
                    + """', 2163) ,10)""")
        result = cur.fetchall()
        for res in result:
            cur.execute("""SELECT geom FROM nodes where id = """ + str(res[0]))
            cur.execute("""SELECT ST_AsText('""" + cur.fetchone()[0] + """')""")
            p = cur.fetchone()
            cur.execute("""SELECT ST_X('""" + p[0] + """');""")
            x = cur.fetchone()[0]
            xs.append(float(x))
            cur.execute("""SELECT ST_Y('""" + p[0] + """');""")
            y = cur.fetchone()[0]
            ys.append(float(y))

    cur.close()
    conn.close()

    return zip(ys, xs)

