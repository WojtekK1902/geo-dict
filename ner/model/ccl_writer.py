# -*- coding: utf-8 -*-

import corpus2
from collections import defaultdict
from ner.model.tagparser import TagNEParser, TagRelParser
#from ccl_parser import CCLNERParser, CCLRELParser

class CCLNERWriter(object):
    IOB_BEGIN = 1
    IOB_CONTINUATION = 2

    def __init__(self, path):
        self.tagset = corpus2.get_named_tagset('nkjp')
        self.input_format = 'ccl'
        self.writer = corpus2.TokenWriter.create_path_writer(self.input_format, path, self.tagset)

    def write(self, plain_text, objects):
        chunk = corpus2.Chunk()
        i = 0
        channels_by_sentence, channels_by_sentence_and_word = self.get_channels(objects)
        for sent in plain_text:
            s = corpus2.AnnotatedSentence()
            s.set_id('sent' + str(i + 1))
            channels_map = {}

            for channel_name in channels_by_sentence[i]:
                channel = corpus2.AnnotationChannel()
                s.add_channel(channel_name.encode('utf-8'), channel)
                channels_map[channel_name] = channel

            for token in sent:
                t = corpus2.Token()
                t.set_orth_utf8(token.encode('utf-8'))
                s.append(t.clone())

            marked_ne = channels_by_sentence_and_word[i]

            for j in range(len(sent)):
                for ne_type, iob in marked_ne[j]:

                    for channel_name in s.all_channels():
                        channel = s.get_channel(channel_name)
                        if channel_name == ne_type:
                            channel.set_iob_at(j, iob)

            for channel_name in s.all_channels():
                channel = s.get_channel(channel_name)
                channel.make_segments_from_iob()
            chunk.append(s.clone_shared())

            i += 1

        self.writer.write_chunk(chunk.clone_shared())
        self.writer.finish()

    @staticmethod
    def get_channels(objects):
        channels_by_sentence = defaultdict(list)
        channels_by_sentence_and_word = defaultdict(lambda : defaultdict(list))

        for obj in objects:
            phrase_no = obj[TagNEParser.PHRASE]
            ne_type = obj[TagNEParser.TYPE]
            words = obj[TagNEParser.WORD_NO]

            channels_by_sentence[phrase_no].append(ne_type)
            channels_by_sentence_and_word[phrase_no][words[0]].append((ne_type.encode('utf-8'), CCLNERWriter.IOB_BEGIN))

            if len(words) > 1:
                for j in range(1, len(words)):
                    channels_by_sentence_and_word[phrase_no][words[j]].\
                        append((ne_type.encode('utf-8'), CCLNERWriter.IOB_CONTINUATION))

        return channels_by_sentence, channels_by_sentence_and_word

class CCLRELWriter(object):
    def __init__(self, path):
        self.writer = corpus2.RelationWriter(path)

    def write(self, relations, sent_struct):
        struct = self.reverse_sent_struct(sent_struct)
        relation_objects = []

        for rel in relations:
            phrase_no = rel[TagRelParser.PHRASE]
            phrase_id = 'sent' + str(rel[TagRelParser.PHRASE] + 1)
            channel_from, ann_number_from = struct[phrase_no][rel[TagRelParser.OBJECT_FROM_NO]]
            channel_to, ann_number_to = struct[phrase_no][rel[TagRelParser.OBJECT_TO_NO]]
            rel_name = rel[TagRelParser.TYPE].encode('utf-8')

            rel_from = corpus2.DirectionPoint(phrase_id, channel_from, ann_number_from)
            rel_to = corpus2.DirectionPoint(phrase_id, channel_to, ann_number_to)

            relation = corpus2.Relation(rel_name, rel_from, rel_to)

            relation_objects.append(relation.clone_shared())

        self.writer.write(relation_objects)

    pass

    @staticmethod
    def reverse_sent_struct(sent_struct):
        rev = defaultdict(lambda : defaultdict(tuple))
        for sent_no, sent_channels in sent_struct.iteritems():
            for channel_name, annotations in sent_channels.iteritems():
                for ann_no, ann in enumerate(annotations):
                    rev[sent_no][ann] = channel_name, ann_no
        return rev

# if __name__ == '__main__':
    # a = CCLNERWriter("test.xml")
    # plain_text = [[u"Ala", u"ma", u"kota", u"."], [u"A", u"kot", u"ma", u"Alę", u"i", u"Boba" , u"Kowalskiego"]]
    # objects = [(0, (0,), u"osoba_nam"), (0, (2,), u"zwierz_nam"), (1, (1,), u"zwierz_nam"), (1, (3,), u"osoba_nam"), (1, (5, ), u"imie_nam"), (1, (5, 6), u"osoba_nam")]
    #
    # a.write(plain_text, objects)

    #
    # b_pars = CCLNERParser("test.xml")
    # b = CCLRELWriter("test.rel.xml")
    # relations = [(0, (0,), (2,), u"posiada"), (1, (1,), (3,), u"dreczy"), (1, (1,), (5, 6), u"dreczy")]
    #
    # b.write(relations, b_pars.sent_struct)

    #rel_pars = CCLRELParser(b_pars, "test.rel.xml")