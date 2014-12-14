from collections import defaultdict, Counter
from itertools import groupby
import logging
import math
import sys
import time
from ner.corpus.kpwr import load_kpwr_model

import features
from ner.model.tagparser import TagNEParser
from ner.model.types import filter_corpus, VALID_TYPES
from ner.stats.coding import BOS, EOS, LabelException, get_BMEWOP_states, encode_BMEWOP, decode_BMEWOP
from ner.tools import score
from ner.tools.io import save, load
from ner.tools.stemmer import gen_sjp_base


CRF_PATH = "../dane/model/crf_hmm.sav"

LEARN_MAX_N = 50

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(message)s')
logger = logging.getLogger('ConditionalRandomFiels')


class ZipfDict:

    LIMIT = 0.5

    def __init__(self):
        self.c = Counter()

    def update(self, words):
        self.c.update([gen_sjp_base(w) for w in words])

    def find_limit(self):

        all_words = sum(self.c.values())
        n_words =  self.LIMIT * all_words

        words_counter = 0
        pos = 0
        vals = []

        results = self.c.most_common()

        for word, val in reversed(results):
            words_counter += val
            vals.append(val)
            if words_counter > n_words:
                break
            pos += 1

        return pos

    def infrequents(self):
        return set(w for w,c in self.c.most_common()[-self.find_limit():])

class FeatureValSet:
    def __init__(self):
        self._val_to_weight = defaultdict(list)
        self._non_zero_weights = set()
        self._weights_history = {}

    def add(self, val):
        self._val_to_weight[val] = [(0, 0)]

    def has_val(self, val):
        return val in self._val_to_weight

    def weight(self, val):
        return self._val_to_weight[val][-1][1]

    def change_to_average(self, N):
        for val in self._val_to_weight:
            self._val_to_weight[val].append((0, self.compute_average_weight(val, N)))

    def compute_average_weight(self, val, N):
        weights = self._val_to_weight[val]
        prev_w = 0
        prev_i = 0
        w_sum = 0

        for i, w in weights:
            w_sum += (i - prev_i) * prev_w
            prev_w = w
            prev_i = i
        w_sum += (N - prev_i) * prev_w

        return w_sum / N


    def weights(self):
        return self._val_to_weight.values()

    def set_weight(self, val, weight, i):

        self._val_to_weight[val].append((i, weight))
        if weight:
            self._non_zero_weights.add(val)
        elif val in self._non_zero_weights:
            self._non_zero_weights.remove(val)

    def rescore(self, divider):
        for val in self._non_zero_weights:
            self._val_to_weight[val] = [w / divider for n, w in self._val_to_weight[val]]

    def __str__(self):
        return self._val_to_weight.__str__()


class ConditionalRandomFiels(object):
    def __init__(self):
        self.transitions = Counter()
        self.emissions = Counter()
        self.states = get_BMEWOP_states(VALID_TYPES)

        self.symbols = set()
        self.training_model = []

        self.features = []
        self.features_map = defaultdict(lambda: defaultdict(FeatureValSet))

        self.freq_dict = ZipfDict()

    def learn(self, text_data):

        logger.info('Generating features set...')
        self.gen_features()

        for file, objects, phrases in text_data:

            logger.debug('Updating CRF transitions and emissions base for: %s', file)

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
                    # validate_BMEWOP(labels)

                    self.update_model(phrase, labels)
                    self.symbols.update(phrase)
                except LabelException as e:
                    logger.info('Wrong training set labeling for phrase, omiting example: {}'.format(phrase))
                    logger.info(e)

        logger.info('Freq dict calculation...')
        infrequents = self.freq_dict.infrequents()
        features.infrequents = infrequents

        logger.info('Initializing features map...')
        self.init_features_map()

        logger.info('Estimating CRF parameters...')
        self.estimate_parameters()

        logger.info('Learning complete')
        print_weights(self.features_map)


    def gen_features(self):
        self.features = features.VALID_FEATURES


    def estimate_parameters(self):


        logger.debug('Training model size: {}'.format(len(self.training_model)))
        divider = 100

        previous_time = time.time()
        weights_history = defaultdict(list)

        for t in range(LEARN_MAX_N):

            global_weight_changes = []
            weight_changes = 0

            for phrase_id in range(len(self.training_model)):
                phrase, labeling = self.training_model[phrase_id]
                logger.debug('New weights calculation iteration')
                new_weights = []
                weight_gains = []

                estimated_labeling = self.infer_labeling(phrase)

                if labeling != estimated_labeling:
                    for f_index in range(len(self.features)):

                        f_name = self.features[f_index].__name__

                        real_features_map = self.calculate_feature_val_sparse_matrix(labeling, phrase,
                                                                                     f_index)
                        estimated_features_map = self.calculate_feature_val_sparse_matrix(
                            estimated_labeling,
                            phrase,
                            f_index)

                        for state, val in set(real_features_map.keys() + estimated_features_map.keys()):
                            real_features_val = real_features_map[state, val]
                            estimated_features_val = estimated_features_map[state, val]

                            delta = (real_features_val - estimated_features_val) / float(divider)

                            if delta:
                                new_weight = self.features_map[state][f_name].weight(val) + delta

                                logger.debug(u'Phrase: {}'.format(phrase))
                                logger.debug(u'Real: {}'.format(labeling))
                                logger.debug(u'Estimated: {}'.format(estimated_labeling))
                                logger.debug(u'Weight change: real={}, estimated={},feat name={}, new weight={}'.format(
                                    real_features_val, estimated_features_val, self.features[f_index].__name__,
                                    new_weight))

                                # weights_history[f_index].append(
                                # (t * len(self.training_model) + phrase_id, new_weight))

                                new_weights.append((state, f_name, val, new_weight))

                            weight_gains.append(real_features_val - estimated_features_val)
                            if weight_gains[-1]:
                                weight_changes += 1

                if new_weights:
                    for state, f_name, val, weight in new_weights:
                        self.features_map[state][f_name].set_weight(val, weight, t * len(self.training_model) + phrase_id)


                global_weight_changes.append(weight_gains and sum(weight_gains) / float(len(weight_gains)) or 0)

            new_time = time.time()
            logger.info('time={}'.format(new_time - previous_time))
            previous_time = new_time
            logger.info('{} {}'.format(weight_changes, sum(global_weight_changes) / float(len(global_weight_changes))))

            if weight_changes == 0:
                t += 1
                break

        for f_dict in self.features_map.values():
            for f_set in f_dict.values():
                f_set.change_to_average(t * len(self.training_model))



    def calculate_feature_val_sparse_matrix(self, states, symbols, f_index):
        result = defaultdict(lambda: 0)
        for i in range(len(symbols) - 1):
            f_val = self.features[f_index](states, symbols, i + 1)
            f_name = self.features[f_index].__name__
            state = states[i + 1]
            result[state, f_val] += self.features_map[state][f_name].has_val(f_val) and 1 or 0

        return result


    def update_model(self, phrase, labels):
        base_phrase = [None] + phrase + [None]
        self.training_model.append((base_phrase, labels))
        self.freq_dict.update(phrase)


    def init_features_map(self):
        for base_phrase, labels in self.training_model:

            for i in range(len(base_phrase) - 1):
                for j in range(len(self.features)):
                    curr_label = labels[i + 1]
                    feat_name = self.features[j].__name__
                    feat_val = self.features[j](labels, base_phrase, i + 1)
                    self.features_map[curr_label][feat_name].add(feat_val)


    def compute_features(self, states, symbols, i):
        feat_score = 0

        for j in range(len(self.features)):
            f_val = self.features[j](states, symbols, i)
            state = states[i]
            f_name = self.features[j].__name__

            if self.features_map[state][f_name].has_val(f_val):
                feat_score += self.features_map[state][f_name].weight(f_val)

        return math.exp(feat_score)


    def check_transition_valid(self, t1, t2):
        if t2 == BOS:
            return False
        if t2 == EOS:
            return t1 == 'E-O-EOS' or (not t1.startswith('E-O-') and t1.startswith('E-')) or (
                t1 != 'W-O' and not t1.startswith('W-O-') and t1.startswith('W-'))
        if t2.startswith('B-O-'):
            t = t2[4:]
            return t1 == 'W-' + t or t1 == 'E-' + t or t == t1 == BOS
        if t2.startswith('E-O-'):
            return t1 == 'W-O' or t1.startswith('B-O-')
        if t2.startswith('E-') or t2.startswith('M-'):
            t = t2[2:]
            return t1 == 'M-' + t or t1 == 'E-' + t
        if t2 == 'W-O':
            return t1.startswith('B-O-') or t1 == 'W-O'
        if t2.startswith('W-O-'):
            t = t2[4:]
            return t1 == 'E-' + t or t1 == 'W-' + t or t1 == t == BOS
        if t2.startswith('B-') or t2.startswith('W-'):
            t = t2[2:]
            return t1 == BOS or t1 == 'E-' + t or t1 == 'E-O-' + t or t1 == 'W-O-' + t or t1 == 'W-' + t

        raise LabelException('Not known state', [t1, t2])


    def compute_viterbi_probability(self, v, i, k, phrase):
        probabilities = []
        for l in self.states:
            viterbi_state = v[(i - 1, l)]
            # if self.check_transition_valid(l, k):

            new_states = viterbi_state[1] + [k]
            probabilities.append((l, viterbi_state[0] * self.compute_features(new_states, phrase, i + 1)))
            # else:
            # probabilities.append((l, viterbi_state[0]))

        l, p = max(probabilities, key=lambda x: x[1])
        v[(i, k)] = (p, v[(i - 1, l)][1] + [k])

    def infer_labeling(self, phrase):
        v = {}
        for k in self.states:
            v[(-1, k)] = (0, [k])
        v[(-1, BOS)] = (1, [BOS])

        for i in range(len(phrase) - 1):
            for k in self.states:
                self.compute_viterbi_probability(v, i, k, phrase)

        last_state = len(phrase) - 2
        self.compute_viterbi_probability(v, last_state, EOS, phrase)


        return v[last_state, EOS][1]

def print_weights(features_map):
    for l in features_map:
        logger.info('Label: {}'.format(l))
        for f in features_map[l]:
            logger.info('    {} : {}'.format(f, features_map[l][f]))


def train(model):
    crf = ConditionalRandomFiels()
    crf.learn(model)

    save(crf, CRF_PATH)


def test_different_weights(model, crf):

    old_crf_map = crf.features_map
    new_crf_map =  defaultdict(lambda: defaultdict(FeatureValSet))

    for state in old_crf_map:
        for feat_name in old_crf_map[state]:
            for val in old_crf_map[state][feat_name]._val_to_weight:
                new_crf_map[state][feat_name].set_weight(val, old_crf_map[state][feat_name]._val_to_weight[val][0][1], 0)

    test_set_size =  len(crf.training_model)
    crf.features_map = new_crf_map


    for i in range(2, LEARN_MAX_N):
        for state in new_crf_map:
            for feat_name in new_crf_map[state]:
                for val in new_crf_map[state][feat_name]._val_to_weight:
                    last_index = new_crf_map[state][feat_name]._val_to_weight[val][-1][0]

                    old_feat_val = old_crf_map[state][feat_name]._val_to_weight[val]
                    while last_index < len(old_feat_val) and old_feat_val[last_index][0] < i * test_set_size:
                        last_index += 1

                    last_index -= 1
                    new_crf_map[state][feat_name].set_weight(val, old_feat_val[last_index][1], last_index - 1)

        previous_time = time.time()
        test(model, crf)
        new_time = time.time() - previous_time
        logger.info('{}) Time: {}'.format(i, new_time))







def test(model, crf):


    global_metrics = defaultdict(list)
    complex_ne_count = 0
    complex_ne_found = 0

    def get_complex_ne_count(objects, real_objects):
        return len(filter(lambda o: o in real_objects and len(o[TagNEParser.WORD_NO]) > 1, objects))

    for i in range(len(model)):
        real_objects = model[i][1]
        complex_ne_count += get_complex_ne_count(real_objects, real_objects)
        matched_objects = []
        for j in range(len(model[i][2])):
            base_phrase = [None] + model[i][2][j] + [None]
            label = crf.infer_labeling(base_phrase)

            try:
                phrase_objects = decode_BMEWOP(j, label)
                complex_ne_found += get_complex_ne_count(phrase_objects, real_objects)
                matched_objects.extend(phrase_objects)
                # logger.info(phrase_objects)
                # logger.info(model[i][2][j])
                # logger.info('best labeling: %s\n', label)
            except LabelException as e:
                logger.error(e)
        # logger.info('Real objects: {}'.format(real_objects))
        m = score.compute_metrics_for_types(real_objects, matched_objects, global_metrics, model[i][0])
        # if len(matched_objects) > 3 and f1(m) > 0.5:
        # writer = CCLNERWriter('test.ccl')
        # writer.write(model[i][2], matched_objects)
        # exit(0)

    print '\n==== Global results ====\n'
    score.print_metrics_map(global_metrics)

    print 'Phrases in model : {}'.format(sum([len(text[2]) for text in model]))

    logger.info('Complex NE count: {}'.format(complex_ne_count))
    logger.info('Complex NE found: {}'.format(complex_ne_found))

    return global_metrics


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

        # train(train_model)


        crf = load(CRF_PATH)
        features.infrequents = crf.freq_dict.infrequents()

        previous_time = time.time()
        metrics = test(test_model, crf)
        new_time = time.time() - previous_time
        logger.info('Time: {}'.format(new_time))

        for t in metrics:
            global_metrics[t].extend(metrics[t])

        i = j

        # just for testing
        break

    print '\n==== Cross validation global results ====\n'
    score.print_metrics_map(global_metrics)


if __name__ == "__main__":
    model = filter_corpus(load_kpwr_model())
    # model = load('../dane/model/temp_model.sav')
    cross_validation(model)
    # train(model[:1])
    # cProfile.run('train(model[:5])')
    # test(model[11:20])
