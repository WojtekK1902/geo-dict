# -*- coding: utf-8 -*-
from collections import defaultdict, Counter
import glob

from corpus.kpwr import load_kpwr_model
from dict import generate
from model.ccl_parser import CCLNERParser
from model.tagparser import TagNEParser
from model.types import PERSON_NAME, STREET, CITY, PERSON_SURNAME, filter_corpus, COUNTRY
from tools import score, stemmer


names_dict = generate.load_names_dict()
print 'names dict loaded'
surnames_dict = generate.load_surnames_dict()
print 'surnames dict loaded'

cities_dict = generate.load_cities_dict()
print 'cities dict loaded'
streets_dict = generate.load_streets_dict()
print 'streets dict loaded'

countries_dict = generate.load_countries_dict()
print 'countries dict loaded'

CORPUS_PATH = "../dane/kpwr-1.1"


def mark_objects(phrases):
    processing_results = []

    for i in range(len(phrases)):
        phrase_len = len(phrases[i])
        print phrase_len
        for j in range(1):  # range(phrase_len)
            for k in range(phrase_len - j):
                processing_results.append(
                    process_token(' '.join(phrases[i][k:k + j + 1]), i, tuple(range(k, k + j + 1))))

    return filter(lambda x: x, processing_results)


def process_token(token, phrase_no, token_no):
    base = stemmer.gen_sjp_base(token)

    if token in names_dict:
        type = PERSON_NAME
    elif token in countries_dict:
        type = COUNTRY
    elif token in cities_dict:
        type = CITY
    elif base in streets_dict:
        type = STREET
    elif token in surnames_dict:
        type = PERSON_SURNAME
    else:
        type = None

    if type: print token, type, (phrase_no, token_no, type)
    return type and (phrase_no, token_no, type) or None


def test_corpus():
    corpus = load_kpwr_model()

    global_metrics = defaultdict(list)

    i = 1
    for (filename, objects, plain_text) in filter_corpus(corpus):
        matched_objects = mark_objects(plain_text)

        print objects
        score.compute_metrics_for_types(objects, matched_objects, global_metrics, filename)

        print i, '/', len(corpus)
        i += 1

    score.print_metrics_map(global_metrics)





def load_corpus():
    parsers = []
    c = 0

    try:

        for filename in glob.glob(CORPUS_PATH + '/*/*.xml'):
            if filename.find('rel') == -1:
                parsers.append(CCLNERParser(filename))
                c += 1
                #
                # for filename in glob.glob(CORPUS_PATH + '/wikipedia/*.xml'):
                # if filename.find('rel') == -1:
                #         parsers.append(CCLNERParser(filename))
                #         c += 1


    except Exception as e:
        print e
        print c

    return parsers


if __name__ == "__main__":
    test_corpus()
    # print mark_objects([[u"Ala", u"ma", u"kota", u"w", u"Polsce"], [u"A", u"kot", u"ma", u"Alę", u"i", u"Boba"]])

