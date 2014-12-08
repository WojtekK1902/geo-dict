import codecs
from operator import itemgetter
import re
import os
import itertools
import numpy as np

from geo_dict.common.stoplist import stoplist
from geo_dict.common import geo_relations_prepositions
from geo_dict.common.diacritic_letters import diacritic_letters
from geo_dict.common.levenshtein import lev_dist
from geo_dict.postgis import streets_relations, nodes_relations
from geo_dict.postgis.nodes_relations import relation_1, relation_2, relation_3
from geo_dict.postgis.streets_relations import relation_1, relation_2, relation_3, relation_4, relation_4_single


def process(text):
    text = text.strip().lower()

    words = [w for w in re.findall(r'\w+', text, re.U) if w not in stoplist]

    all_streets = prepare_streets(os.environ['STREETS_DATA'])
    streets = find_streets(words, all_streets)

    all_places = prepare_places(os.environ['PLACES_DATA'])
    places = find_places(words, all_places)

    if streets:
        shift = 5

        if len(streets) > 2:
            combinations = itertools.combinations(streets, 2)   # If there are more than a pair of streets, we should
                                                                # check all the combinations
            for c in combinations:
                if c[0][1] < c[1][1]:
                    offset = c[0][1] - shift
                else:
                    offset = c[1][1] - shift
                if offset < 0:
                    offset = 0

                if has_preposition(words[:offset], geo_relations_prepositions.relation_4):
                    coords = streets_relations.relation_4.gis(c[0][0], c[1][0])
                    if coords:
                        return coords

                if has_preposition(words[:offset], geo_relations_prepositions.relation_3):
                    coords = streets_relations.relation_3.gis(c[0][0], c[1][0])
                    if coords:
                        return coords

        for s in streets:
            if has_preposition(words[:s[1]-shift], geo_relations_prepositions.relation_4):
                coords = streets_relations.relation_4_single.gis(s[0])
                if coords:
                    # We look for some additional information
                    places_coords = []
                    for p in places:
                        places_coords.extend(nodes_relations.relation_1.gis(p))

                    common_coords = list(set(coords).intersection(places_coords))
                    if common_coords:
                        return [np.mean(zip(*common_coords)[0]), np.mean(zip(*common_coords)[1])]
                    return coords

            if has_preposition(words[:s[1]-shift], geo_relations_prepositions.relation_2):
                coords = streets_relations.relation_2.gis(s[0])
                if coords:
                    return coords

            if has_preposition(words[:s[1]-shift], geo_relations_prepositions.relation_1):
                coords = streets_relations.relation_1.gis(s[0])
                if coords:
                    return coords

    return None


def prepare_streets(path):
    """
    Street names have to be recognized by their last word, for example:
    'Aleja Adama Mickiewicza', 'Adama Mickiewicza' and 'Mickiewicza' are names of the same street.
    Therefore, the last word is the most significant one
    Key in a dictionary is the last word of each street only
    :param path:
    :return:
    """
    streets = {}
    with codecs.open(path, 'r', 'utf-8') as f:
        for line in f:
            inflections = line.strip().lower().split(';')
            for i in inflections:
                streets[i.split()[-1]] = inflections[0]
    return streets


def prepare_places(path):
    with codecs.open(path, 'r', 'utf-8') as f:
        return [p.strip().lower() for p in f.readlines()]


def find_streets(words, all_streets):
    """
    :param words:
    :param all_streets:
    :return: List of tuples with potential street names. Each tuple consists of:
     * street name,
     * Levenshtein distance between the street name and the word in a text recognized as this name
     * and this word's location in text
    """
    streets = []
    for i, w in enumerate(words):
        # Let's limit potential street names to the ones that begin with the same letter as the given word
        streets_same_letter = [s for s in all_streets if s[0] == w[0]
                               or (s[0] in diacritic_letters and diacritic_letters[s[0]] == w[0])]
        for s in streets_same_letter:
            dist = lev_dist(w, s)
            if dist < 1.5:
                streets.append((all_streets[s], dist, i))
    return sorted(streets, key=itemgetter(1, 2))  # Sort by Levenshtein distance, then by location in text


def find_places(words, all_places):
    places = []
    for i, w in enumerate(words):
        # Let's limit potential place names to the ones that begin with the same letter as the given word
        places_same_letter = [p for p in all_places if p[0] == w[0]
                              or (p[0] in diacritic_letters and diacritic_letters[p[0]] == w[0])]
        for p in places_same_letter:
            dist = lev_dist(w, p)
            if dist < 2.5:
                places.append((p, dist, i))
    return sorted(places, key=itemgetter(1, 2))  # Sort by Levenshtein distance, then by location in text


def has_preposition(words, relation_prepositions):
    for prep in relation_prepositions:
        for word in words:
            if lev_dist(word, prep) <= 0.75:
                return True
    return False