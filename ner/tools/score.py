import codecs
from collections import defaultdict

from ner.model import types

from ner.model.tagparser import TagNEParser, TagRelParser
from ner.model.types import VALID_TYPES, TYPES_INDEX


TRUE_POSITIVE = "True Positive"
WRONG_MATCH = "Wrong Match"
FALSE_NEGATIVE = "False Negative"
FALSE_POSITIVE = "False Positive"


def compute_object_scores(source_objects, result_objects):
    full_match_set = set(source_objects)

    position_match_set = set((s[TagNEParser.PHRASE], s[TagNEParser.WORD_NO]) for s in source_objects)
    types_for_position = defaultdict(set)
    for obj in source_objects:
        types_for_position[(obj[TagNEParser.PHRASE], obj[TagNEParser.WORD_NO])].add(obj[TagNEParser.TYPE])

    scores = defaultdict(list)

    scores[TRUE_POSITIVE] = []
    scores[FALSE_POSITIVE] = []
    scores[WRONG_MATCH] = []
    scores[FALSE_NEGATIVE] = []

    for result in result_objects:
        result_pos = (result[TagNEParser.PHRASE], result[TagNEParser.WORD_NO])

        if result_pos in position_match_set:
            if result[TagNEParser.TYPE] in types_for_position[result_pos]:
                score_class = TRUE_POSITIVE
                full_match_set.remove((result_pos[0], result_pos[1], result[TagNEParser.TYPE]))
            else:
                score_class = WRONG_MATCH

        else:
            score_class = FALSE_POSITIVE

        scores[score_class].append(result)

    scores[FALSE_POSITIVE].extend(scores[WRONG_MATCH])
    scores[FALSE_NEGATIVE].extend(full_match_set)

    return scores


def compute_relations_scores(source_relations, result_relations):
    full_match_set = set(source_relations)
    position_match_set = set(
        (s[TagRelParser.PHRASE], s[TagRelParser.OBJECT_FROM_NO], s[TagRelParser.OBJECT_TO_NO]) for s in
        source_relations)
    types_for_position = {}
    for rel in source_relations:
        types_for_position[
            (rel[TagRelParser.PHRASE], rel[TagRelParser.OBJECT_FROM_NO], rel[TagRelParser.OBJECT_TO_NO])] = rel[
            TagRelParser.TYPE]

    scores = defaultdict(list)

    scores[TRUE_POSITIVE] = []
    scores[FALSE_POSITIVE] = []
    scores[WRONG_MATCH] = []
    scores[FALSE_NEGATIVE] = []

    for result in result_relations:
        result_pos = (
            result[TagRelParser.PHRASE], result[TagRelParser.OBJECT_FROM_NO], result[TagRelParser.OBJECT_TO_NO])

        if result_pos in position_match_set:
            if types_for_position[result_pos] == result[TagRelParser.TYPE]:
                score_class = TRUE_POSITIVE

            else:
                score_class = WRONG_MATCH

            full_match_set.remove((result_pos[0], result_pos[1], result_pos[2], types_for_position[result_pos]))

        else:
            score_class = FALSE_POSITIVE

        scores[score_class].append(result)

    scores[FALSE_POSITIVE].extend(scores[WRONG_MATCH])
    scores[FALSE_NEGATIVE].extend(full_match_set)

    return scores


def precision(scores):
    return len(scores[TRUE_POSITIVE]) > 0 and len(scores[TRUE_POSITIVE]) / float(
        len(scores[TRUE_POSITIVE]) + len(scores[FALSE_POSITIVE])) or 0


def recall(scores):
    return len(scores[TRUE_POSITIVE]) > 0 and len(scores[TRUE_POSITIVE]) / float(
        len(scores[TRUE_POSITIVE]) + len(scores[FALSE_NEGATIVE])) or 0


def f1(scores):
    p = precision(scores)
    r = recall(scores)
    return p + r > 0 and (2 * p * r) / (p + r) or 0


def merge_metrics(metrics_list):
    result_metrics = defaultdict(list)

    for m in metrics_list:
        result_metrics[TRUE_POSITIVE].extend(m[TRUE_POSITIVE])
        result_metrics[FALSE_POSITIVE].extend(m[FALSE_POSITIVE])
        result_metrics[WRONG_MATCH].extend(m[WRONG_MATCH])
        result_metrics[FALSE_NEGATIVE].extend(m[FALSE_NEGATIVE])

    return result_metrics


def print_metrics_map(metrics):
    for t in sorted(metrics, key=lambda m: m in TYPES_INDEX and TYPES_INDEX[m] or -1):
        print_metrics(merge_metrics(metrics[t]), t)


def print_metrics(metrics, type):
    print type
    print 'TP: ', len(metrics[TRUE_POSITIVE])
    print 'FP: ', len(metrics[FALSE_POSITIVE])
    print 'FN: ', len(metrics[FALSE_NEGATIVE])
    print 'WM: ', len(metrics[WRONG_MATCH])

    print ''
    print 'Precision: ', precision(metrics)
    print 'Recall: ', recall(metrics)
    print 'F1: ', f1(metrics)

    print '*****************\n'


def convert_to_latex(metrics_file):
    metrics = None
    with codecs.open(metrics_file, 'r', encoding="utf-8") as in_file:
        metrics = parse_metrics(in_file.readlines())

    def format_float(s):
        return '%.3f' % float(s)

    lines = []
    if metrics:
        for caption, m_list in metrics:
            lines.append(u'\\begin{table}[h]')
            lines.append(u'\t\\begin{center}')
            lines.append(
                u"\t\t\\begin{tabular}{ >{\\centering\\arraybackslash}m{2cm} | >{\\centering\\arraybackslash}m{1cm}  "
                u">{\\centering\\arraybackslash}m{1cm} >{\centering\\arraybackslash}m{1cm} ||"
                u">{\\centering\\arraybackslash}m{1.5cm} >{\\centering\\arraybackslash}m{1.5cm} "
                u">{\\centering\\arraybackslash}m{1.5cm}}")
            lines.append(u'\t\t\t& TP & FP & FN & Precision & Recall & F1 \\\\')
            lines.append(u'\t\t\t\\hline')

            for m_dict in m_list[1:]:
                lines.append(u'\t\t\t{} & {} & {} & {} & {} & {} & \\textbf{{{}}}  \\\\'.format(
                    m_dict['type'],
                    m_dict['TP'], m_dict['FP'], m_dict['FN'],
                    format_float(m_dict['Precision']),
                    format_float(m_dict['Recall']),
                    format_float(m_dict['F1'])))
            all_line = m_list[0]
            lines.append(u'\t\t\t\\hline')
            lines.append(u'\t\t\t\\hline')
            lines.append(
                u' & \\textbf{{{}}} & \\textbf{{{}}} & \\textbf{{{}}} & \\textbf{{{}}} & \\textbf{{{}}} & \\textbf{{{}}}  \\\\'.format(
                    all_line['TP'], all_line['FP'], all_line['FN'],
                    format_float(all_line['Precision']),
                    format_float(all_line['Recall']),
                    format_float(all_line['F1'])))
            lines.append(u'\t\t\\end{tabular}')
            lines.append(u'\t\t\\caption{{{}}}'.format(caption))
            lines.append(u'\t\\end{center}')
            lines.append(u'\\end{table}\n')

    for line in lines:
        print line


def parse_metrics(metrics_lines):
    m_dict = {}

    global_result = []
    for line in metrics_lines:
        if line.strip() != '':
            if line.startswith('='):
                caption = line[5:-7]
                result = []
                global_result.append((caption, result))
            elif ':' in line:
                key, val = tuple(w.strip() for w in line.split(':'))
                m_dict[key] = val
            elif line.startswith('*'):
                result.append(m_dict)
                m_dict = {}
            else:
                t = line.strip()
                m_dict['type'] = t in types.DISPLAY_NAMES and types.DISPLAY_NAMES[t] or t

    return global_result


def compute_metrics_for_types(real_objects, matched_objects, global_metrics, name):
    # print '==== {} ===='.format(name)
    for t in VALID_TYPES:
        filtered_real = filter(lambda o: o[TagNEParser.TYPE] == t, real_objects)
        filtered_matched = filter(lambda o: o[TagNEParser.TYPE] == t, matched_objects)
        metrics = compute_object_scores(filtered_real, filtered_matched)
        # print_metrics(metrics, t)
        global_metrics[t].append(metrics)

    metrics = compute_object_scores(real_objects, matched_objects)
    # print_metrics(metrics, 'all')
    global_metrics['all'].append(metrics)

    # print '*****************\n'
    return metrics


if __name__ == "__main__":
    convert_to_latex('../dane/rezultaty/hmm_training.txt')