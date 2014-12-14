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

text = u'Czekam na Czarnowiejskiej obok AGH'
model_coords = (50.066558, 19.922043)

test(text, model_coords)

text = u'Dzwonię z Królewskiej obok Biprostalu'
model_coords = (50.073073, 19.915252)

test(text, model_coords)

text = u'Jestem pomiędzy Politechniką a Galerią Krakowską'  #NER is needed...
model_coords = (50.069489, 19.945056)

test(text, model_coords)

text = u'Wysiadłem obok Wawelu'
model_coords = (50.053669, 19.936891)

test(text, model_coords)

text = u'Jestem w Biprostalu'
model_coords = (50.0732415, 19.9153479)

test(text, model_coords)