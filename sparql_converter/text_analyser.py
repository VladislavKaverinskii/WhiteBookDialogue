# -*- coding: utf-8 -*-
import os
from argparse import ArgumentParser
import json
import nltk



# подгружает пакеты, если их нет
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('maxent_treebank_pos_tagger')
nltk.download('treebank')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger_ru')


from text_analysis_handlers import *

class GrahBuilder:
    def __init__(self):
        self.sentance_analyzer = SentenceAnalyzer()
        self.auxiliary_preprocessor = AuxiliaryPreprocessors()

    def draw(self, in_file_path="text.txt", sentences_n="all"):
        encoding = chardet.detect(open(in_file_path, 'rb').read())["encoding"]
        f = open(in_file_path, 'r', encoding=encoding)
        document = f.read()
        f.close()

        sent_no = None
        if sentences_n != "all":
            sent_no = [int(i) for i in sentences_n.split(",")]

        text = self.auxiliary_preprocessor.clear_hyphenations(self.auxiliary_preprocessor.remove_junk_symbols(document))

        sentences = nltk.sent_tokenize(text)  # разбиваем на предложения

        sentences_1 = [nltk.word_tokenize(sent) for sent in sentences]  # предложения разбиваем на слова

        sent_counter = 0  # Счётчик предложений
        for sent in sentences_1:
            if sent_no is not None:
                if sent_counter not in sent_no:
                    sent_counter += 1
                    continue

            self.sentance_analyzer.analize_sentance(sentences[sent_counter])
            self.sentance_analyzer.print_graph()
            self.sentance_analyzer.graw_graph()
            sent_counter += 1



if __name__ == "__main__":

    parser = ArgumentParser(description='Text Analysis Service')
    parser.add_argument(
        '-i', '--input', help='Path to a text file with an initial text.', dest='input_file', default='text.txt')
    parser.add_argument(
        '-a', '--action', help='An operation you are to do with the text. Options: get_ontology, view_graphs', dest='action', default='get_ontology')
    parser.add_argument(
        '-l', '--language', help='Language of the text. Options: uk, ru.', dest='lang', default='uk')
    parser.add_argument(
        '-f', '--format', help='Format of an output file (owl only).', dest='file_format', default='owl')
    args, unknown = parser.parse_known_args()
    del (unknown)

    set_language(args.lang)
    from foreign_libraries import morph, stemmer_obj
    from analitic_tools import SentenceAnalyzer

    # visualizator = GrahBuilder()
    # visualizator.draw(in_file_path=args.input_file)

    if args.action == 'get_ontology':
        handler = TermParser()
        if args.file_format == "owl":
            handler.save_owl_file(in_file_path=args.input_file, out_file_path='')
        else:
            print(args.format, " is not supported.")
            exit(1)


    exit(0)












