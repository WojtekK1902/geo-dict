import glob
from ner.model.ccl_parser import CCLNERParser
from ner.tools.io import save, load

KPWR_CORPUS_PATH = "../dane/kpwr-1.1"

KPWR_PICKLE_PATH = "../dane/kpwr.sav"


def load_kpwr_corpus():
    parsers = []

    for filename in glob.glob(KPWR_CORPUS_PATH + '/*/*.xml'):
        if filename.find('rel') == -1:
            parsers.append(CCLNERParser(filename))
    return parsers


def load_kpwr_model():
    return load(KPWR_PICKLE_PATH)


def gen_model(corpus_generator, output):
    model = []

    for parser in corpus_generator():
        model.append((parser.path, parser.objects, parser.plain_text))
        print parser.objects

    save(model, output)

if __name__ == "__main__":
    gen_model(load_kpwr_corpus, KPWR_PICKLE_PATH)