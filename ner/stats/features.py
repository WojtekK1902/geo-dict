import logging

# from ner.dict import generate
# from ner.tools.stemmer import gen_sjp_base


logger = logging.getLogger('Features')

features_cache = {}


# names_dict = generate.load_names_dict()
# surnames_dict = generate.load_surnames_dict()
# cities_dict = generate.load_cities_dict()
# countries_dict = generate.load_countries_dict()
# streets_dict = generate.load_streets_dict()

infrequents = None


def cachable(f):
    def inner(T, S, i):
        key = (f.__name__, S[i], i)
        if key in features_cache:
            return features_cache[key]

        val = f(T, S, i)
        features_cache[key] = val
        return val

    inner.__name__ = f.__name__
    return inner



@cachable
def capital(T, S, i):
    return S[i] and S[i][0].isupper()


def sentence_beginning(T, S, i):
    return i == 0


@cachable
def infrequent(T, S, i):
    return False
    # return gen_sjp_base(S[i]) in infrequents


@cachable
def suffix(T, S, i):
    w = S[i]
    if not w or len(w) < 3:
        return None
    suff = w[-3:]
    if suff.isalpha():
        return suff
    return None


def prev_word(T, S, i):
    if i > 0:
        # return gen_sjp_base(S[i - 1])
        return S[i-1]
    return None


# ## Dictionary features ###
@cachable
def in_names_dict(T, S, i):
    return S[i] and S[i] in names_dict


@cachable
def in_surnames_dict(T, S, i):
    return S[i] and S[i] in surnames_dict


@cachable
def in_cities_dict(T, S, i):
    return S[i] and S[i] in cities_dict


@cachable
def in_countries_dict(T, S, i):
    return S[i] and S[i] in countries_dict


@cachable
def in_streets_dict(T, S, i):
    return S[i] and S[i] in streets_dict


# ## HMM features ###

@cachable
def current_word(T, S, i):
    # return gen_sjp_base(S[i])
    return S[i]


def prev_label(T, S, i):
    return T[i - 1]


VALID_FEATURES = [current_word, prev_label, prev_word, suffix, capital, sentence_beginning, infrequent]
                  # in_names_dict,
                  # in_surnames_dict,
                  # in_cities_dict,
                  # in_countries_dict]


