import psycopg2
import os


def process_street(street_name):
    conn = psycopg2.connect(
        'dbname = ' + os.environ['DBNAME'] + ' user = ' + os.environ['DBUSER'] + ' port = ' + os.environ['DBPORT'])

    cur = conn.cursor()

    cur.execute("""SELECT node_id, sequence_id FROM way_nodes
	WHERE way_id IN (SELECT way_id FROM way_tags WHERE k LIKE 'name' AND lower(v) LIKE '""" + street_name.lower() +
                """');""")

    row = cur.fetchall()

    way_parts, l, i = [], [], 0

    for r in row:
        l.append(r[0])
        if i + 1 < len(row) and row[i + 1][1] == 0:
            way_parts.append(l)
            l = []
        i += 1
    way_parts.append(l)

    # szukam rozwidlen, czyli innych odcinkow, ktore tez mozna dolaczyc do obecnego fragmentu w rozwidleniach takich, koniec dodatkowej drogi jest taki jak koniec obecnego fragmentu przed dodaniem nowego

    rozwidlenia = []  # jest to lista list - kazda lista w srodku to grupy rozwidlen w tym samym punkcie
    for i in range(len(way_parts) - 1):
        r = []
        for j in range(i + 1, len(way_parts)):
            if way_parts[i][-1] == way_parts[j][-1]:
                if len(
                        r) == 0:  # to jest po to, zeby way_parts[i] nie mogl byc dodany kilka razy (przy kilku rozwidleniach)
                    r.append(way_parts[i])
                r.append(way_parts[j])
        if len(r) > 0:
            rozwidlenia.append(r)

    # usuwam rozwidlenia - wywalam te fragmenty, ktore sa krotsze
    for r in rozwidlenia:
        while len(r) > 1:
            cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(r[0][0]) + """;""")
            geom1 = cur.fetchone()
            cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(r[0][-1]) + """;""")
            geom2 = cur.fetchone()
            cur.execute("""SELECT ST_Distance(ST_Transform('""" + geom1[0] + """',26986),ST_Transform('""" + geom2[
                0] + """',26986));""")
            dist1 = cur.fetchone()

            cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(r[1][0]) + """;""")
            geom1 = cur.fetchone()
            cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(r[1][-1]) + """;""")
            geom2 = cur.fetchone()
            cur.execute("""SELECT ST_Distance(ST_Transform('""" + geom1[0] + """',26986),ST_Transform('""" + geom2[
                0] + """',26986));""")
            dist2 = cur.fetchone()
            if dist1[0] > dist2[0]:
                way_parts.remove(r[1])
                r.remove(r[1])
            else:
                way_parts.remove(r[0])
                r.remove(r[0])


    #lacze poczatki odcinkow drog z koncami kolejnych odcinkow
    ways = []
    w = way_parts[0]
    way_parts.remove(w)
    while len(way_parts) > 0:
        last = w[-1]
        first = w[0]
        found = False
        for i in range(len(way_parts)):
            if way_parts[i][0] == last:  #wiaze poczatek jakiegos fragmentu z koncem obecnego
                w.extend(way_parts[i][1:])  #jak znalazlem, to rozszerzam obecny fragment
                found = True
                break
        if not found:
            for i in range(len(way_parts)):
                if way_parts[i][-1] == first:  #wiaze koniec jakiegos fragmentu z poczatkiem obecnego
                    w1 = way_parts[i]
                    w1.extend(w[1:])  #lacze te fragmenty
                    w = w1
                    found = True
                    break

        if found:
            way_parts.remove(way_parts[i])  #usuwam znaleziony fragment
        else:
            ways.append(w)
            w = way_parts[0]
            way_parts.remove(w)

    ways.append(w)

    #lacze poprzerywane odcinki
    while len(ways) > 1:
        d = {}  #slownik: klucz: odleglosc miedzy dwoma odcinkami (miedzy koncem pierwszego i poczatkiem drugiego)
        #wartosc: tuple(indeks odcinka 1, indeks odcinka 2, odcinek1_inversed (boolean), odcinek2_inversed (boolean)
        #trzecia i czwarta wartosc tupli jest potrzebna, bo niektore odcinki sa odwrocone wzgledem siebie
        for i in range(len(ways)):
            for j in range(len(ways)):
                if i != j:
                    cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(ways[i][-1]) + """;""")
                    geom1 = cur.fetchone()
                    cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(ways[j][0]) + """;""")
                    geom2 = cur.fetchone()
                    cur.execute(
                        """SELECT ST_Distance(ST_Transform('""" + geom1[0] + """',26986),ST_Transform('""" + geom2[
                            0] + """',26986));""")
                    dist = cur.fetchone()
                    d[dist] = (i, j, False, False)

                    cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(ways[i][-1]) + """;""")
                    geom1 = cur.fetchone()
                    cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(ways[j][-1]) + """;""")
                    geom2 = cur.fetchone()
                    cur.execute(
                        """SELECT ST_Distance(ST_Transform('""" + geom1[0] + """',26986),ST_Transform('""" + geom2[
                            0] + """',26986));""")
                    dist = cur.fetchone()
                    d[dist] = (i, j, False, True)

                    cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(ways[i][0]) + """;""")
                    geom1 = cur.fetchone()
                    cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(ways[j][0]) + """;""")
                    geom2 = cur.fetchone()
                    cur.execute(
                        """SELECT ST_Distance(ST_Transform('""" + geom1[0] + """',26986),ST_Transform('""" + geom2[
                            0] + """',26986));""")
                    dist = cur.fetchone()
                    d[dist] = (i, j, True, False)

                    cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(ways[i][0]) + """;""")
                    geom1 = cur.fetchone()
                    cur.execute("""SELECT geom FROM nodes WHERE id = """ + str(ways[j][-1]) + """;""")
                    geom2 = cur.fetchone()
                    cur.execute(
                        """SELECT ST_Distance(ST_Transform('""" + geom1[0] + """',26986),ST_Transform('""" + geom2[
                            0] + """',26986));""")
                    dist = cur.fetchone()
                    d[dist] = (i, j, True, True)

        min_dist = min(d.keys())
        w1_ind = d[min_dist][0]
        w2_ind = d[min_dist][1]
        w1_inv = d[min_dist][2]
        w2_inv = d[min_dist][3]

        if w1_inv:
            ways[w1_ind].reverse()
        if w2_inv:
            ways[w2_ind].reverse()
        ways[w1_ind].extend(ways[w2_ind])
        ways.remove(ways[w2_ind])

    cur.close()
    conn.close()

    return ways[0]

