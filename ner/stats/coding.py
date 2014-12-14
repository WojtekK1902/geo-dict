from ner.model.tagparser import TagNEParser, MockNETagParser

BOS = 'BOS'
EOS = 'EOS'

class LabelException(Exception):
    def __init__(self, msg, labels):
        super(Exception, self).__init__('{}\nlabels: {}'.format(msg, labels))

def get_type(obj):
    if obj == BOS or obj == EOS:
        return obj
    return obj[TagNEParser.TYPE].upper()


def get_object_pos_map(objects, phrase):
    objects_pos = {}
    for obj in objects:
        for pos in obj[TagNEParser.WORD_NO]:
            objects_pos[pos] = obj
    objects_pos[-1] = BOS
    objects_pos[len(phrase)] = EOS
    return objects_pos


def encode_IO(phrase, objects):
    objects_pos = get_object_pos_map(objects, phrase)
    labels = [BOS]

    for i in range(len(phrase)):

        if i in objects_pos:
            obj = objects_pos[i]
            obj_type = get_type(obj)
            labels.append('I-{}'.format(obj_type))
        else:
            labels.append('O')
    labels.append(EOS)
    return labels


def get_BMEWO_states(types):
    states = [BOS, EOS, 'W-O']

    for obj_type in types:
        obj_type = obj_type.upper()
        states.extend(
            ['W-{}'.format(obj_type), 'B-{}'.format(obj_type), 'M-{}'.format(obj_type), 'E-{}'.format(obj_type)])
    return states

def get_BMEWOP_states(types):
    states = [BOS, EOS, 'B-O-BOS', 'W-O-BOS', 'E-O-EOS', 'W-O']

    for obj_type in types:
        obj_type = obj_type.upper()
        states.extend(
            ['W-{}'.format(obj_type), 'B-{}'.format(obj_type), 'M-{}'.format(obj_type), 'E-{}'.format(obj_type),
             'B-O-{}'.format(obj_type), 'W-O-{}'.format(obj_type), 'E-O-{}'.format(obj_type)
            ])
    return states

def get_IO_states(types):
    states = [BOS, EOS, 'O']
    states.extend(['I-{}'.format(obj_type.upper()) for obj_type in types])
    return states

def encode_BMEWO(phrase, objects):
    labels = [BOS]

    objects_pos = get_object_pos_map(objects, phrase)

    for i in range(len(phrase)):

        if i in objects_pos:
            obj = objects_pos[i]
            obj_pos = obj[TagNEParser.WORD_NO]
            obj_type = get_type(obj)

            if obj_pos[0] == obj_pos[-1] == i:
                labels.append('W-{}'.format(obj_type))
            elif obj_pos[0] == i:
                labels.append('B-{}'.format(obj_type))
            elif obj_pos[-1] == i:
                labels.append('E-{}'.format(obj_type))
            elif obj_pos[0] < i < obj_pos[-1]:
                labels.append('M-{}'.format(obj_type))
        else:
            labels.append('W-O')

    labels.append(EOS)
    return labels

def encode_BMEWOP(phrase, objects):
    labels = [BOS]

    objects_pos = get_object_pos_map(objects, phrase)

    for i in range(len(phrase)):

        if i in objects_pos:
            obj = objects_pos[i]
            obj_pos = obj[TagNEParser.WORD_NO]
            obj_type = get_type(obj)

            if obj_pos[0] == obj_pos[-1] == i:
                labels.append('W-{}'.format(obj_type))
            elif obj_pos[0] == i:
                labels.append('B-{}'.format(obj_type))
            elif obj_pos[-1] == i:
                labels.append('E-{}'.format(obj_type))
            elif obj_pos[0] < i < obj_pos[-1]:
                labels.append('M-{}'.format(obj_type))

        elif i - 1 in objects_pos and i + 1 in objects_pos:
            obj = objects_pos[i - 1]
            obj_type = get_type(obj)
            labels.append('W-O-{}'.format(obj_type))
        elif i - 1 in objects_pos:
            obj = objects_pos[i - 1]
            obj_type = get_type(obj)
            labels.append('B-O-{}'.format(obj_type))
        elif i + 1 in objects_pos:
            obj = objects_pos[i + 1]
            obj_type = get_type(obj)
            labels.append('E-O-{}'.format(obj_type))
        else:
            labels.append('W-O')

    labels.append(EOS)
    return labels

def validate_BMEWOP(labels):

    i = 0
    while i < len(labels):
        content_pos = labels[i].rfind('-')
        prefix = labels[i][:content_pos]
        content = labels[i][content_pos+1:]

        if prefix == 'B':
            obj = content
            i+=1
            while i < len(labels):
                prefix = labels[i][:content_pos]
                content = labels[i][content_pos+1:]

                if prefix != 'M' and prefix != 'E':
                    raise LabelException('Object begins, but not ends: {}, prefix={}'.format(content, prefix), labels)

                if content != obj:
                    raise LabelException('Content with incorrect type: {}, should be: {}'.format(content, obj), labels)

                i+=1
                if prefix == 'E':
                    break


        elif prefix == 'M' or prefix == 'E':
            raise LabelException('Incorrect label outside object: {}'.format(labels[i]), labels)

        i+= 1


def decode_IO(phrase_no, labels):
    objects = []
    current_obj_pos = []
    current_obj_type = None
    for i in range(len(labels)):
        if labels[i].startswith('I-'):
            type = labels[i][2:]
            if not current_obj_type:
                current_obj_type = type
                current_obj_pos.append(i-1)
            elif current_obj_type != type:
                objects.append((phrase_no, tuple(current_obj_pos), current_obj_type.lower()))
                current_obj_type = type
                current_obj_pos = [i-1]
        elif current_obj_type:
            objects.append((phrase_no, tuple(current_obj_pos), current_obj_type.lower()))
            current_obj_type = None
            current_obj_pos = []
    return objects


def decode_BMEWO(phrase_no, labels):

    objects = []
    current_object_pos = []
    for i in range(len(labels)):
        content_pos = labels[i].rfind('-')
        prefix = labels[i][:content_pos]
        content = labels[i][content_pos+1:]

        if prefix == 'W' and content != 'O':
            objects.append((phrase_no, (i-1,), content.lower()))
        elif prefix == 'B':
            current_object_pos = [i-1]
        elif prefix == 'M':
            current_object_pos.append(i-1)
        elif prefix == 'E':
            current_object_pos.append(i-1)
            for j in range(len(current_object_pos) - 1):
                if current_object_pos[j+1] - current_object_pos[j] != 1:
                    raise LabelException('', labels)

            objects.append((phrase_no, tuple(current_object_pos), content.lower()))

    return objects

def decode_BMEWOP(phrase_no, labels):

    objects = []
    current_object_pos = []
    for i in range(len(labels)):
        content_pos = labels[i].rfind('-')
        prefix = labels[i][:content_pos]
        content = labels[i][content_pos+1:]

        if prefix == 'W' and content != 'O':
            objects.append((phrase_no, (i-1,), content.lower()))
        elif prefix == 'B':
            current_object_pos = [i-1]
        elif prefix == 'M':
            current_object_pos.append(i-1)
        elif prefix == 'E':
            current_object_pos.append(i-1)
            for j in range(len(current_object_pos) - 1):
                if current_object_pos[j+1] - current_object_pos[j] != 1:
                    raise LabelException('', labels)

            objects.append((phrase_no, tuple(current_object_pos), content.lower()))

    return objects





if __name__ == "__main__":
    parser = MockNETagParser('')
    parser.type = 'source'

    phrases_objects = [[] for i in range(len(parser.plain_text))]
    for obj in parser.objects:
        phrases_objects[obj[TagNEParser.PHRASE]].append(obj)

    for i in range(len(parser.plain_text)):
        phrase = parser.plain_text[i]
        objects = phrases_objects[i]

        labels = encode_BMEWOP(phrase, objects)

        print phrase
        print objects
        print labels

        print '***'






