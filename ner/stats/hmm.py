# -*- coding: utf-8 -*-
from collections import Counter, defaultdict
import heapq
from itertools import groupby
import logging
import sys
import time

# from corpus.kpwr import load_kpwr_model
# from model.ccl_writer import CCLNERWriter
# from ner.corpus.kpwr import load_kpwr_model
from ner.corpus.nkjp import load_nkjp_model
from ner.model.tagparser import TagNEParser
from ner.model.types import VALID_TYPES, filter_corpus
from ner.stats.coding import BOS, EOS, get_BMEWOP_states, encode_BMEWOP, decode_BMEWOP, validate_BMEWOP, LabelException
from ner.tools import score
from ner.tools.io import save, load


logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(message)s')

HMM_PATH = "ner/data/bin/model/hmm.sav"

logger = logging.getLogger('HiddenMarkovModel')


class HiddenMarkovModel(object):
    def __init__(self):
        self.transitions = Counter()
        self.emissions = Counter()
        self.states = get_BMEWOP_states(VALID_TYPES)
        self.transition_factors = {}
        self.emission_factors = {}
        self.symbols = set()
        self.hapax_logomena_distribution = {}

    @staticmethod
    def load_from_file(path=HMM_PATH):
        return load(path)

    def learn(self, text_data):
        for file, objects, phrases in text_data:

            logger.debug('Updating HMM for:%s', file)

            object_groups = {}
            for phrase_id, objects in groupby(objects, lambda obj: obj[TagNEParser.PHRASE]):
                object_groups[phrase_id] = list(objects)

            for phrase_id in range(1, len(phrases)):
                phrase = phrases[phrase_id]
                if phrase_id in object_groups:
                    phrase_objects = object_groups[phrase_id]
                else:
                    phrase_objects = []

                labels = encode_BMEWOP(phrase, phrase_objects)
                try:
                    validate_BMEWOP(labels)
                    # print phrase, phrase_objects
                    self.update_model(phrase, labels)
                    self.symbols.update(phrase)
                except LabelException, e:
                    logger.warning(e.message)

        logger.debug('\n=== Stats for HMM ===\n')
        logger.debug('Symbols number: %i', len(self.symbols))
        logger.debug('Transitions top 10: %s', self.transitions.most_common(10))
        for t, c in self.transitions.most_common():
            logger.debug('(%s -> %s) : %s' % (t[0], t[1], c))

        logger.debug('Emissions top 10: %s', self.emissions.most_common(10))

        logger.debug('\nComputing factors...')
        self.compute_hmm_parameters()

        logger.debug('\nFinding hapax logomena...')
        self.find_hapax_logomena()

        logger.debug('\nFinding overall distribution...')
        self.find_overall_distribution()

        logger.debug('\nHMM learning complete!')

    def get_base(self, symbol):
        return symbol
        # return gen_sjp_base(symbol)

    def emission_probability(self, symbol, label):
        return self.hapax_logomena_EP(self.get_base(symbol), label)

    def transition_probability(self, label1, label2):
        if (label1, label2) in self.transitions:
            P = self.transitions[(label1, label2)]
        else:
            P = 0

        return self.transition_factors[label1] and float(P) / self.transition_factors[label1] or 0

    def basic_EP(self, symbol, label):
        if (symbol, label) in self.emissions:
            P = self.emissions[(symbol, label)]
        else:
            P = 0

        return self.emission_factors[label] and float(P) / self.emission_factors[label] or 0

    def laplace_smoothing_EP(self, symbol, label):
        if (symbol, label) in self.emissions:
            P = self.emissions[(symbol, label)] + 1
        else:
            P = 1

        return float(P) / (self.emission_factors[label] + len(self.symbols))

    def hapax_logomena_EP(self, symbol, label):
        if (symbol, label) in self.emissions:
            P = self.emissions[(symbol, label)]
        else:
            return self.hapax_logomena_distribution[label]

        return float(P) / self.emission_factors[label]

    def overall_distribution_EP(self, symbol, label):
        if (symbol, label) in self.emissions:
            P = self.emissions[(symbol, label)]
        else:
            return self.overall_distribution[label]

        return float(P) / self.emission_factors[label]

    def find_hapax_logomena(self):

        c = Counter()
        c.update([e[0] for e in self.emissions])

        possible_hapaxes = [entry[0] for entry in filter(lambda x: x[1] == 1, c.most_common())]

        self.hapax_logomena_distribution = {}

        for s in self.states:
            state_distribution = [self.basic_EP(h, s) for h in possible_hapaxes]
            self.hapax_logomena_distribution[s] = sum(state_distribution) / len(state_distribution)
            logger.debug('%s %s', s, self.hapax_logomena_distribution[s])

    def find_overall_distribution(self):
        self.overall_distribution = {}

        for s in self.states:
            state_emissions = filter(lambda e: e[1] == s, self.emissions)
            state_distribution = [self.basic_EP(*e) for e in state_emissions]
            self.overall_distribution[s] = state_distribution and min(
                state_distribution) or 0  # state_distribution and sum(state_distribution)/len(state_distribution) or 0
            logger.debug('%s %s', s, self.overall_distribution[s])


    def update_model(self, phrase, labels):
        for i in range(len(phrase) + 1):
            self.transitions.update([(labels[i], labels[i + 1])])

            if i < len(phrase):
                self.emissions.update([(self.get_base(phrase[i]), labels[i + 1])])
                if phrase[i] == u'Polsce':
                    print u' '.join(phrase)

    def compute_hmm_parameters(self):
        for state in self.states:
            state_transitions = filter(lambda t: t[0][0] == state, self.transitions.most_common())
            self.transition_factors[state] = sum(t[1] for t in state_transitions)

            state_emissions = filter(lambda e: e[0][1] == state, self.emissions.most_common())
            self.emission_factors[state] = sum(e[1] for e in state_emissions)


    def compute_viterbi_probability(self, v, i, k, n_best, ek, phrase):
        for l in self.states:
            for j in range(len(v[(i - 1, l)])):
                p, _, _ = v[(i - 1, l)][j]
                new_p = p * self.transition_probability(l, k) * ek
                if (i, k) not in v:
                    v[(i, k)] = []
                if new_p > 0:
                    if len(v[(i, k)]) < n_best:
                        heapq.heappush(v[(i, k)], (new_p, l, j))
                    else:
                        heapq.heappushpop(v[(i, k)], (new_p, l, j))

    def infer_labeling(self, phrase, n_best=1):
        v = {}
        for k in self.states:
            v[(-1, k)] = []
            heapq.heappush(v[(-1, k)], (0, None, None))

        v[(-1, BOS)] = []
        heapq.heappush(v[(-1, BOS)], (1, None, None))

        for i in range(len(phrase)):
            logger.debug(phrase[i])

            for k in self.states:
                logger.debug(k)
                ek = self.emission_probability(phrase[i], k)
                logger.debug('emission : e(%s), state %s: %s', phrase[i], k, ek)

                self.compute_viterbi_probability(v, i, k, n_best, ek, phrase)

                # l, p = max([(l, v[(i - 1, l)][0] * self.transition_probability(l, k)) for l in self.states],
                # key=lambda x: x[1])
                # logger.debug('transition: %s -> %s : %s', l, k, p)
                # v[(i, k)] = (ek * p, l)
                # logger.debug('current k=%s : %s', k, label_paths[k])

        # labelings = sorted([(l, v[(len(phrase) - 1, l)][0] * self.transition_probability(l, EOS)) for l in self.states],
        # key=lambda x: -x[1])

        self.compute_viterbi_probability(v, len(phrase), EOS, n_best, 1, phrase)

        labelings = []
        for p, l, prev_l in v[(len(phrase), EOS)]:
            label = [EOS]
            i = len(phrase) - 1
            while i >= -1:
                label.append(l)
                _, l, prev_l = v[(i, l)][prev_l]
                i -= 1

            labelings.append((list(reversed(label)), p))

        return labelings


    def get_best_labeling(self, phrase, phrase_no=0):
        return self.get_best_labelings(phrase, 1, phrase_no)[0]

    def get_best_labelings(self, phrase, N, phrase_no=0):
        return [(decode_BMEWOP(phrase_no, label), p) for label, p in self.infer_labeling(phrase, N)]


def train(model):
    hmm = HiddenMarkovModel()

    previous_time = time.time()
    hmm.learn(model)
    logger.info('training time: {}'.format(time.time() - previous_time))

    save(hmm, HMM_PATH)

    print '**Transitions***'

    for trans in hmm.transitions:
        print trans, hmm.transition_probability(*trans)

        # exit(0)


def test_local():
    p = [u'Spotkajmy', u'się', u'na', u'Rynku', u'Głównym', u'obok', u'ul', u'.', u'Floriańskiej', u'.']
    hmm = load(HMM_PATH)
    label = hmm.infer_labeling(p)

    print p
    print decode_BMEWOP(0, label)


def test(model):
    hmm = HiddenMarkovModel.load_from_file()
    global_metrics = defaultdict(list)

    complex_ne_count = 0
    complex_ne_found = 0

    previous_time = time.time()

    def get_complex_ne_count(objects, real_objects):
        return len(filter(lambda o: o in real_objects and len(o[TagNEParser.WORD_NO]) > 1, objects))

    for i in range(len(model)):
        real_objects = model[i][1]
        complex_ne_count += get_complex_ne_count(real_objects, real_objects)
        matched_objects = []
        for j in range(len(model[i][2])):
            label = hmm.infer_labeling(model[i][2][j])

            phrase_objects = decode_BMEWOP(j, label)
            complex_ne_found += get_complex_ne_count(phrase_objects, real_objects)

            matched_objects.extend(phrase_objects)
            logger.info(phrase_objects)
            logger.info(model[i][2][j])
            logger.info('best labeling: %s\n', label)
        m = score.compute_metrics_for_types(real_objects, matched_objects, global_metrics, model[i][0])


        # if len(matched_objects) > 3 and f1(m) > 0.5:
        # # t_real = set(map(lambda o : o[TagNEParser.TYPE], phrase_objects))
        # # t_found = set(map(lambda o : o[TagNEParser.TYPE], matched_objects))
        #
        # # if len(t_found) == len(t_real) and len(t_real) > 1:
        # if model[i][0] == '../dane/kpwr-1.1/wikipedia/00100521.xml':
        # writer = CCLNERWriter('test.ccl')
        # writer.write(model[i][2], matched_objects)
        # exit(0)

    print '\n==== Global results ====\n'
    score.print_metrics_map(global_metrics)

    print 'Phrases in model : {}'.format(sum([len(text[2]) for text in model]))

    logger.info('Complex NE count: {}'.format(complex_ne_count))
    logger.info('Complex NE found: {}'.format(complex_ne_found))

    logger.info('Testing time: {}'.format(time.time() - previous_time))

    return global_metrics


def unknown_words_stat(model):
    N = len(model)
    all_phrases = sum([len(text[2]) for text in model])
    step = all_phrases / 5

    phrases_count = 0
    j = 0
    while j < N and phrases_count < step:
        phrases_count += len(model[j][2])
        j += 1

    test_model = model[0:j]

    test_words = set()
    for i in range(len(test_model)):
        for j in range(len(model[i][2])):
            test_words.update(model[i][2][j])

    hmm = load(HMM_PATH)

    logger.info('Training words: {}'.format(len(hmm.symbols)))
    logger.info('Test words: {}'.format(len(test_words)))
    logger.info('Unkwnown words: {}'.format(len(filter(lambda w: w not in hmm.symbols, test_words))))


def cross_validation(model):
    N = len(model)

    all_phrases = sum([len(text[2]) for text in model])
    step = all_phrases / 5

    global_metrics = defaultdict(list)

    i = 0
    while i < N:

        phrases_count = 0
        j = i
        while j < N and phrases_count < step:
            phrases_count += len(model[j][2])
            j += 1

        train_model = model[0:i] + model[j:N]
        test_model = model[i:j]

        train(train_model)
        metrics = test(test_model)

        for t in metrics:
            global_metrics[t].extend(metrics[t])

        i = j

    print '\n==== Cross validation global results ====\n'
    score.print_metrics_map(global_metrics)


if __name__ == "__main__":
    model = filter_corpus(load_nkjp_model())
    train(model)
    # cross_validation(model)
    # unknown_words_stat(model)
    # test_local()









