import itertools
import numpy as np

from geo_dict.common import geo_relations_prepositions
from geo_dict.postgis import streets_relations, nodes_relations, nodes_streets_relations
from geo_dict.postgis.nodes_relations import relation_2
from geo_dict.postgis.nodes_streets_relations import relation_3
from geo_dict.postgis.streets_relations import relation_1, relation_2, relation_3, relation_4, relation_4_single
from geo_dict.processing.processing import has_preposition


def process(words, streets, places):
    shift = 5

    if len(streets) > 2:
        combinations = itertools.combinations(streets, 2)  # If there are more than a pair of streets, we should
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

            if has_preposition(words[left:right], geo_relations_prepositions.relation_4):
                coords = streets_relations.relation_4.gis(c[0][0], c[1][0])
                if coords:
                    return coords

            if has_preposition(words[left:right], geo_relations_prepositions.relation_3):
                coords = streets_relations.relation_3.gis(c[0][0], c[1][0])
                if coords:
                    return coords

    for s in streets:
        left = s[2] - shift
        if left < 0:
            left = 0

        if has_preposition(words[left:s[2]+shift], geo_relations_prepositions.relation_4):
            coords = streets_relations.relation_4_single.gis(s[0])
            if coords:
                # We look for some additional information
                places_coords = []
                for p in places:
                    places_coords.extend(nodes_relations.relation_2.gis(p[0]))

                common_coords = list(set(coords).intersection(places_coords))
                if common_coords:
                    return [np.mean(zip(*common_coords)[0]), np.mean(zip(*common_coords)[1])]
                return coords

        if has_preposition(words[left:s[2]+shift], geo_relations_prepositions.relation_3):
            if places:
                coords = nodes_streets_relations.relation_3.gis(s[0], places[0][0])
                if coords:
                    return coords

        if has_preposition(words[left:s[2]+shift], geo_relations_prepositions.relation_2):
            coords = streets_relations.relation_2.gis(s[0])
            if coords:
                # We look for some additional information
                places_coords = []
                for p in places:
                    places_coords.extend(nodes_relations.relation_2.gis(p[0]))

                common_coords = list(set(coords).intersection(places_coords))
                if common_coords:
                    return [np.mean(zip(*common_coords)[0]), np.mean(zip(*common_coords)[1])]
                return coords

        if has_preposition(words[left:s[2]+shift], geo_relations_prepositions.relation_1):
            coords = streets_relations.relation_1.gis(s[0])
            if coords:
                # We look for some additional information
                places_coords = []
                for p in places:
                    places_coords.extend(nodes_relations.relation_2.gis(p[0]))

                common_coords = list(set(coords).intersection(places_coords))
                if common_coords:
                    return [np.mean(zip(*common_coords)[0]), np.mean(zip(*common_coords)[1])]
                return coords