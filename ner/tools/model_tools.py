from collections import Counter
import ner.corpus.nkjp
from ner.model.tagparser import TagNEParser


def print_plain_text(model):

    print ' '.join(' '.join(phrase) for phrase in model.plain_text)

    s =  u'[\n'
    for phrase in model.plain_text:
        tab = u'\t'
        s += tab + u'[\n' + tab + tab

        if len(phrase) > 0:
            s += u'\'{}\''.format(phrase[0])

        for w in range(1, len(phrase)):
            s += u', \'{}\''.format(phrase[w])
            if w and w != len(phrase) - 1 and not (w + 1) % 5:
                s += u'\n' + tab + tab


        s += '\n' + tab + u']\n'
    s += u']'

    print s


def print_objects(model):
    s =  '[\n'

    for o in model.objects:
        tab = '\t'
        s += tab + str(o) + '\n'


    s += ']'

    print s

def print_objects(corpus, type):
    onames = []
    for path, objects, plain_text in corpus:
        for o in objects:
            if o[TagNEParser.TYPE] == type:
                onames.append(' '.join(plain_text[o[TagNEParser.PHRASE]][word_no] for word_no in o[TagNEParser.WORD_NO]))

    for o in sorted(onames):
        print o

def print_types_stats(corpus):
    types = Counter()

    words_count = 0
    phrases_count = 0
    documents_count = 0
    NE_count = 0

    ne_to_name = []

    for path, objects, plain_text in corpus:
        documents_count += 1
        phrases_count += len(plain_text)
        words_count += sum(len(phrase) for phrase in plain_text)
        NE_count += len(objects)
        types.update([o[TagNEParser.TYPE] for o in objects])

        ne_to_name.append((len(objects), path))

    print max(ne_to_name, key= lambda x: x[0])
    print '\nTYPES RANKING:'
    for t, c in types.most_common():
        print t, c

    print '\nWords count: {}\nPhrases count: {}\nDocuments count: {}\nNE count: {}'.format(words_count, phrases_count,
                                                                                         documents_count, NE_count)



if __name__ == "__main__":
    corpus = ner.corpus.nkjp.load_nkjp_model()
    # print_types_stats(corpus)

    print_objects(corpus, 'geogName')
