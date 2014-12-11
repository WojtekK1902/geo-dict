from geo_dict.common import geo_relations_prepositions
from geo_dict.processing.processing import has_preposition

from geo_dict.postgis import nodes_relations
from geo_dict.postgis.nodes_relations import relation_1, relation_2, relation_3


def process(words, places):
    shift = 5

    if places[0][2] < places[1][2]:
        left = places[0][2] - shift
        right = places[1][2] + shift
    else:
        left = places[1][2] - shift
        right = places[0][2] + shift
    if left < 0:
        left = 0

    if has_preposition(words[left:right], geo_relations_prepositions.relation_3):
        coords = nodes_relations.relation_3.gis(places[0][0], places[1][0])
        if coords:
            return coords

    for p in places:
        left = p[2] - shift
        if left < 0:
            left = 0

        if has_preposition(words[left:p[2]+shift], geo_relations_prepositions.relation_2):
            coords = nodes_relations.relation_2.gis(p[0])
            if coords:
                return coords

    for p in places:
        if has_preposition(words[left:p[2]+shift], geo_relations_prepositions.relation_1):
            coords = nodes_relations.relation_1.gis(p[0])
            if coords:
                return coords