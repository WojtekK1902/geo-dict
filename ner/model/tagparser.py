# -*- coding: utf-8 -*-
import collections


class TagParser(object):
    def __init__(self, path):
        self.path = path

    @property
    def types(self):
        raise NotImplementedError()


class TagNEParser(TagParser):
    PHRASE = 0
    WORD_NO = 1
    TYPE = 2

    def __init__(self, path):
        super(TagNEParser, self).__init__(path)
        self._plain_text = []
        self._objects = []

    @property
    def objects(self):
        return self._objects

    @objects.setter
    def objects(self, value):
        self._objects = value

    @property
    def plain_text(self):
        return self._plain_text

    @plain_text.setter
    def plain_text(self, value):
        self.plain_text = value

    @property
    def types(self):
        counter = collections.Counter()
        counter.update(tag[TagNEParser.TYPE] for tag in self.objects)
        return counter.most_common()

class TagRelParser(TagParser):
    PHRASE = 0
    OBJECT_FROM_NO = 1
    OBJECT_TO_NO = 2
    TYPE = 3

    def __init__(self, path):
        super(TagRelParser, self).__init__(path)
        self._relations = []

    @property
    def relations(self):
        return self._relations

    @relations.setter
    def relations(self, value):
        self._relations = value

    @property
    def types(self):
        counter = collections.Counter()
        counter.update(tag[TagRelParser.TYPE] for tag in self.relations)
        return counter.most_common()

class MockNETagParser(TagNEParser):

    @property
    def plain_text(self):
        return [[u"Ala", u"ma", u"kota", u"."], [u"A", u"kot", u"ma", u"Alę", u"i", u"Boba", u"Borubarowskiego"]]

    @property
    def objects(self):
        if self.type == 'source':
            return [(0, (0,), u"osoba"), (0, (2,), u"zwierz"), (1, (1,), u"zwierz"), (1, (3,), u"osoba"), (1, (5,6), u"osoba")]
        else:
            return [(0, (0,), u"zwierz"), (0, (1,), u"osoba"), (0, (2,), u"zwierz"), (1, (3,), u"osoba"), ]


class MockRelTagParser(TagRelParser):

    @property
    def relations(self):
        if self.type == 'source':
            return [(0, (0,), (2,), u"posiada"), (1, (1,), (3,), u"dręczy"), (1, (1,), (5,6), u"dręczy")]
        else:
            return [(0, (1,), (2,), u"posiada"), (1, (1,), (3,), u"dręczy"), (1, (1,), (5,6), u"posiada")]

