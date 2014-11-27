from numpy import mean
import psycopg2
import os
from helpers.helpers import process_street


def gis(street_name1, street_name2):
    conn = psycopg2.connect(
        'dbname = ' + os.environ['DBNAME'] + ' user = ' + os.environ['DBUSER'] + ' port = ' + os.environ['DBPORT'])

    cur = conn.cursor()

    way1 = process_street(street_name1)
    way2 = process_street(street_name2)

    # tworze polygon z dwoch ulic

    points1 = ""
    for n in way1:
        cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(n) + """;""")
        point = cur.fetchone()[0]
        cur.execute("""SELECT ST_X(ST_AsText(ST_Transform('""" + point + """',26986)));""")
        x = cur.fetchone()[0]
        cur.execute("""SELECT ST_Y(ST_AsText(ST_Transform('""" + point + """',26986)));""")
        y = cur.fetchone()[0]
        points1 += str(x) + ' ' + str(y) + ', '

    points2 = points1  #trzeba stworzyc dwie wersje polygonu, zeby zobaczyc ktore wierzcholki nalezy polaczyc

    for n in way2:
        cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(n) + """;""")
        point = cur.fetchone()[0]
        cur.execute("""SELECT ST_X(ST_AsText(ST_Transform('""" + point + """',26986)));""")
        x = cur.fetchone()[0]
        cur.execute("""SELECT ST_Y(ST_AsText(ST_Transform('""" + point + """',26986)));""")
        y = cur.fetchone()[0]
        points1 += str(x) + ' ' + str(y) + ', '

    for i in range(len(way2) - 1, -1, -1):
        cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(way2[i]) + """;""")
        point = cur.fetchone()[0]
        cur.execute("""SELECT ST_X(ST_AsText(ST_Transform('""" + point + """',26986)));""")
        x = cur.fetchone()[0]
        cur.execute("""SELECT ST_Y(ST_AsText(ST_Transform('""" + point + """',26986)));""")
        y = cur.fetchone()[0]
        points2 += str(x) + ' ' + str(y) + ', '

    cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(way1[0]) + """;""")
    point = cur.fetchone()[0]
    cur.execute("""SELECT ST_X(ST_AsText(ST_Transform('""" + point + """',26986)));""")
    x = cur.fetchone()[0]
    cur.execute("""SELECT ST_Y(ST_AsText(ST_Transform('""" + point + """',26986)));""")
    y = cur.fetchone()[0]

    points1 += str(x) + ' ' + str(y)
    points2 += str(x) + ' ' + str(y)

    cur.execute("""SELECT ST_AREA(ST_GeomFromText('POLYGON((""" + points1 + """))'));""")
    area1 = cur.fetchone()[0]

    cur.execute("""SELECT ST_AREA(ST_GeomFromText('POLYGON((""" + points2 + """))'));""")
    area2 = cur.fetchone()[0]

    if area1 > area2:
        points = points1
    else:
        points = points2

    cur.execute(
        """SELECT ST_AsText(geom) FROM nodes WHERE ST_Within(ST_Transform(geom, 26986),
ST_GeomFromText('SRID=26986;POLYGON((""" + points + """))'));""")
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