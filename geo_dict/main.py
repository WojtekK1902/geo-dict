# coding=utf-8
from geo_dict.processing.processing import process
from geo_dict.test.test import calculate_distance

text = u'Opis problemu: skrzyżowanie Łukasińskiego i Huculskiej. Duża wyrwa w drodze.'
model_coords = '50.022075850566914#19.926117202377327'

coords = process(text)

print min([calculate_distance(float(model_coords.split('#')[0]), float(model_coords.split('#')[1]), c[0], c[1])
         for c in coords])