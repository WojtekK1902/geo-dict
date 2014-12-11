import codecs
from operator import itemgetter
import re
import os

from geo_dict.common.stoplist import stoplist
from geo_dict.common.diacritic_letters import diacritic_letters
from geo_dict.common.levenshtein import lev_dist
from geo_dict.processing import streets_processing, places_processing


def process(text):
    text = text.strip().lower()

    words = [w for w in re.findall(r'\w+', text, re.U) if w not in stoplist]

    all_streets = prepare_streets(os.environ['STREETS_DATA'])
    streets = find_streets(words, all_streets)

    all_places = prepare_places(os.environ['PLACES_DATA'])
    places = find_places(words, all_places)

    if streets:
        coords = streets_processing.process(words, streets, places)
        if coords:
            return coords

    if places:
        coords = places_processing.process(words, places)
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