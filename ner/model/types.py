#-*- coding: utf-8 -*-
from ner.model.tagparser import TagNEParser

PERSON_NAME = u'person_first_nam'
PERSON_SURNAME = u'person_last_nam'
CITY = u'city_nam'
STREET = u'road_nam'
COUNTRY = u'country_nam'
ADMIN1 = u'admin1_nam'
ADMIN2 = u'admin2_nam'
CONTINENT = u'continent_nam'

DISTRICT_NKJP = u'district'
GEOGNAME_NKJP = u'geogname'

VALID_TYPES = [GEOGNAME_NKJP, DISTRICT_NKJP] # [PERSON_NAME, PERSON_SURNAME, COUNTRY, CITY, STREET]
# VALID_TYPES = [ADMIN1, ADMIN2, COUNTRY, CITY, STREET, CONTINENT]

TYPES_INDEX = dict((VALID_TYPES[i], i) for i in range(len(VALID_TYPES)))

DISPLAY_NAMES = {PERSON_NAME: u'Imiona', PERSON_SURNAME: u'Nazwiska', CITY: u'Miasta', STREET: u'Ulice',
                 COUNTRY: u'Państwa', ADMIN1: u'Województwa', ADMIN2: u'Powiaty', CONTINENT : u'Kontynenty'}


def filter_corpus(corpus, valid_types=VALID_TYPES):
    new_corpus = []

    for (file, objects, plain_text) in corpus:

        new_objects = filter(
            lambda o: o[TagNEParser.TYPE] in valid_types,
            objects)
        if new_objects:
            new_corpus.append((file, new_objects, plain_text))

    return new_corpus