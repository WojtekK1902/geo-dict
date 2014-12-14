# -*- coding: utf-8 -*-

import ner.stats.coding as coding
import ner.stats.hmm as hmm

def find_streets(words):
    model = hmm.HiddenMarkovModel.load_from_file()
    label = model.infer_labeling(words)
    phrase_objects = coding.decode_BMEWOP(0, label)
    print phrase_objects


def find_places(words):
    pass


find_streets([u'Spotkajmy', u'się', u'na', u'Rynku',u'Głównym', u'obok', u'ul',u'.', u'Floriańskiej', u'.'])