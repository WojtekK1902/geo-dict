import re

from geo_dict.common import stoplist
from geo_dict.common import geo_relations_prepositions
from geo_dict.common.levenshtein import lev_dist
from geo_dict.postgis import streets_relations
from geo_dict.postgis.streets_relations import relation_3, relation_4
from geo_dict.processing.ner import find_streets, find_places


def process(text):
    text = text.decode('utf-8').strip().lower()

    words = [w for w in re.findall(r'\w+', text, re.U) if w not in stoplist]

    streets = find_streets(words)
    places = find_places(words)

    if len(streets) > 1:
        left, right = 5, 5
        if streets[0][1] < left:
            left = 0

        if has_prepositions(words[streets[0][1]-left:words[streets[1][1]+right]], geo_relations_prepositions.relation_4):
            coords = streets_relations.relation_4.gis(streets[0][0], streets[0][1])
            if coords:
                return coords

        if has_prepositions(words[streets[0][1]-left:], geo_relations_prepositions.relation_3):
            coords = streets_relations.relation_3.gis(streets[0][0], streets[0][1])
            if coords:
                return coords


def has_prepositions(words, relation_prepositions):
    for prep in relation_prepositions:
        for word in words:
            if lev_dist(word, prep) <= 0.75:
                return True
    return False