from geo_dict.common import geo_relations_prepositions
from geo_dict.processing.processing import has_preposition

from geo_dict.postgis import nodes_relations
from geo_dict.postgis.nodes_relations import relation_1, relation_2, relation_3


def process(words, places):
    shift = 5

    if has_preposition(words[:places[0][1] - shift], geo_relations_prepositions.relation_3):
        coords = nodes_relations.relation_3.gis(places[0][0], places[0][1])
        if coords:
            return coords

    for p in places:
        if has_preposition(words[:p[1] - shift], geo_relations_prepositions.relation_2):
            coords = nodes_relations.relation_2.gis(p[0])
            if coords:
                return coords

    for p in places:
        if has_preposition(words[:p[1] - shift], geo_relations_prepositions.relation_1):
            coords = nodes_relations.relation_1.gis(p[0])
            if coords:
                return coords