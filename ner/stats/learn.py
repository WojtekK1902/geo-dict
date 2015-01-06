from ner.corpus.nkjp import load_nkjp_model
from ner.model.types import filter_corpus
from ner.stats.hmm import train

if __name__ == "__main__":
    model = filter_corpus(load_nkjp_model())
    # model = load('../dane/model/temp_model.sav')
    train(model)
    # train(model[:1])
    # cProfile.run('train(model[:5])')
    # test(model[11:20])
    pass