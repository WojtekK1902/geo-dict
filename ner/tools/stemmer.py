import pickle
from collections import Counter
import struct
from ner.dict import generate

DICT_FILE = 'ner/data/dict/clp.sav'
SUFF_FILE = 'ner/data/dict/suffixes.sav'

base_form_cache = {}

def read_dict():
    input_s = open(DICT_FILE, 'rb')
    return pickle.load(input_s)

def read_suffixes():
    input_s = open(SUFF_FILE, 'rb')
    return pickle.load(input_s)

t = read_dict()
suffixes = read_suffixes()

def gen_base(word):
    forms = []
    tempw = word[::-1]
    while not forms and tempw:
        forms = t.items(tempw)
        tempw = tempw[:-1]

    c = Counter()
    for form, ei in forms:
        # print form[::-1]
        i = struct.unpack('<I', ei)
        c[suffixes[i[0]]] +=1

    if len(c) > 0:
        result = c.most_common()[0][0]
    # print result

        toCut = len(result[0])
        if toCut > 0:
            word = word[:-toCut]

        word += result[1]

    return word


def gen_sjp_base(symbol):
    if not symbol:
        return None
    if symbol in base_form_cache:
        return base_form_cache[symbol]
    base = generate.get_sjp_pydic().word_base(symbol)
    result = base and base[0] or symbol
    base_form_cache[symbol] = result
    return result

if __name__ == "__main__":
    print gen_base(u'bubaczanego')

