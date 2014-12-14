from collections import defaultdict
import logging
import os
import sys

from bs4 import BeautifulSoup
from ner.model.tagparser import TagNEParser
import tools.model_tools as model_tools


logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(message)s')

MORPHOSYNTAX_FILENAME = 'ann_morphosyntax.xml'
NE_FILENAME = 'ann_named.xml'

# Possible values : high, medium, low, unknown
ALLOWED_CERTAINTY = {'high'}  # 'medium',  'low',  'unknown'}

SUBTYPES_ALLOWED = True


class NKJPParser(TagNEParser):
    def __init__(self, path):
        super(NKJPParser, self).__init__(path)
        self.logger = logging.getLogger('NKJPParser')
        self.words_parser = BeautifulSoup(self.read_file_data(path, MORPHOSYNTAX_FILENAME))
        try:
            self.named_parser = BeautifulSoup(self.read_file_data(path, NE_FILENAME))
        except IOError:
            self.named_parser = None
        self._ignored_obj_count = 0
        self.parse()


    def read_file_data(self, path, file):
        with open(os.path.join(path, file), 'r') as f:
            return f.read()




    def is_object_valid(self, seg):
        for fTag in seg.fs.findAll('f'):
            if fTag['name'] == 'certainty':
                if fTag.symbol['value'] in ALLOWED_CERTAINTY:
                    return True
                return False
        return False

    def extract_object_type(self, seg):
        def get_type(meta_type):
            for fTag in seg.fs.findAll('f'):
                if fTag['name'] == meta_type:
                    return fTag.symbol['value'].lower()
            return None

        result_type = None
        if SUBTYPES_ALLOWED:
            result_type = get_type('subtype')

        if not result_type:
            return get_type('type')

        return result_type


    def find_valid_objects(self, namedSegs):
        namedTagsMap = defaultdict(list)
        all_objs = set()

        for k in range(len(namedSegs)):
            ids = []

            if self.is_object_valid(namedSegs[k]):

                for idTag in namedSegs[k].findAll('ptr'):
                    id = idTag['target']
                    if id.startswith('named'):
                        self.logger.debug('Found sub-NE, searching for word id...')
                        for l in range(k + 1, len(namedSegs)):
                            if namedSegs[l]['xml:id'] == id:
                                ids.append(namedSegs[l].ptr['target'])
                                self.logger.debug('Sub-NE id : ' + ids[-1])
                                break
                    else:
                        self.logger.debug('Found NE for word id: ' + id)
                        ids.append(id)

                objType = self.extract_object_type(namedSegs[k])
                obj = (tuple(ids), objType)
                all_objs.add(obj)
                for id in ids:
                    namedTagsMap[id].append(obj)
                    self.logger.debug('NE entry: ({}, {})'.format(id, namedTagsMap[id]))

            else:
                self._ignored_obj_count += 1
                self.logger.debug('Object not valid, ignoring...')

        return all_objs, namedTagsMap

    def parse(self):
        self.logger.info('### PARSING NKJP ENTRY: {}'.format(self.path))
        wordsBodyTag = self.words_parser.tei.find('text').body

        if self.named_parser:
            namedBodyTag = self.named_parser.tei.find('text').body

        wordsPTags = wordsBodyTag.findAll('p')

        if self.named_parser:
            namedPTags = namedBodyTag.findAll('p')

        pSenNo = 0
        for i in range(len(wordsPTags)):
            wordsSentenceTags = wordsPTags[i].findAll('s')

            if self.named_parser:
                namedSentenceTags = namedPTags[i].findAll('s')

            for j in range(len(wordsSentenceTags)):
                self.logger.debug('### New sentence ###')
                sentence = []

                if self.named_parser:
                    namedSegs = namedSentenceTags[j].findAll('seg')
                    all_objs, namedTagsMap = self.find_valid_objects(namedSegs)

                wordSegs = wordsSentenceTags[j].findAll('seg')
                for k in range(len(wordSegs)):
                    word = wordSegs[k].fs.f.find('string').text
                    id = MORPHOSYNTAX_FILENAME + '#' + wordSegs[k]['xml:id']
                    sentence.append(word)

                    self.logger.debug(u'Word added to sentence: {}'.format(word))
                    if self.named_parser and id in namedTagsMap:
                        for obj in namedTagsMap[id]:
                            if obj in all_objs:
                                ne_ids, ne_type = obj
                                word_no = tuple([k + w for w in range(len(ne_ids))])
                                self._objects.append((pSenNo + j, word_no, ne_type))
                                self.logger.debug('Objects for added word: {}'.format(self._objects[-1]))
                                all_objs.remove(obj)

                self._plain_text.append(sentence)
            pSenNo += len(wordsSentenceTags)

        model_tools.print_plain_text(self)
        model_tools.print_objects(self)

        for o in self._objects:
            self.logger.info(self._plain_text[o[TagNEParser.PHRASE]])
            self.logger.info('Object: {}'.format(o))
            self.logger.info('Details: {} : {}'.format(o[TagNEParser.TYPE],
                                                       [self._plain_text[o[TagNEParser.PHRASE]][no] for no in
                                                        o[TagNEParser.WORD_NO]]))

        self.logger.info('Ignored objects: {}'.format(self._ignored_obj_count))


