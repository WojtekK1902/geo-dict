# import dill as pickle
import pickle
__author__ = 'Soamid'


def load(file):
    with open(file, 'rb') as handle:
        return pickle.load(handle)


def save(struct, file):
    with open(file, 'wb') as handle:
        pickle.dump(struct, handle)