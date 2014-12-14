# -*- coding: utf-8 -*-

import corpus2
import sys
import logging
from collections import Counter
from collections import defaultdict
from ner.model import types
from ner.model.tagparser import TagRelParser, TagNEParser
from ner.tools import model_tools


class CCLNERParser(TagNEParser):

    def __init__(self, path):
        super(CCLNERParser, self).__init__(path)
        self.tagset = corpus2.get_named_tagset('nkjp')
        self.input_format = 'ccl'
        print path
        self.reader = corpus2.TokenReader.create_path_reader(self.input_format, self.tagset, path)
        self.sent_struct = {}

        self.logger = logging.getLogger('CCLNERParser')

        self.parse()


    def parse(self):
        self.logger.debug('*****************\nParsing NE\n*****************\n')
        while True:
            chunk = self.reader.get_next_chunk()
            if not chunk:
                break

            for sent in chunk.sentences():
                asent = corpus2.AnnotatedSentence_wrap_sentence(sent)
                channels = defaultdict(list)
                for chan_name in asent.all_channels():
                    if chan_name[-4:] == '_nam':
                        chan = asent.get_channel(chan_name)
                        ann_vec = chan.make_annotation_vector()

                        for ann in ann_vec:
                            indices = tuple(ann.indices)

                            channels[chan_name].append(indices)
                            self.objects.append((len(self.plain_text), indices, chan_name))

                if self.logger.isEnabledFor(logging.DEBUG) and len(channels) > 0:
                    self.logger.debug('CHANNELS IN SENTENCE ' + str(len(self.plain_text)))
                    for channel in channels.iteritems():
                        self.logger.debug(channel[0] + ': ' + ', '.join([str(l) for l in channel[1]]))
                    self.logger.debug('')

                self.sent_struct[len(self.plain_text)] = channels

                sentence = []
                for tok in sent.tokens():
                    sentence.append(tok.orth_utf8().decode('utf-8'))

                self.plain_text.append(sentence)

        self.objects.sort(key=lambda x: (x[CCLNERParser.PHRASE], x[CCLNERParser.WORD_NO][0]))

        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug('\n=======SUMMARY=======\n')

            self.logger.debug('NAMED ENTITIES:')
            for obj in self.objects:
                self.logger.debug('SENT NO: ' + str(obj[0]) + ' TOKENS: ' + str(obj[1]) + ' TYPE: ' + str(obj[2]))

            self.logger.debug('')

            self.logger.debug('NAMED ENTITIES BY TYPES:')
            for type in self.types:
                self.logger.debug(type[0] + ': ' + str(type[1]))

            self.logger.debug('')

        if types.VALID_TYPES:
            self.objects = filter(lambda o: o[TagNEParser.TYPE] in types.VALID_TYPES, self.objects)

        model_tools.print_plain_text(self)
        model_tools.print_objects(self)

class CCLRELParser(TagRelParser):

    def __init__(self, cclparser, path):
        super(CCLRELParser, self).__init__(path)
        self.reader = corpus2.RelationReader(path)
        self.sent_struct = cclparser.sent_struct

        self.logger = logging.getLogger('CCLRELParser')

        self.parse()

    def parse(self):
        self.logger.debug('*****************\nParsing REL\n*****************\n')

        for relation in self.reader.relations():
            channel_from_name = relation.rel_from().channel_name()
            channel_to_name = relation.rel_to().channel_name()

            if relation.rel_name()[:11] == 'coreference' or relation.rel_name()[:3] == 'obj' \
                    or relation.rel_name()[:4] == 'subj' or relation.rel_name()[-6:] == '_coref':
                continue

            if channel_from_name[-4:] == '_nam' and channel_to_name[-4:] == '_nam' and relation.rel_from().sentence_id() == relation.rel_to().sentence_id():
                sent_no = int(relation.rel_from().sentence_id()[4:]) - 1
                channels = self.sent_struct[sent_no]

                channel_from = channels[relation.rel_from().channel_name()]
                rel_from = channel_from[int(relation.rel_from().annotation_number()) - 1]

                channel_to = channels[relation.rel_to().channel_name()]
                rel_to = channel_to[int(relation.rel_to().annotation_number()) - 1]

                rel_type = relation.rel_name()

                self.logger.debug('SENT NO: ' + str(sent_no) +
                              ' FROM: ' + relation.rel_from().channel_name() +
                              ' ANN NO: ' + str(relation.rel_from().annotation_number()) +
                              ' TO: ' + relation.rel_to().channel_name() +
                              ' ANN NO: ' + str(relation.rel_to().annotation_number()) +
                              ' TYPE: ' + rel_type)

                self.relations.append((sent_no, rel_from, rel_to, rel_type))

        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug('\n=======SUMMARY=======\n')

            self.logger.debug('RELATION BY TYPES:')
            for type in self.types:
                self.logger.debug(type[0] + ': ' + str(type[1]))

            self.logger.debug('')

if __name__ == '__main__':
    a = CCLNERParser('/home/sunniva/uczelnia/pjndata/kpwr-1.1/wikipedia/00100504.xml')
    b = CCLRELParser(a, '/home/sunniva/uczelnia/pjndata/kpwr-1.1/wikipedia/00100504.rel.xml')