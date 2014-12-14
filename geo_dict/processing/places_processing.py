import itertools
from geo_dict.common import geo_relations_prepositions
from geo_dict.common.geo_relations_prepositions import has_preposition

from geo_dict.postgis import nodes_relations
from geo_dict.postgis.nodes_relations import relation_1, relation_2, relation_3


def process(words, places):
    shift = 5

    if len(places) >= 2:
        combinations = itertools.combinations(places, 2)  # If there are more than a pair of streets, we should
                                                          # check all the combinations
        for c in combinations:
            if c[0][2] < c[1][2]:
                left = c[0][2] - shift
                right = c[1][2] + shift
            else:
                left = c[1][2] - shift
                right = c[0][2] + shift
            if left < 0:
                left = 0

        if has_preposition(words[left:right], geo_relations_prepositions.relation_3):
            coords = nodes_relations.relation_3.gis(c[0][0], c[1][0])
            if coords:
                return coords

    for p in places:
        left = p[2] - shift
        if left < 0:
            left = 0

        if has_preposition(words[left:p[2]], geo_relations_prepositions.relation_2):
            coords = nodes_relations.relation_2.gis(p[0])
            if coords:
                return coords

        if has_preposition(words[left:p[2]], geo_relations_prepositions.relation_1):
            coords = nodes_relations.relation_1.gis(p[0])
            if coords:
                return coords