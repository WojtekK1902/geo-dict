import glob
import logging
import os

from ner.tools.io import save, load

FORCE_NEW_MODEL = False

BACKUP_PARTS = 100

NKJP_CORPUS_PATH = "ner/data/raw/corpus/nkjp"

NKJP_PICKLE_PATH = "ner/data/bin/corpus/nkjp.sav"

logger = logging.getLogger('nkjp')



def gen_model(output):
    try:
        if FORCE_NEW_MODEL:
            raise Exception('New model request flag set')
        model = load_nkjp_model()
        paths = set([path for path, _, _ in model])
        print paths
        logger.info('NKJP model exists, updating...')
    except:
        logger.info('Creating new NKJP model')
        model = []
        paths = set()

    all_paths = glob.glob(NKJP_CORPUS_PATH + '/*')
    for i in range(len(all_paths)):
        logger.info('Part: {} / {}'.format(i, len(all_paths)))
        path = all_paths[i]
        if not path in paths and os.path.isdir(path):
            parser = model.nkjp_parser.NKJPParser(path)
            model.append((parser.path, parser.objects, parser.plain_text))

            if i and not (i % BACKUP_PARTS):
                logger.info('Backup time!')
                save(model, output)


    save(model, output)


def load_nkjp_model():
    return load(NKJP_PICKLE_PATH)



if __name__ == "__main__":
    # gen_model(NKJP_PICKLE_PATH)

    def convert(objects):
        return tuple((phrase, word_no, obj_type.lower()) for phrase, word_no, obj_type in objects)

    model = load_nkjp_model()
    new_model = map(lambda (path, objects, plain_text): (path, convert(objects), plain_text), model)

    save(new_model, NKJP_PICKLE_PATH)
