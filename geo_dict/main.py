# coding=utf-8
from geo_dict.processing.processing import process
from geo_dict.common.distance import calculate_distance


def test(text, model_coords):
    coords = process(text)

    print min([(calculate_distance(model_coords[0], model_coords[1], c[0], c[1]), (c[0], c[1])) for c in coords])


text = u'Opis problemu: skrzyżowanie Łukasińskiego i Huculskiej. Duża wyrwa w drodze.'
model_coords = (50.022075, 19.926117)

test(text, model_coords)

text = u'Między wroclawska a mazowiecka są jakies osiedla.'
model_coords = (50.0775898, 19.9225592)

test(text, model_coords)

text = u'Czekałem na Kijowskiej, na skrzyżowaniu obok Biprostalu'
model_coords = (50.072973, 19.915578)

test(text, model_coords)

text = u'Pomiędzy ulicą Świętego Jana a Jamą Michalika znajduje się Muzeum Czartoryskich'  # NER is needed both in places and streets
model_coords = (50.064624, 19.939964)

test(text, model_coords)

text = u'Co jest pomiędzy ulicą Szujskiego a AGH?'
model_coords = (50.064266, 19.927148)

test(text, model_coords)

text = u'Czekam przy Czarnowiejskiej obok AGH'
model_coords = (50.066275, 19.922667)

test(text, model_coords)