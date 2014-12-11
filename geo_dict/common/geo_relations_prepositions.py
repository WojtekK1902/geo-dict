# coding=utf-8
from geo_dict.common.levenshtein import lev_dist

relation_1 = [u'na', u'we', u'w', u'wewnątrz']
relation_2 = [u'za', u'wzdłuż', u'koło', u'przy', u'obok', u'naprzeciwko', u'przed', u'nad', u'pod', u'ponad', u'poza']
relation_3 = [u'między', u'pomiędzy']
relation_4 = [u'róg', u'rogu', u'rogiem', u'skrzyżowanie', u'skrzyżowania', u'skrzyżowaniu', u'skrzyżowaniem',
              u'wjazd', u'wjazdu', u'wjazdem', u'wyjazd', u'wyjazdu', u'wyjazdem', u'zjazd', u'zjazdu', u'zjazdem']


def has_preposition(words, relation_prepositions):
    for prep in relation_prepositions:
        for word in words:
            if lev_dist(word, prep) <= 0.75:
                return True
    return False