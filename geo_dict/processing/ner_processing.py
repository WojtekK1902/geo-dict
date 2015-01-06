# -*- coding: utf-8 -*-
from ner.dict import generate
from ner.model import tagparser

import ner.stats.coding as coding
import ner.stats.hmm as hmm
# import ner.stats.crf as crf

streets_dict = generate.load_streets_cracow_dict()


def compare_with_dict(obj_words, dict_words):
    dict_len = len(dict_words)
    obj_len = len(obj_words)
    max_i = min(obj_len, dict_len)

    score = 0
    for i in range(max_i):
        if obj_words[i] == dict_words[i]:
            score += 1/obj_len
        else:
            return score
    return score

def find_streets(words):
    print '### {} ###'.format(words)
    # model = crf.ConditionalRandomFiels.load_from_file()
    model = hmm.HiddenMarkovModel.load_from_file()
    labels = model.get_best_labelings(words, 64)

    print  max(labels, key=lambda x : -x[1])

    p_sum = sum([label[1] for label in labels])


    d_sum = 0
    d_score = []
    for l, p in labels:
        dict_score = 0
        for object in l:
            obj_words = [words[i] for i in object[tagparser.TagNEParser.WORD_NO]]
            first_word = obj_words[0]
            if first_word in streets_dict:

                dict_score += max(compare_with_dict(obj_words, dict_words) for dict_words in streets_dict[first_word])


        d_score.append(dict_score + 1)
        d_sum += dict_score + 1


    for i in range(len(labels)):
        l, p = labels[i]

        basic_p = p/p_sum
        dict_p = d_score[i] / d_sum

        labels[i] = (l, 0.3 * basic_p + 0.7 * dict_p)




    # for label in sorted(labels, key=lambda x : -x[1]):

    print  max(labels, key=lambda x : -x[1])


def find_places(words):
    pass


# find_streets([u'Spotkajmy', u'się', u'na', u'Rynku',u'Głównym', u'obok', u'ul',u'.', u'Floriańskiej', u'.'])