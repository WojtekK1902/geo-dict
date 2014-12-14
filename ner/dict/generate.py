# -*- coding: utf-8 -*-
import codecs
from xml.etree.ElementTree import iterparse
from pydic import PyDic
import marisa_trie
import re

from ner.tools.io import load, save


STREETS_SOURCE = "../dane/slowniki/ULIC.xml"
STREETS_OUT = "../dane/slowniki/ulice.txt"
STREETS_PICKLE = "../dane/slowniki/bin/ulice.sav"

CITIES_SOURCE = "../dane/slowniki/SIMC.xml"
CITIES_OUT = "../dane/slowniki/miasta.txt"
CITIES_ODM = "../dane/slowniki/miasta_odm2.txt"
CITIES_PICKLE = "../dane/slowniki/bin/miasta.sav"

COUNTRIES_ODM = "../dane/slowniki/panstwa_odm.txt"
COUNTRIES_PICKLE = "../dane/slowniki/bin/panstwa.sav"

NAMES_SOURCE = "../dane/slowniki/names.pl.infl.utf8.txt"
NAMES_PICKLE = "../dane/slowniki/bin/imiona.sav"

SURNAMES_SOURCE = "../dane/slowniki/surnames.pl.infl.utf8.txt"
SURNAMES_PICKLE = "../dane/slowniki/bin/nazwiska.sav"

SJP_PYDIC_PATH = "/home/sjp.pydic"


def gen_streets():

    name1 = []
    name2 = []
    for event, element in iterparse(STREETS_SOURCE):
        attr = element.attrib
        if 'name' in attr and attr['name'] == "NAZWA_1":
            name1.append(element.text)
        elif 'name' in attr and attr['name'] == "NAZWA_2":
            name2.append(element.text)
        element.clear()

    names = [''.join((normalize(name2[i]), normalize(name1[i]))) + '\n' for i in range(len(name1))]

    names = filter(lambda name : not name.strip().isdigit(), names)

    with codecs.open(STREETS_OUT, "w", encoding="utf-8") as out_file:
        out_file.writelines(sorted(set(names)))


def gen_cities():

    names = set()

    for event, element in iterparse(CITIES_SOURCE):
        attr = element.attrib
        if 'name' in attr and attr['name'] == "NAZWA":
            names.add(element.text + '\n')
        element.clear()

    with codecs.open(CITIES_OUT, "w", encoding="utf-8") as out_file:
        out_file.writelines(sorted(names))





def pickle_dict(in_name, out_name):
    with  codecs.open(in_name, 'r', encoding="utf-8") as in_file:
        lines = in_file.readlines()

    d = set()

    for line in lines:
        [d.add(word) for word in re.split(',| ',line.strip()) if len(word) > 1 and word.isalpha()]

    t = marisa_trie.Trie(d)
    save(t, out_name)


def load_names_dict():
    return load(NAMES_PICKLE)

def load_surnames_dict():
    return load(SURNAMES_PICKLE)

def load_cities_dict():
    return load(CITIES_PICKLE)

def load_countries_dict():
    return load(COUNTRIES_PICKLE)

def load_streets_dict():
    return load(STREETS_PICKLE)


sjp_dic = None
def get_sjp_pydic():
    global sjp_dic
    if not sjp_dic:
        sjp_dic = PyDic(SJP_PYDIC_PATH)
    return sjp_dic

def normalize(string):
    return string or ""


if __name__ == "__main__":
    #gen_cities()
    #gen_streets()
    # pickle_dict(STREETS_OUT, STREETS_PICKLE)
    # pickle_dict(CITIES_ODM, CITIES_PICKLE)
    #pickle_dict(NAMES_SOURCE, NAMES_PICKLE)
    #pickle_dict(SURNAMES_SOURCE, SURNAMES_PICKLE)
    # pickle_dict(COUNTRIES_ODM, COUNTRIES_PICKLE)
    #gen_model(load_kpwr_corpus, KPWR_PICKLE_PATH)



    c = load(STREETS_PICKLE)
    print u'Żółkiewskiego' in c