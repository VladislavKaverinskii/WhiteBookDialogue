# -*- coding: utf-8 -*-

import os
import json
import chardet

from owlready2 import *
import xml.etree.ElementTree as ET

from analitic_tools import *
from foreign_libraries import *


class AuxiliaryPreprocessors:
    '''
    Вспомагательные методы, служащие для предварительной подготовки исходного текста для анализа.
    '''

    def __init__(self):
        # Список допустимых в тексте символов:
        self.allowed_symbols = {'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'a', 's', 'd', 'f', 'g', 'h', 'j',
                                'k', 'l', 'z', 'x', 'c', 'v', 'b', 'n',
                                'm', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'A', 'S', 'D', 'F', 'G', 'H',
                                'J', 'K', 'L', 'Z', 'X', 'C', 'V', 'B',
                                'N', 'M', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '!', '@', '#', '$', '%',
                                '^', '&', '*', '(', ')', '-', '_', '=',
                                '+', ',', '.', '?', '<', '>', '{', '}', '[', ']', ':', ';', '|', '\\', '/', '№', '\n',
                                '\t', "й", "ц", "у", "к",
                                "е", "н", "г", "ш", "щ", "з", "х", "ъ", "ф", "ы", "в", "а", "п", "р", "о", "д", "л",
                                "ж", "э", "я", "ч", "с", "м", "и", "т", "ь",
                                "б", "ю", "Й", "Ц", "У", "К", "Е", "Н", "Г", "Ш", "Щ", "З", "Х", "Ъ", "Ф", "Ы", "В",
                                "А", "П", "Р", "О", "Л", "Д", "Ж", "Э",
                                "Я", "Ч", "С", "М", "И", "Т", "Ь", "Б", "Ю", "Ё", "І", "ё", "і", "ї", "Ї", "є", "Є",
                                " ", "—"}

    def remove_junk_symbols(self, text):
        """
        Функция для удаления из текста "мусорных" символов
        :param text:
        :return: cleaned text
        """
        cleaned_text = ""  # Сюда записывается очищенный текст
        if isinstance(text, str):  # Проверяем, что переданный текст является строкой
            for symbol in text:  # Перебираем все символы в тексте
                if symbol in self.allowed_symbols:  # Если данный символ числится в списке разрешённых,
                    # добавляем его к тексту для вывода
                    cleaned_text += symbol
        return cleaned_text.strip()  # Убираем начальные и конечные пробельные символы, если таковые имеются

    def clear_hyphenations(self, text):
        """
        Функция, предназначенная для склейки перенесённых слов в тексте
        :param text:
        :return: text without hyphenations
        """
        cleaned_text = ""  # Перемення для хранения преодразованного текста
        list_of_words = nltk.word_tokenize(text)  # Разбиваем текст на слова
        # Перебираем все слова из полученного списка
        counter = 0
        for word in list_of_words:
            if "-" in word:  # Если в слове встретился дефис оно подлежит проверке
                # Рассматривается 3 потенциальных варианта: дефис вначале слова, дефис вконце слова, слово с дефисом в середине
                # Отдельно сотящие дефисы не рассматривались. Они редко возникаеют как следствие переносов и часто ими заменяют тире.
                if word[-1] == "-":  # Дефис вконце слова
                    if counter + 1 < len(list_of_words):  # Проверяем, есть ли слово, идущее после после данного
                        # Если такое слово есть, "приклеиваем" его к данному убрав дефис
                        tmp_word = "".join(word.split("-")) + list_of_words[counter + 1]
                        if morph.word_is_known(tmp_word):  # Проверяем, есть ли такое слово в словаре
                            cleaned_text += tmp_word  # Если слово, полученное в результате склейки в словаре есть,
                            # присоединяем его к формироуемому на выходе тексту
                            del list_of_words[counter + 1]  # вторую половину удаляем из исходного текста,
                            # чтобы предотвратить её рассмотрение как слова
                        else:
                            # Если слова, полученного в результате склейки в словаре нет, просто присодиняем данное
                            # слово с его дефисом к формироуемому на выходе тексту
                            cleaned_text += word
                    else:
                        # Если слово в тексте является последини (бальше слов нет), то просто присоединяем его как есть
                        cleaned_text += word
                elif word[0] == "-":  # Дефис вначале слова
                    if counter > 0:  # Проверяем, что слово не является первым словом в тексте
                        # (в противном случае склеивать его несчем)
                        # Объединяем данное слово с предыдущим убрав дефис
                        tmp_word = list_of_words[counter - 1] + "".join(word.split("-"))
                        if morph.word_is_known(
                                tmp_word):  # Если слово, полученное в качестве результата склейки есть в словаре
                            # Добавляем результат склейки к формруемому тексту найденный фрагмент без пробела.
                            cleaned_text += tmp_word
                        else:
                            # Если варианта, полученного после склейки по дефису в словаре нет, то оставляем как есть
                            cleaned_text += word
                    else:
                        # Если сново в дефисом в начле является первым в тексте, то оставляем как есть.
                        cleaned_text += word
                else:  # Если дефис всередине слова
                    tmp_word = "".join(word.split("-"))  # Склеиваем половинки без дефиса
                    if morph.word_is_known(tmp_word):  # Проверяем наличие в словаре реультата склейки
                        # Если такое слово есть, добавляем результат склейки
                        cleaned_text += tmp_word
                    else:
                        # Если такого слова нет, оставляем как есть
                        cleaned_text += word
            else:
                if counter + 1 == len(list_of_words):
                    cleaned_text += word
                elif not list_of_words[counter + 1][0] == "-":
                    cleaned_text += word
            if counter + 1 == len(list_of_words):
                cleaned_text += " "
            elif (list_of_words[counter + 1] != "," and list_of_words[counter + 1] != "." and
                  list_of_words[counter + 1] != ";" and list_of_words[counter + 1] != ":" and
                  list_of_words[counter + 1] != "!" and list_of_words[counter + 1] != "?"):
                if len(cleaned_text) > 0:
                    if cleaned_text[-1] != " ":
                        cleaned_text += " "
                else:
                    cleaned_text += " "
            counter += 1
        return cleaned_text.strip()

    def replace_prohibited_xml_symbols(xml_text):
        out = "&amp;".join(xml_text.split("&"))
        tmp = [i for i in out]
        n = 0
        for i in tmp:
            if i == "<":
                k = n + 1
                while k < len(tmp) - 1:
                    if tmp[k] == ">":
                        break
                    if tmp[k] == "<":
                        tmp[n] = "&lt;"
                        break
                    k += 1
            if i == ">":
                k = n + 1
                while k < len(tmp) - 1:
                    if tmp[k] == "<":
                        break
                    if tmp[k] == ">":
                        tmp[k] = "&gt;"
                        break
                    k += 1

            n += 1

        out = "".join(tmp)
        return out


class WordParser:
    """
    Класс для разбора слов передложения и установления связай между ними
    """

    def __init__(self):
        # Инициализируем класс анализатора предложений
        self.sentance_analyzer = SentenceAnalyzer()
        self.auxiliary_preprocessor = AuxiliaryPreprocessors()

    def get_schema(self, document, sentences_n="all"):
        """
        Функция для получения схемы (графа) синтаксического разбора предложений текста
        :param document: Текст документа
        :param sentences_n: для каких предложений выполнить анализ
        :return:
        """

        out_schema = []

        sent_no = None
        if sentences_n != "all":
            # Получаем из строки список предложений, для которых выполнять анализ
            sent_no = [int(i) for i in sentences_n.split(",")]

        text = self.auxiliary_preprocessor.clear_hyphenations(self.auxiliary_preprocessor.remove_junk_symbols(document))

        sentences = nltk.sent_tokenize(text)  # разбиваем на предложения

        sentences_1 = [nltk.word_tokenize(sent) for sent in sentences]  # предложения разбиваем на слова

        sentences_items = []  # Список найденных слов

        sent_counter = 1  # Счётчик предложений
        for sent in sentences_1:  # Перебираем предложения
            if sent_no is not None:
                # Определяем надо ли анлизировать данное предложение
                if sent_counter not in sent_no:
                    sent_counter += 1
                    continue
            # Выполняем синтаксический анализ каждого предложения
            self.sentance_analyzer.analize_sentance(sentences[sent_counter - 1])
            # Получаем схему синтаксического разбора
            out_schema.append(self.sentance_analyzer.serialyze())
            sent_counter += 1
        return out_schema


    def preprocess(self, document, sentences_n="all"):
        """
        Функция выполняющая анализ текста
        :param document: Текст документа
        :param sentences_n: для каких предложений выполнить анализ
        :return:
        """

        sent_no = None
        if sentences_n != "all":
            # Получаем из строки список предложений, для которых выполнять анализ
            sent_no = [int(i) for i in sentences_n.split(",")]

        text = self.auxiliary_preprocessor.clear_hyphenations(self.auxiliary_preprocessor.remove_junk_symbols(document))

        sentences = nltk.sent_tokenize(text)  # разбиваем на предложения

        sentences_1 = [nltk.word_tokenize(sent) for sent in sentences]  # предложения разбиваем на слова

        sentences_items = []  # Список найденных слов

        sent_counter = 1  # Счётчик предложений
        for sent in sentences_1:  # Перебираем предложения
            if sent_no is not None:
                # Определяем надо ли анлизировать данное предложение
                if sent_counter not in sent_no:
                    sent_counter += 1
                    continue
            # Выполняем синтаксический анализ каждого предложения
            self.sentance_analyzer.analize_sentance(sentences[sent_counter - 1])
            # Получаем схему синтаксического разбора
            schema = self.sentance_analyzer.serialyze()

            # Получаем части предложения (если оно сложное)
            parts = self.sentance_analyzer.check_if_sentence_is_complex(sentences[sent_counter - 1])
            parts_of_speach = []

            # Определяем части речи для слов
            for list_of_words in parts:
                parts_of_speach += self.sentance_analyzer.define_spech(list_of_words)

            # Находим связанные группы
            word_linked_groups = self.find_linked_groups(schema)

            word_counter = 1  # Счётчик слов в предложении
            sentence = {
                'items': [],
                'sentnumber': str(sent_counter),
                'sent': sentences[sent_counter - 1]
            }
            position_counter = 1
            for word in sent:
                item = {}
                item["word"] = word
                item["osnova"] = stemmer_obj.stem(word)

                item["lemma"] = ""

                for word_links_dict in schema:
                    if "group_self_characteristics" not in word_links_dict and "words" not in word_links_dict:
                        if word_links_dict["id"] == word_counter:
                            item["lemma"] = self.__check_right_pos__(word_links_dict)
                            break
                    elif "group_self_characteristics" in word_links_dict and "words" in word_links_dict:
                        for word_links_subdict in word_links_dict["words"]:
                            if word_links_subdict["id"] == word_counter:
                                item["lemma"] = self.__check_right_pos__(word_links_subdict)
                                break

                item["flex"] = self.get_ending(word)
                item["kflex"] = ""  # Что это?
                item["number"] = str(word_counter)

                item["group_n"] = ""
                group_n = 0
                while group_n < len(word_linked_groups):
                    if word_counter in word_linked_groups[group_n]:
                        item["group_n"] = str(group_n)
                        break
                    group_n += 1

                item["speech"] = "99"
                for point in parts_of_speach:
                    if point[2] == word_counter:
                        item["speech"] = point[1]

                if item["speech"] == "99":
                    position_counter -= 1

                item["pos"] = str(position_counter)

                item["relate"] = ""
                item["rel_type"] = ""
                for word_links_dict in schema:
                    if "group_self_characteristics" not in word_links_dict and "words" not in word_links_dict:
                        relation = self.__find_relations__(word_links_dict, word_counter)
                        if relation is not None:
                            item["relate"], item["rel_type"] = relation
                    elif "group_self_characteristics" in word_links_dict and "words" in word_links_dict:
                        for word_links_subdict in word_links_dict["words"]:
                            relation = self.__find_relations__(word_links_subdict, word_counter)
                            if relation is not None:
                                item["relate"], item["rel_type"] = relation

                sentence['items'].append(item)
                word_counter += 1

                for s in word:
                    position_counter += 1
                position_counter += 1

            sentences_items.append(sentence)
            sent_counter += 1

        return sentences_items

    def __check_right_pos__(self, obj):
        p = morph.parse(obj["word"])
        for option in p:
            tmp_pos = option.tag.POS
            if tmp_pos == "VERB":
                try:
                    if "infn" in option.tag:
                        tmp_pos = "INFN"
                except ValueError:
                    tmp_pos = "VERB"
            if obj["pos"] == tmp_pos:
                return option.normal_form

    def __find_relations__(self, word_links_dict, word_counter):
        if word_links_dict["id"] == word_counter:
            relate = [str(w[1]) for w in word_links_dict['dependens_on']]
            if len(relate) < 1:
                relate += [str(w[1]) for w in word_links_dict['probably_dependens_on']]
            rel_type = [str(w[2]) for w in word_links_dict['dependens_on']]
            if len(rel_type) < 1:
                rel_type += [str(w[2]) for w in word_links_dict['probably_dependens_on']]
            if len(relate) > 0:
                return (relate[0], rel_type[0])
            else:
                return ("", "")
        elif word_links_dict['preposition'][1] == word_counter and word_links_dict['preposition'][1] != 0:
            return (str(word_links_dict["id"]), 'preposition')
        elif word_links_dict['particle'][1] == word_counter and word_links_dict['particle'][1] != 0:
            return (str(word_links_dict["id"]), 'particle')
        return None

    def find_linked_groups(self, schema):
        groups = []
        schema_work = copy.deepcopy(schema)
        while len(schema_work) > 0:
            current_group = set()
            current_group.add(schema_work[0]["id"])
            if "group_self_characteristics" not in schema_work[0] and "words" not in schema_work[0]:
                if len(schema_work[0]['dependens_on']) > 0:
                    current_group.add(schema_work[0]['dependens_on'][0][1])
                elif len(schema_work[0]['probably_dependens_on']) > 0:
                    current_group.add(schema_work[0]['probably_dependens_on'][0][1])
                if schema_work[0]['preposition'][1] != 0:
                    current_group.add(schema_work[0]['preposition'][1])
                if schema_work[0]['particle'][1] != 0:
                    current_group.add(schema_work[0]['particle'][1])
            elif "group_self_characteristics" in schema_work[0] and "words" in schema_work[0]:
                if schema_work[0]["id"] in current_group:
                    if len(schema_work[0]["group_self_characteristics"]['dependens_on']) > 0:
                        current_group.add(schema_work[0]["group_self_characteristics"]['dependens_on'][0][1])
                    elif len(schema_work[0]["group_self_characteristics"]['probably_dependens_on']) > 0:
                        current_group.add(schema_work[0]["group_self_characteristics"]['probably_dependens_on'][0][1])
                    for item in schema_work[0]["words"]:
                        current_group.add(item['id'])
                        if item['preposition'][1] != 0:
                            current_group.add(item['preposition'][1])
                        if item['particle'][1] != 0:
                            current_group.add(item['particle'][1])

            counter = 1
            while counter < len(schema_work):
                if "group_self_characteristics" not in schema_work[counter] and "words" not in schema_work[counter]:
                    if schema_work[counter]["id"] in current_group:
                        if len(schema_work[counter]['dependens_on']) > 0:
                            current_group.add(schema_work[counter]['dependens_on'][0][1])
                        elif len(schema_work[counter]['probably_dependens_on']) > 0:
                            current_group.add(schema_work[counter]['probably_dependens_on'][0][1])
                        if schema_work[counter]['preposition'][1] != 0:
                            current_group.add(schema_work[counter]['preposition'][1])
                        if 'particle' in schema_work[counter]:
                            if schema_work[counter]['particle'][1] != 0:
                                current_group.add(schema_work[counter]['particle'][1])
                elif "group_self_characteristics" in schema_work[counter] and "words" in schema_work[counter]:
                    if schema_work[counter]["id"] in current_group:
                        if len(schema_work[counter]["group_self_characteristics"]['dependens_on']) > 0:
                            current_group.add(schema_work[counter]["group_self_characteristics"]['dependens_on'][0][1])
                        elif len(schema_work[counter]["group_self_characteristics"]['probably_dependens_on']) > 0:
                            current_group.add(
                                schema_work[counter]["group_self_characteristics"]['probably_dependens_on'][0][1])
                        for item in schema_work[counter]["words"]:
                            current_group.add(item['id'])
                            if item['preposition'][1] != 0:
                                current_group.add(item['preposition'][1])
                            if item['particle'][1] != 0:
                                current_group.add(item['particle'][1])

                counter += 1
            groups.append(copy.deepcopy(current_group))
            counter = 0
            while counter < len(schema_work):
                if schema_work[counter]["id"] in current_group:
                    schema_work.remove(schema_work[counter])
                    counter -= 1
                counter += 1

        groups = [list(item) for item in groups]

        counter = 0
        while counter < len(groups):
            for i in groups[counter]:
                if counter + 1 < len(groups):
                    counter_2 = counter + 1
                    while counter_2 < len(groups):
                        if i in groups[counter_2]:
                            groups[counter] += groups[counter_2]
                            groups.remove(groups[counter_2])
                            counter_2 -= 1
                        counter_2 += 1
            counter += 1

        groups = [set(item) for item in groups]
        return groups

    def get_ending(self, word):
        osn = stemmer_obj.stem(word)
        return word[len(osn):]

    def make_xml(self, document, sentences_n="all"):
        """
        Вызывает разбор морфологический разбор слов текста и сохраняет результаты разбора в xml
        :param in_file_path:
        :param out_file_path:
        :return:
        """

        data = self.preprocess(document, sentences_n)
        text = '<?xml version="1.0" encoding="windows-1251"?>\n'
        text += '<document>\n'
        text += '\t<text>\n'

        for sentance in data:
            text += '\t\t<sentence>\n'
            for item in sentance['items']:
                text += '\t\t\t<item>\n'
                text += '\t\t\t\t<word>' + item['word'] + "</word>\n"
                text += '\t\t\t\t<osnova>' + item['osnova'] + "</osnova>\n"
                if item['lemma'] is None:
                    item['lemma'] = ""
                text += '\t\t\t\t<lemma>' + item['lemma'] + "</lemma>\n"
                text += '\t\t\t\t<kflex>' + item['kflex'] + "</kflex>\n"
                text += '\t\t\t\t<flex>' + item['flex'] + "</flex>\n"
                text += '\t\t\t\t<number>' + item['number'] + "</number>\n"
                text += '\t\t\t\t<pos>' + item['pos'] + "</pos>\n"
                text += '\t\t\t\t<group_n>' + item['group_n'] + "</group_n>\n"
                text += '\t\t\t\t<speech>' + item['speech'] + "</speech>\n"
                text += '\t\t\t\t<relate>' + item['relate'] + "</relate>\n"
                text += '\t\t\t\t<rel_type>' + item['rel_type'] + "</rel_type>\n"
                text += '\t\t\t</item>\n'
            text += '\t\t\t<sentnumber>' + sentance['sentnumber'] + '</sentnumber>\n'
            text += '\t\t\t<sent>' + sentance['sent'] + '</sent>\n'
            text += '\t\t</sentence>\n'

        text += '\t</text>\n'
        text += '</document>\n'

        return text

    def make_json(self, document, sentences_n="all"):
        """
        Вызывает разбор морфологический разбор слов текста и сохраняет результаты разбора в json
        :param in_file_path:
        :param out_file_path:
        :return:
        """

        data = self.preprocess(document, sentences_n)
        json_data = {
            "encoding": "windows-1251",
            "document": {
                "text": {
                    "sentences": [
                    ]
                }
            }
        }

        for sentance in data:
            sentance_json = {
                "items": []
            }
            for item in sentance['items']:
                item = {
                    "word": item['word'],
                    "osnova": item['osnova'],
                    "lemma": item['lemma'],
                    "kflex": item['kflex'],
                    "flex": item['flex'],
                    "number": item['number'],
                    "pos": item['pos'],
                    "group_n": item['group_n'],
                    "speech": item['speech'],
                    "relate": item['relate'],
                    "rel_type": item['rel_type']
                }

                sentance_json["items"].append(item)
            sentance_json["sentnumber"] = sentance['sentnumber']
            sentance_json["sent"] = sentance['sent']

            json_data["document"]["text"]["sentences"].append(sentance_json)

        return json_data

    def save_xml_file(self, in_file_path="text.txt", out_file_path="parce.xml", sentences_n="all"):
        # encoding = chardet.detect(open(in_file_path, 'rb').read())["encoding"]
        f = open(in_file_path, 'r')
        document = f.read()
        f.close()
        text = self.make_xml(document, sentences_n)
        f = open(out_file_path, 'w')
        f.write(text)
        f.close()

    def save_json_file(self, in_file_path="text.txt", out_file_path="parce.json", sentences_n="all"):
        encoding = chardet.detect(open(in_file_path, 'rb').read())["encoding"]
        f = open(in_file_path, 'r', encoding=encoding)
        document = f.read()
        f.close()
        text = self.make_json(document, sentences_n)
        f = open(out_file_path, 'w', encoding=encoding)
        f.write(text)
        f.close()


class TermParser:

    def __init__(self):
        self.auxiliary_preprocessor = AuxiliaryPreprocessors()

    def preprocessor(self, document, sentences_n="all"):
        '''
        Формирует данные о имеющихся существительных и именных группах
        Подготавливает сформированные данные в виде удобном для вывода в файл
        :param document:
        :param sentences_n:
        :return:
        '''
        # Получаем из переданных исходных данных
        # номера предложений для последующего анализа
        sent_no = None
        if sentences_n != "all":
            # Разбиваем преданную строку по символу запятой
            # и приводим элементы полученного массива к целому числу
            sent_no = [int(i) for i in sentences_n.split(",")]

        text = self.auxiliary_preprocessor.clear_hyphenations(self.auxiliary_preprocessor.remove_junk_symbols(document))

        sentences = nltk.sent_tokenize(text)  # Разбиваем переданный таекст на предложения
        out_data = []  # Создаём список, в который будем сохранять основные результаты разбора текста
        sentance_analyzer = SentenceAnalyzer()  # Создаём объект анализатора предложения

        sent_counter = 0  # Счётчик номеров предложений
        for sentance in sentences:  # Перебираем предложения
            if sent_no is not None:  # Отсеиваем предложения не числящиеся в списк еsentences_n
                if sent_counter not in sent_no:
                    sent_counter += 1
                    continue
            # Получаем собственно именные группы и существительные из данного предложения
            name_groups = sentance_analyzer.get_nouns_and_name_groups(sentance, sent_number=sent_counter)

            # Перебираем полученные именные группы
            for group in name_groups:
                if group.name_group is not None:
                    # Если такой группы ещё нету, записываем её в результат
                    if group.tname not in [record.tname for record in out_data]:
                        group.sentpos()
                        out_data.append(group)
                    # В противном случае если группа состоит из менее чем 7 слов
                    elif group.wcount < 7:
                        i = 0
                        while i < len(out_data):  # Перебираем все имеющиеся на данный момент выходные данные
                            if out_data[i].tname == group.tname:  # Когда найдём данное слово
                                for sentpos in group.sentpos():  # Добавляем в выходные данные из списка пары
                                    # номер предложения / номер слова в предложении
                                    out_data[i].add_sentpos(sentpos)
                            i += 1
            sent_counter += 1

        # Формируем связи relup
        test_group_n = 0
        for test_group in out_data:
            test_tname_as_llist = [morph.parse(word) for word in test_group.tname.split()]
            group_n = 0
            for group in out_data:
                if test_group_n != group_n:
                    tname_as_llist = [morph.parse(word) for word in group.tname.split()]
                    is_in_this_group = True
                    for test_word in test_tname_as_llist:
                        test_word_found = False
                        for word in tname_as_llist:
                            for test_form in test_word:
                                if test_form.tag.POS == "NOUN" or test_form.tag.POS == "ADJF":
                                    for form in word:
                                        if form.tag.POS == "NOUN" or test_form.tag.POS == "ADJF":
                                            if test_form.normal_form == form.normal_form:
                                                test_word_found = True
                                                break
                                if test_word_found:
                                    break
                            if test_word_found:
                                break
                        if not test_word_found:
                            is_in_this_group = False
                            break
                    if is_in_this_group:
                        test_group.relup.append(group_n)

                group_n += 1
            test_group_n += 1

        # Формируем связи reldown
        test_group_n = 0
        for test_group in out_data:
            test_tname_as_llist = [morph.parse(word) for word in test_group.tname.split()]
            if len(test_tname_as_llist) > 1:
                group_n = 0
                for group in out_data:
                    if test_group_n != group_n:
                        tname_as_llist = [morph.parse(word) for word in group.tname.split()]
                        # Надо проверить, что все слова из tname_as_llist входят в test_tname_as_llist
                        # Для этого перебираем tname_as_llist
                        all_words_are_in_list = True  # Критерий того, что все слова из tname_as_llist входят в test_tname_as_llist
                        # Дальше строим алгоритм на опровержение. Опровержением является то, если
                        # хотябы одного слова из tname_as_llist нет в test_tname_as_llist
                        for word in tname_as_llist:
                            # Для каждого слова word из списка tname_as_llist проверяем его наличие в списке test_tname_as_llist
                            word_found = False
                            for test_word in test_tname_as_llist:
                                # Просто сверить if test_word == word нельзя, так как сравнивать нужно начальные формы
                                words_equel = False  # Индикатор того, что test_word == word
                                for test_form in test_word:
                                    if test_form.tag.POS == "NOUN" or test_form.tag.POS == "ADJF":
                                        for form in word:
                                            if form.tag.POS == "NOUN" or test_form.tag.POS == "ADJF":
                                                if test_form.normal_form == form.normal_form:
                                                    words_equel = True
                                                    word_found = True
                                                    break
                                if words_equel:
                                    break
                            if not word_found:
                                all_words_are_in_list = False
                                break
                        if all_words_are_in_list:
                            test_group.reldown.append(group_n)
                    group_n += 1
            test_group_n += 1

        return (out_data, sentences, sent_no)

    def make_xml(self, document, path, sentences_n="all"):
        """
        Вызывает поиск именных групп в тексте и возвращает результаты разбора в xml
        :param in_file_path:
        :param out_file_path:
        :return:
        """

        out_data, sentences, sent_no = self.preprocessor(document, sentences_n)

        xml_text = '<?xml version="1.0" encoding="windows-1251"?>\n'
        xml_text += '<termsintext>\n'
        xml_text += '<filepath>-----' + path + '-----</filepath>\n'
        xml_text += '\t<exporterms>\n'
        for record in out_data:
            xml_text += '\t\t<term>\n'
            xml_text += '\t\t\t<ttype>' + record.ttype + '</ttype>\n'
            xml_text += '\t\t\t<tname>' + record.tname + '</tname>\n'
            xml_text += '\t\t\t<wcount>' + str(record.wcount) + '</wcount>\n'
            for word in record.name_group.get_words_as_obj():
                xml_text += '\t\t\t<osn>' + stemmer_obj.stem(word.word) + '</osn>\n'
            for sentpos in record.sentpos():
                xml_text += '\t\t\t<sentpos>' + str(sentpos[0]) + '/' + str(sentpos[1]) + '</sentpos>\n'
            for relup in record.relup:
                xml_text += '\t\t\t<relup>' + str(relup) + '</relup>\n'
            for reldown in record.reldown:
                xml_text += '\t\t\t<reldown>' + str(reldown) + '</reldown>\n'
            xml_text += '\t\t</term >\n'

        xml_text += '\t</exporterms>\n'
        xml_text += '\t<sentences>\n'

        sent_counter = 0
        for sentance in sentences:
            if sent_no is not None:
                if sent_counter not in sent_no:
                    sent_counter += 1
                    continue
            xml_text += '\t\t<sent>' + sentance + '</sent>\n'

        xml_text += '\t</sentences>\n'
        xml_text += '</termsintext>\n'

        return xml_text

    def create_ontology(self, document):

        out_data, sentences, sent_no = self.preprocessor(document)

        sentance_analyzer = SentenceAnalyzer()

        v_subj_groups = {}
        n_subj_groups = {}

        # собираем группы подлежащих, связанных с глагольными и именными сказуемыми

        for sentance in sentences:  # Перебираем предложения
            sentance_analyzer.analize_sentance(sentance)
            struct = sentance_analyzer.serialyze()
            for clusters in struct:
                if 'word' in clusters:
                    for word in clusters['dependent_words'] + clusters['probably_dependent_words']:
                        if word[2] == 'v_subj':
                            p1 = morph.parse(clusters['word'])
                            can_be_NPRO = False
                            for w_form in p1:
                                if w_form.tag.POS == 'NPRO':
                                    can_be_NPRO = True
                                    break
                            if not can_be_NPRO:
                                for w_form in  p1:
                                    if w_form.tag.POS == 'NOUN':
                                        normal_form = w_form.normal_form
                                        if not normal_form in v_subj_groups:
                                            v_subj_groups[normal_form] = []
                                        pred_id = int(word[1])
                                        for clusters_2 in struct:
                                            if clusters_2['id'] == pred_id:
                                                if 'word' in clusters_2:
                                                    p2 = morph.parse(clusters_2['word'])
                                                    for w_form_2 in p2:
                                                        if w_form_2.tag.POS == 'VERB':
                                                            normal_form_pred =  w_form_2.normal_form
                                                            if not [normal_form_pred] in v_subj_groups[normal_form]:
                                                                v_subj_groups[normal_form].append([normal_form_pred])
                                                            break
                                                elif 'words' in clusters_2:
                                                    predicate_list = []
                                                    for item in clusters_2['words']:
                                                        p2 = morph.parse(item)
                                                        if item['pos'] != 'NOUN':
                                                            for w_form_2 in p2:
                                                                if w_form_2.tag.POS == item['pos']:
                                                                    if item['pos'] == 'ADJF':
                                                                        mp = morph.parse(clusters_2['group_self_characteristics']['main_word'])
                                                                        for f in mp:
                                                                            if f.tag.POS == 'ADJF':
                                                                                gender = f.tag.gender
                                                                                nf = f.inflect({gender})
                                                                                if nf is not None:
                                                                                    predicate_list.append(nf.word)
                                                                                    break
                                                                    else:
                                                                        predicate_list.append(w_form_2.normal_form)
                                                                    break
                                                        else:
                                                            for w_form_2 in p2:
                                                                if w_form_2.tag.POS == item['pos']:
                                                                    predicate_list.append(w_form_2.inflect({'sing'}).word)
                                                                    break
                                                    if not predicate_list in v_subj_groups[normal_form]:
                                                        v_subj_groups[normal_form].append(predicate_list)
                        elif word[2] == 'n_subj':
                            p1 = morph.parse(clusters['word'])
                            can_be_NPRO = False
                            for w_form in p1:
                                if w_form.tag.POS == 'NPRO':
                                    can_be_NPRO = True
                                    break
                            if not can_be_NPRO:
                                for w_form in p1:
                                    if w_form.tag.POS == 'NOUN':
                                        normal_form = w_form.normal_form
                                        if not normal_form in n_subj_groups:
                                            n_subj_groups[normal_form] = []
                                        pred_id = int(word[1])
                                        for clusters_2 in struct:
                                            if clusters_2['id'] == pred_id:
                                                if 'word' in clusters_2:
                                                    p2 = morph.parse(clusters_2['word'])
                                                    for w_form_2 in p2:
                                                        if w_form_2.tag.POS == 'NOUN':
                                                            normal_form_pred = w_form_2.normal_form
                                                            if w_form_2.normal_form is not None:
                                                                if not [normal_form_pred] in n_subj_groups[normal_form]:
                                                                    n_subj_groups[normal_form].append([normal_form_pred])
                                                            else:
                                                                if not [w_form_2.word] in n_subj_groups[normal_form]:
                                                                    n_subj_groups[normal_form].append([w_form_2.word])
                                                            break
                                                elif 'words' in clusters_2:
                                                    predicate_list = []
                                                    for item in clusters_2['words']:
                                                        p2 = morph.parse(item['word'])
                                                        if item['pos'] != 'NOUN':
                                                            for w_form_2 in p2:
                                                                if w_form_2.tag.POS == item['pos']:
                                                                    if item['pos'] == 'ADJF':
                                                                        mp = morph.parse(
                                                                            clusters_2['group_self_characteristics'][
                                                                                'main_word'])
                                                                        for f in mp:
                                                                            if f.tag.POS == 'ADJF':
                                                                                gender = f.tag.gender
                                                                                nf = f.inflect({gender})
                                                                                if nf is not None:
                                                                                    predicate_list.append(nf.word)
                                                                                    break
                                                                    else:
                                                                        if w_form_2.normal_form is not None:
                                                                            predicate_list.append(w_form_2.normal_form)
                                                                        else:
                                                                            predicate_list.append(w_form_2.word)
                                                                    break
                                                        else:
                                                            for w_form_2 in p2:
                                                                if w_form_2.tag.POS == item['pos']:
                                                                    tmp_w = w_form_2.inflect({'sing'})
                                                                    if tmp_w is not None:
                                                                        predicate_list.append(tmp_w.word)
                                                                    else:
                                                                        predicate_list.append(w_form_2.word)
                                                                    break
                                                    if not predicate_list in n_subj_groups[normal_form]:
                                                        n_subj_groups[normal_form].append(predicate_list)
                elif 'words' in clusters:
                    for word in clusters['group_self_characteristics']['dependent_words'] + clusters['group_self_characteristics']['probably_dependent_words']:
                        if word[2] == 'v_subj':
                            subj_list = []
                            for item in clusters['words']:
                                p2 = morph.parse(item['word'])
                                if item['pos'] == 'NOUN': #or item['pos'] == 'ADJF' or item['pos'] == 'ADJS' or item['pos'] == 'PRTF':
                                    if item['pos'] == 'ADJF':
                                        for w_form_2 in p2:
                                            if w_form_2.tag.POS == 'ADJF':
                                                if len(item['dependens_on'] + item['probably_dependens_on']) > 0:
                                                    w = list(item['dependens_on'] + item['probably_dependens_on'])[0]
                                                    pw = morph.parse(w[0])
                                                    for i in pw:
                                                        if i.tag.POS == 'NOUN':
                                                            gender = i.tag.gender
                                                            case = i.tag.case
                                                            if clusters['group_self_characteristics']['main_word'] == w[0]:
                                                                case = 'nomn'
                                                            if gender is not None and case is not None:
                                                                subj_list.append(
                                                                    w_form_2.inflect({gender, case}).word)
                                                                break
                                            break
                                    else:
                                        for w_form_2 in p2:
                                            if w_form_2.tag.POS == item['pos']:
                                                if w_form_2.tag.case == 'gent':
                                                    if w_form_2.inflect({'sing', 'gent'}) is not None:
                                                        subj_list.append(w_form_2.inflect({'sing', 'gent'}).word)
                                                    elif w_form_2.inflect({'sing'}) is not None:
                                                        subj_list.append(w_form_2.inflect({'sing'}).word)
                                                    elif w_form_2.inflect({'gent'}) is not None:
                                                        subj_list.append(w_form_2.inflect({'gent'}).word)
                                                    else:
                                                        subj_list.append(w_form_2.normal_form)
                                                    break
                                                else:
                                                    subj_list.append(w_form_2.normal_form)
                                                    break
                            subjeect_word = '_'.join(subj_list)
                            if not  subjeect_word in v_subj_groups:
                                v_subj_groups[subjeect_word] = []
                            pred_id = int(word[1])
                            for clusters_2 in struct:
                                if clusters_2['id'] == pred_id:
                                    if 'word' in clusters_2:
                                        p2 = morph.parse(clusters_2['word'])
                                        for w_form_2 in p2:
                                            if w_form_2.tag.POS == 'VERB':
                                                normal_form_pred = w_form_2.normal_form
                                                if [normal_form_pred] not in v_subj_groups[subjeect_word]:
                                                    v_subj_groups[subjeect_word].append([normal_form_pred])
                                                break
                                    elif 'words' in clusters_2:
                                        predicate_list = []
                                        for item in clusters_2['words']:
                                            p2 = morph.parse(item['word'])
                                            if item['pos'] != 'NOUN':
                                                for w_form_2 in p2:
                                                    if w_form_2.tag.POS == item['pos']:
                                                        predicate_list.append(w_form_2.normal_form)
                                                        break
                                            else:
                                                for w_form_2 in p2:
                                                    if w_form_2.tag.POS == item['pos']:
                                                        predicate_list.append(w_form_2.inflect({'sing'}))
                                                        break
                                        if predicate_list not in v_subj_groups[subjeect_word]:
                                            v_subj_groups[subjeect_word].append(predicate_list)
                        elif word[2] == 'n_subj':
                            subj_list = []
                            for item in clusters['words']:
                                p2 = morph.parse(item['word'])
                                if item['pos'] == 'NOUN':
                                    if item['pos'] == 'ADJF':
                                        for w_form_2 in p2:
                                            if w_form_2.tag.POS == 'ADJF':
                                                if len(item['dependens_on'] + item['probably_dependens_on']) > 0:
                                                    w = list(item['dependens_on'] + item['probably_dependens_on'])[0]
                                                    pw = morph.parse(w[0])
                                                    for i in pw:
                                                        if i.tag.POS == 'NOUN':
                                                            gender = i.tag.gender
                                                            case = i.tag.case
                                                            if clusters['group_self_characteristics']['main_word'] == w[0]:
                                                                case = 'nomn'
                                                            if gender is not None and case is not None:
                                                                subj_list.append(
                                                                    w_form_2.inflect({gender, case}).word)
                                                                break
                                            break
                                    else:
                                        for w_form_2 in p2:
                                            if w_form_2.tag.POS == item['pos']:
                                                if w_form_2.tag.case == 'gent':
                                                    if w_form_2.inflect({'sing', 'gent'}) is not None:
                                                        subj_list.append(w_form_2.inflect({'sing', 'gent'}).word)
                                                    elif w_form_2.inflect({'sing'}) is not None:
                                                        subj_list.append(w_form_2.inflect({'sing'}).word)
                                                    elif w_form_2.inflect({'gent'}) is not None:
                                                        subj_list.append(w_form_2.inflect({'gent'}).word)
                                                    else:
                                                        subj_list.append(w_form_2.normal_form)
                                                    break
                                                else:
                                                    subj_list.append(w_form_2.normal_form)
                                                    break
                            subjeect_word = '_'.join(subj_list)
                            #print(subjeect_word)
                            if not  subjeect_word in n_subj_groups:
                                n_subj_groups[subjeect_word] = []
                            pred_id = int(word[1])
                            for clusters_2 in struct:
                                if clusters_2['id'] == pred_id:
                                    if 'word' in clusters_2:
                                        p2 = morph.parse(clusters_2['word'])
                                        for w_form_2 in p2:
                                            if w_form_2.tag.POS == 'NOUN':
                                                normal_form_pred = w_form_2.normal_form
                                                if normal_form_pred is None:
                                                    normal_form_pred = w_form_2.word
                                                if [normal_form_pred] not in n_subj_groups[subjeect_word]:
                                                    n_subj_groups[subjeect_word].append([normal_form_pred])
                                                break
                                    elif 'words' in clusters_2:
                                        predicate_list = []
                                        for item in clusters_2['words']:
                                            #print("\t", item['word'])
                                            p2 = morph.parse(item['word'])
                                            if item['pos'] != 'NOUN':
                                                pass
                                                '''
                                                for w_form_2 in p2:
                                                    if w_form_2.tag.POS == item['pos']:
                                                        if w_form_2.normal_form is not None:
                                                            if w_form_2.normal_form not in predicate_list:
                                                                predicate_list.append(w_form_2.normal_form)
                                                        else:
                                                            if w_form_2.word not in predicate_list:
                                                                predicate_list.append(w_form_2.word)
                                                        break
                                                '''
                                            else:
                                                for w_form_2 in p2:
                                                    if w_form_2.tag.POS == item['pos']:
                                                        tmp_w = w_form_2.inflect({'sing'})
                                                        if tmp_w is not None:
                                                            predicate_list.append(tmp_w.word)
                                                        else:
                                                            predicate_list.append(w_form_2.word)
                                                        break

                                        if predicate_list not in n_subj_groups[subjeect_word]:
                                            n_subj_groups[subjeect_word].append(predicate_list)

        verb_occ_groups = {} # Свойства глаголов
        verb_sup_gruops = {} # Глагольные дополнения

        for sentance in sentences:  # Перебираем предложения
            sentance_analyzer.analize_sentance(sentance)
            struct = sentance_analyzer.serialyze()
            for clusters in struct:
                if 'word' in clusters:
                    if clusters['pos'] == 'VERB':
                        for word in clusters['dependent_words'] + clusters['probably_dependent_words']:
                            if word[2] == 'occ':
                                p1 = morph.parse(clusters['word'])
                                for w_form in p1:
                                    if w_form.tag.POS == 'VERB':
                                        normal_form = w_form.normal_form
                                        if normal_form not in verb_occ_groups:
                                            verb_occ_groups[normal_form] = []
                                        p2 = morph.parse(word[0])
                                        normal_form_2 = [word[0], 0]
                                        word_pos = ""
                                        for item in struct:
                                            if 'word' in item:
                                                if word[1] == item['id']:
                                                    word_pos = item['pos']
                                                    break
                                            elif 'group_self_characteristics' in item:
                                                if word[1] == item['group_self_characteristics']['id']:
                                                    word_pos = item['pos']
                                                    break
                                        if word_pos == 'ADJF':
                                            for w_form_2 in p2:
                                                if w_form_2.tag.POS == 'ADJF':
                                                    tmp = w_form_2.inflect({'masc', 'ablt'})
                                                    if tmp is not None:
                                                        normal_form_2 = [tmp.word, 1]
                                                        break
                                        if normal_form_2 not in verb_occ_groups[normal_form]:
                                            verb_occ_groups[normal_form].append(normal_form_2)
                                        break
                            else:
                                p1 = morph.parse(clusters['word'])
                                for w_form in p1:
                                    if w_form.tag.POS == 'VERB':
                                        normal_form = w_form.normal_form
                                        if normal_form not in verb_sup_gruops:
                                            verb_sup_gruops[normal_form] = []
                                        word_info = ()
                                        for item in struct:
                                            if 'word' in item:
                                                if item['id'] == word[1]:
                                                    word_info = item
                                                    break
                                            elif 'group_self_characteristics' in item:
                                                if item['group_self_characteristics']['id'] == word[1]:
                                                    word_info = item
                                                    break
                                        if 'word' in word_info:
                                            current_case = word[2].split('_')[1]
                                            if current_case == 'sup':
                                                current_case = word[2].split('_')[0]
                                            new_sup = {'words': [word_info['word']],
                                                       'preposition': word_info['preposition'][0],
                                                       'case': current_case}
                                            if new_sup not in verb_sup_gruops[normal_form]:
                                                verb_sup_gruops[normal_form].append(new_sup)
                                        elif 'group_self_characteristics' in word_info:
                                            sup_list = []
                                            main_word = item['group_self_characteristics']['main_word']
                                            current_preposition = ""
                                            for item in word_info['words']:
                                                if item['word'] == main_word:
                                                    current_preposition = item['preposition'][0]
                                                p2 = morph.parse(item['word'])
                                                for w_form_2 in p2:
                                                    if w_form_2.tag.POS == 'NOUN':
                                                        sup_list.append(item['word'])
                                                        break
                                            current_case = word[2].split('_')[1]
                                            if current_case == 'sup':
                                                current_case = word[2].split('_')[0]
                                            new_sup = {'words': sup_list,
                                                       'preposition': current_preposition,
                                                       'case': current_case}
                                        break

        action_conditions = []

        # Собираем обстоятельства совершения действий подлежащими
        for sentance in sentences:  # Перебираем предложения
            sentance_analyzer.analize_sentance(sentance)
            struct = sentance_analyzer.serialyze()
            condition = {"subj": [], "pred": [], "conditions": []}
            for clusters in struct:
                if 'word' in clusters:
                    # print(clusters, clusters['id'])
                    is_linked_with_subj_or_pred = False
                    for item in clusters['dependent_words'] + clusters['probably_dependent_words']:
                        if item[2] == 'v_subj':
                            for i in struct:
                                if 'word' in i:
                                    if i['id'] == item[1]:
                                        if i not in condition["pred"]:
                                            condition["pred"].append(i)
                                            break
                                elif 'group_self_characteristics' in i:
                                    if i['group_self_characteristics']['id'] == item[1]:
                                        condition["pred"].append(i)
                                        break
                            if clusters not in condition["subj"]:
                                condition["subj"].append(clusters)
                            is_linked_with_subj_or_pred = True
                        if item[2] == 'n_subj':
                            is_linked_with_subj_or_pred = True
                    for item in clusters['dependens_on'] + clusters['probably_dependent_words']:
                        if item[2] == 'v_subj' or item[2] == 'n_subj':
                            is_linked_with_subj_or_pred = True
                    if not is_linked_with_subj_or_pred and clusters not in condition["conditions"]:
                        if clusters['pos'] != 'PREP' and clusters['pos'] != 'VERB':
                            condition["conditions"].append(clusters)
                elif 'group_self_characteristics' in clusters:
                    is_linked_with_subj_or_pred = False
                    for item in clusters['group_self_characteristics']['dependent_words'] + clusters['group_self_characteristics']['probably_dependent_words']:
                        if item[2] == 'v_subj':
                            for i in struct:
                                if 'word' in i:
                                    if i['id'] == item[1]:
                                        if i not in condition["pred"]:
                                            condition["pred"].append(i)
                                            break
                                elif 'group_self_characteristics' in i:
                                    if i['group_self_characteristics']['id'] == item[1]:
                                        condition["pred"].append(i)
                                        break
                            if clusters not in condition["subj"]:
                                condition["subj"].append(clusters)
                            is_linked_with_subj_or_pred = True
                        if item[2] == 'n_subj':
                            is_linked_with_subj_or_pred = True
                    for item in clusters['group_self_characteristics']['dependens_on'] + clusters['group_self_characteristics']['probably_dependent_words']:
                        if item[2] == 'v_subj' or item[2] == 'n_subj':
                            is_linked_with_subj_or_pred = True
                    if not is_linked_with_subj_or_pred and clusters not in condition["conditions"]:
                        condition["conditions"].append(clusters)
            if len(condition["conditions"]) > 0 and len(condition["pred"]) > 0 and  len(condition["subj"]) > 0:
                action_conditions.append(condition)
        '''
        for i in action_conditions:
            if 'word' in i['subj']:
                print(i['subj']['word'])
            else:
                print(i['subj'])
            if 'word' in i['pred']:
                print(i['pred']['word'])
            else:
                print(i['pred'])
            for j in i['conditions']:
                if 'word' in j:
                    print("    ", j['word'])
                elif 'group_self_characteristics' in j:
                    print("    ", j['group_self_characteristics']['main_word'])
        '''



        adjs = set()
        used_terms = set()  # Чтобі не повторялись

        list_of_classes = []
        list_of_property = []

        list_of_classes.append(OntoClass())

        list_of_classes.append(OntoClass(id="Attribute", patent_class_id='Thing'))
        list_of_classes.append(OntoClass(id="Action", patent_class_id='Thing'))
        list_of_classes.append(OntoClass(id="Adverb", patent_class_id='Thing'))
        list_of_classes.append(OntoClass(id="ConditionsInteraction", patent_class_id='Thing'))


        list_of_property.append(OntoProperty(id="GentSup", domain_id="Action", range_id='Thing', label='genitive supplement'))
        list_of_property.append(
            OntoProperty(id="DatvSup", domain_id="Action", range_id='Thing', label='dative supplement'))
        list_of_property.append(
            OntoProperty(id="AccsSup", domain_id="Action", range_id='Thing', label='accusative supplement'))
        list_of_property.append(
            OntoProperty(id="AbltSup", domain_id="Action", range_id='Thing', label='instrumental supplement'))
        list_of_property.append(
            OntoProperty(id="LoctSup", domain_id="Action", range_id='Thing', label='local case supplement'))
        list_of_property.append(
            OntoProperty(id="VerbSup", domain_id="Action", range_id='Thing', label='verb supplement'))
        list_of_property.append(OntoProperty(id="Existence", domain_id='Thing', range_id='Thing', label='Existence'))




    # Собираем одиночные понятия, как классы верхнего уровня

        for record in out_data:
            # Обретает прилагательные

            ttype_list = record.ttype.split('_')
            tname_list = record.tname.split()
            counter = 0
            for word in record.name_group.get_words_as_obj():
                if ttype_list[counter].lower() == 'adj':
                    adjs.add((stemmer_obj.stem(word.word), tname_list[counter]))
                counter += 1

            if record.wcount == 1:
                term = ""
                for word in record.name_group.get_words_as_obj():
                    term += stemmer_obj.stem(word.word).capitalize()
                if term not in used_terms:
                    list_of_classes.append(OntoClass(id=term, patent_class_id='Thing', label=str(record.tname), language=str(language)))
                    used_terms.add(term)
                else:
                    continue

        for adj in adjs:
            if adj[0] not in used_terms:
                list_of_classes.append(
                    OntoClass(id=adj[0].capitalize(), patent_class_id='Attribute', label=adj[1], language=str(language)))
                used_terms.add(adj[0])

        for verb_occ in verb_occ_groups:
            for occ in verb_occ_groups[verb_occ]:
                if stemmer_obj.stem(occ[0]).capitalize() not in used_terms:
                    new_class = OntoClass(id=stemmer_obj.stem(occ[0]).capitalize())

                    if occ[1] == 0:
                        new_class.patent_class_id='Adverb'
                        new_class.language=str(language)
                        new_class.label=occ[0]
                    else:
                        new_class.patent_class_id="Attribute"
                        p1 = morph.parse(occ[0])
                        for w_form in p1:
                            if w_form.tag.POS == 'ADJF':
                                normal_form =  w_form.normal_form
                                if normal_form is not None:
                                    new_class.language=str(language)
                                    new_class.label=normal_form
                                    break
                                else:
                                    new_class.language = str(language)
                                    new_class.label =occ[0]
                                    break
                    list_of_classes.append(new_class)
                    used_terms.add(stemmer_obj.stem(occ[0]).capitalize())

        for item in v_subj_groups:
            for pred in v_subj_groups[item]:
                for word in pred:
                    if stemmer_obj.stem(word).capitalize() not in used_terms:
                        list_of_classes.append(
                            OntoClass(id=stemmer_obj.stem(word).capitalize(), patent_class_id='Action', label=word,
                                      language=str(language)))
                        used_terms.add(stemmer_obj.stem(word).capitalize())

        # Собираем объединения
        for record in out_data:
            for relup in record.relup:
                current_up_term = out_data[relup]
                if current_up_term.wcount == record.wcount + 1:
                    current_ttype = [i.lower() for i in current_up_term.ttype.split('_')]
                    if not 'adj' in current_ttype:
                        current_id = ""
                        for word in current_up_term.name_group.get_words_as_obj():
                            current_id += stemmer_obj.stem(word.word).capitalize()

                        if current_id not in used_terms:
                            new_class = OntoClass(id=current_id, language=str(language))
                            used_terms.add(current_id)
                            for word in current_up_term.name_group.get_words_as_obj():
                                new_class.interactions.append(stemmer_obj.stem(word.word).capitalize())
                            new_class.label=str(current_up_term.tname)
                            list_of_classes.append(new_class)
                        else:
                            continue
                    else:
                        current_id = ""
                        counter = 0
                        n_nouns = 0
                        for word in current_up_term.name_group.get_words_as_obj():
                            if current_ttype[counter].lower() != 'adj':
                                current_id += stemmer_obj.stem(word.word).capitalize()
                                n_nouns +=1
                            counter += 1
                        if current_id not in used_terms:
                            new_class = OntoClass(id=current_id, language=str(language))
                            used_terms.add(current_id)

                            if n_nouns > 1:
                                counter = 0
                                for word in current_up_term.name_group.get_words_as_obj():
                                    if current_ttype[counter].lower() != 'adj':
                                        new_class.interactions.append(stemmer_obj.stem(word.word).capitalize())
                                    counter += 1
                            else:
                                new_class.patent_class_id="Thing"
                            verbal_term_list = str(current_up_term.tname).split()
                            verbal_term = ""
                            counter = 0
                            for word in current_up_term.name_group.get_words_as_obj():
                                if current_ttype[counter].lower() != 'adj':
                                    verbal_term += verbal_term_list[counter] + " "
                                counter += 1
                            verbal_term = verbal_term.strip()
                            new_class.label=verbal_term
                            list_of_classes.append(new_class)
                        else:
                            continue

        # Привязываем прилагательные как свойства
        for record in out_data:
            for relup in record.relup:
                current_up_term = out_data[relup]
                if current_up_term.wcount == record.wcount + 1:
                    current_ttype = [i.lower() for i in current_up_term.ttype.split('_')]
                    if 'adj' in current_ttype:
                        current_adj_set = set()
                        counter = 0
                        for i in current_ttype:
                            if i == 'adj':
                                current_adj_set.add(stemmer_obj.stem(current_up_term.name_group.get_words_as_obj()[counter].word))
                                counter += 1
                        for adj in current_adj_set:
                            domain = ""
                            current_id = ""
                            counter = 0
                            for word in current_up_term.name_group.get_words_as_obj():
                                if current_ttype[counter] == 'adj':
                                    if stemmer_obj.stem(word.word).lower() != adj.lower():
                                        pass
                                    else:
                                        current_id += stemmer_obj.stem(word.word).capitalize()
                                else:
                                    current_id += stemmer_obj.stem(word.word).capitalize()
                                    domain += stemmer_obj.stem(word.word).capitalize()
                                counter += 1
                            if current_id not in used_terms:
                                new_property=OntoProperty(id=current_id, domain_id=domain, range_id=adj.capitalize())

                                verbal_term_list = str(current_up_term.tname).split()
                                verbal_term = ""
                                counter = 0
                                for word in current_up_term.name_group.get_words_as_obj():
                                    if current_ttype[counter].lower() != 'adj':
                                        verbal_term += verbal_term_list[counter] + " "
                                    elif stemmer_obj.stem(word.word).lower() == adj.lower():
                                        verbal_term += verbal_term_list[counter] + " "
                                    counter += 1
                                verbal_term = verbal_term.strip()
                                new_property.language=str(language)
                                new_property.label=verbal_term
                                list_of_property.append(new_property)

                                used_terms.add(current_id)

        for item in v_subj_groups:
            term = "".join([stemmer_obj.stem(i).capitalize() for i in item.split('_')])
            for pred in v_subj_groups[item]:
                for word in pred:
                    current_id = term + stemmer_obj.stem(word).capitalize()
                    if current_id not in used_terms:
                        new_property=OntoProperty(id=current_id, domain_id=term, range_id=stemmer_obj.stem(word).capitalize(), language=str(language))

                        if str(language) == 'uk':
                            new_property.label = " ".join(item.split('_')) + ' може ' +  word
                        elif str(language) == 'ru':
                            new_property.label = " ".join(item.split('_')) + ' может ' +  word
                        else:
                            new_property.label = " ".join(item.split('_')) + ' can ' + word
                        list_of_property.append(new_property)
                        used_terms.add(current_id)

        for item in n_subj_groups:
            term = "".join([stemmer_obj.stem(i).capitalize() for i in item.split('_')])
            if term not in used_terms:
                new_class = OntoClass(id=term, language=str(language), label=" ".join(item.split('_')))
                for word in item.split('_'):
                    new_class.interactions.append(stemmer_obj.stem(word).capitalize())
                used_terms.add(term)
                list_of_classes.append(new_class)
            for pred in n_subj_groups[item]:
                current_id = term
                pred_id = ""
                for word in pred:
                    current_id += stemmer_obj.stem(word).capitalize()
                    pred_id += stemmer_obj.stem(word).capitalize()
                if pred_id not in used_terms:
                    new_class = OntoClass(id=pred_id, language=str(language), label=" ".join(pred))
                    for word in pred:
                        new_class.interactions.append(stemmer_obj.stem(word).capitalize())
                    used_terms.add(pred_id)
                    list_of_classes.append(new_class)

                if current_id not in used_terms:
                    new_property=OntoProperty(id=current_id, parent_id='Existence', domain_id=term, range_id=pred_id, language=str(language))

                    if str(language) == 'uk':
                        new_property.label = " ".join(item.split('_')) + ' може бути ' + " ".join(pred)
                    elif str(language) == 'ru':
                        new_property.label = " ".join(item.split('_')) + ' может мыть ' + " ".join(pred)
                    else:
                        new_property.label = " ".join(item.split('_')) + ' can be ' + " ".join(pred)
                    list_of_property.append(new_property)
                    used_terms.add(current_id)

        for item in verb_occ_groups:
            for occ in verb_occ_groups[item]:
                current_id = stemmer_obj.stem(item).capitalize() + stemmer_obj.stem(occ[0]).capitalize()
                if current_id not in used_terms:
                    new_property = OntoProperty(id=current_id, domain_id=stemmer_obj.stem(item).capitalize(),
                                                range_id=stemmer_obj.stem(occ[0]).capitalize(), language=str(language))
                    if str(language) == 'uk':
                        new_property.label=item.lower() + ' можна ' + occ[0].lower()
                    elif str(language) == 'ru':
                        new_property.label = item.lower() + ' можно ' + occ[0].lower()
                    else:
                        new_property.label = item.lower() + ' can be ' + occ[0].lower()
                    list_of_property.append(new_property)
                    used_terms.add(current_id)

        for item in verb_sup_gruops:
            for sup in verb_sup_gruops[item]:
                sup_term = ""
                for t in sup['words']:
                    sup_term += stemmer_obj.stem(t).capitalize()
                current_id = stemmer_obj.stem(item).capitalize() + sup_term
                if current_id not in used_terms:
                    new_property=OntoProperty(id=current_id, domain_id=stemmer_obj.stem(item).capitalize(),
                                              range_id=sup_term, language=str(language))
                    if 'case' in sup:
                        if sup['case'] != "":
                            if sup['case'] in ['gent', 'datv', 'accs', 'ablt', 'loct', 'verb']:
                                if sup['case'] == 'gent':
                                    new_property.parent_id="GentSup"
                                if sup['case'] == 'datv':
                                    new_property.parent_id = "DatvSup"
                                if sup['case'] == 'accs':
                                    new_property.parent_id = "AccsSup"
                                if sup['case'] == 'ablt':
                                    new_property.parent_id = "AbltSup"
                                if sup['case'] == 'loct':
                                    new_property.parent_id = "LoctSup"
                                if sup['case'] == 'verb':
                                    new_property.parent_id = "VerbSup"
                    if str(language) == 'uk':
                        new_label = item.lower() + ' можна ' + sup['preposition'].lower() + " "
                        for word in sup['words']:
                            new_label += word.lower() + " "
                        new_property.label = new_label
                    elif str(language) == 'ru':
                        new_label = item.lower() + ' можно ' + sup['preposition'].lower() + " "
                        for word in sup['words']:
                            new_label += word.lower() + " "
                        new_property.label = new_label
                    else:
                        new_label = '>you can ' + item.lower() + sup['preposition'].lower() + " "
                        for word in sup['words']:
                            new_label += word.lower() + " "
                        new_property.label = new_label
                    list_of_property.append(new_property)
                    used_terms.add(current_id)

        for item in action_conditions:
            parent_property = ""
            subj_words = []
            for i in item['subj']:
                if 'word' in i:
                    parent_property += stemmer_obj.stem(i['word']).capitalize()
                    if i['pos'] == 'NOUN':
                        subj_words.append(i['word'])
                elif 'group_self_characteristics' in i:
                    for j in i['words']:
                        if j['pos'] == 'NOUN':
                            parent_property += stemmer_obj.stem(j['word']).capitalize()
                            subj_words.append(j['word'])
            class_exists = False
            for i in list_of_classes:
                if parent_property == i.id:
                    class_exists = True
                    break
            if not class_exists:
                new_class = OntoClass(id=copy.deepcopy(parent_property))
                if len(subj_words) > 1:
                    new_class.interactions = [stemmer_obj.stem(i).capitalize() for i in subj_words]
                    new_class.label = " ".join(subj_words)
                elif len(subj_words) > 0:
                    new_class.label = subj_words[0]
                else:
                    new_class.label = new_class.id
                new_class.language = str(language)
                list_of_classes.append(new_class)

            subj_id = copy.deepcopy(parent_property)

            pred_words = []
            for i in item['pred']:
                if 'word' in i:
                    p1 = morph.parse(i['word'])
                    for w_form in p1:
                        if w_form.tag.POS == 'VERB':
                            n_form = w_form.normal_form
                            if n_form is not None:
                                parent_property += stemmer_obj.stem(n_form).capitalize()
                            else:
                                parent_property += stemmer_obj.stem(i['word']).capitalize()
                            pred_words.append(i['word'])
                            break
                elif 'group_self_characteristics' in i:
                    for j in i['words']:
                        if j['pos'] == 'VERB':
                            p1 = morph.parse(j['word'])
                            for w_form in p1:
                                if w_form.tag.POS == 'VERB':
                                    n_form = w_form.normal_form
                                    if n_form is not None:
                                        parent_property += stemmer_obj.stem(n_form).capitalize()
                                    else:
                                        parent_property += stemmer_obj.stem(j['word']).capitalize()
                                    pred_words.append(j['word'])
                                    break

            property_exist = False
            for i in list_of_property:
                if i.id == parent_property:
                    property_exist = True
                    break

            if not property_exist:
                range_id = "".join([stemmer_obj.stem(i).capitalize() for i in  pred_words])
                new_property = OntoProperty(id=parent_property, domain_id=subj_id, range_id=range_id,
                                            language=str(language))
                list_of_property.append(new_property)

            if len(item['conditions']) > 1:
                new_class_name = ""
                interactions = []
                werbal_interactions = []
                for i in item['conditions']:
                    if 'word' in i:
                        if i['pos'] == 'NOUN':
                            p1 = morph.parse(i['word'])
                            for w_form in p1:
                                if w_form.tag.POS == 'NOUN':
                                    n_form = w_form.normal_form
                                    if n_form is not None:
                                        if stemmer_obj.stem(n_form).capitalize() in used_terms:
                                            interactions.append(stemmer_obj.stem(n_form).capitalize())
                                            new_class_name += stemmer_obj.stem(n_form).capitalize()
                                            werbal_interactions.append(n_form)
                                    else:
                                        if stemmer_obj.stem(i['word']).capitalize() in used_terms:
                                            interactions.append(stemmer_obj.stem(i['word']).capitalize())
                                            new_class_name += stemmer_obj.stem(i['word']).capitalize()
                                            werbal_interactions.append(i['word'])
                                    break
                    elif 'group_self_characteristics' in i:
                        int_name = ""
                        for j in i['words']:
                            if j['pos'] == 'NOUN':
                                #new_class_name += stemmer_obj.stem(j['word']).capitalize()
                                p1 = morph.parse(j['word'])
                                for word_f in p1:
                                    if word_f.tag.POS == 'NOUN':
                                        n_form = word_f.normal_form
                                        if n_form is not None:
                                            int_name += stemmer_obj.stem(n_form).capitalize()
                                            werbal_interactions.append(n_form)
                                        else:
                                            n_form = j['word']
                                            int_name += stemmer_obj.stem(j['word']).capitalize()
                                            werbal_interactions.append(j['word'])

                                        if stemmer_obj.stem(n_form).capitalize() not in used_terms:
                                            new_class = OntoClass(id=stemmer_obj.stem(n_form).capitalize(),
                                                                  language=str(language),
                                                                  label=n_form)
                                            list_of_classes.append(new_class)
                                            used_terms.add(stemmer_obj.stem(n_form).capitalize())
                                        break
                        new_class_name += stemmer_obj.stem(int_name).capitalize()
                        interactions.append(int_name)
                new_interaction_class = OntoClass(id=new_class_name, patent_class_id="ConditionsInteraction",
                                                  interactions=interactions, language=str(language))
                if str(language) == 'uk':
                    new_interaction_class.label = "Поєдняння обставин: " + ", ".join(werbal_interactions)
                elif str(language) == 'ru':
                    new_interaction_class.label = "Стечение обстоятельств: " + ", ".join(werbal_interactions)
                else:
                    new_interaction_class.label = "Conditions interaction: " + ", ".join(werbal_interactions)
                if new_class_name not in used_terms:
                    list_of_classes.append(new_interaction_class)
                    used_terms.add(new_class_name)

                new_property = OntoProperty(id=parent_property+new_class_name, domain_id="Thing", parent_id=parent_property,
                                            range_id=new_class_name, language=str(language))
                if str(language) == 'uk':
                    new_property.label = " ".join(subj_words) + " може виконати дію " + " ".join(pred_words) + " за наступних умов: " + ", ".join(werbal_interactions)
                elif str(language) == 'ru':
                    new_property.label = " ".join(subj_words) + " может выполнить действие " + " ".join(pred_words) + " при следующих условиях: " + ", ".join(werbal_interactions)
                else:
                    new_property.label = " ".join(subj_words) + " can do " + " ".join(pred_words) + " at following conditions: " + ", ".join(werbal_interactions)


                if parent_property+new_class_name not in used_terms:
                    list_of_property.append(new_property)

            elif len(item['conditions']) > 0:
                condition_class_name_verbal = []
                if 'word' in item['conditions'][0]:
                    condition_class_name_verbal.append(item['conditions'][0]['word'])
                elif 'words' in item['conditions'][0]:
                    for word in item['conditions'][0]['words']:
                        if word['pos'] == 'NOUN':
                            condition_class_name_verbal.append(word['word'])


                condition_class_name = "".join([stemmer_obj.stem(word).capitalize() for word in condition_class_name_verbal])
                new_property = OntoProperty(id=parent_property+condition_class_name, parent_id=parent_property,
                                            range_id=condition_class_name, domain_id="Thing", language=str(language))
                if str(language) == 'uk':
                    new_property.label = " ".join(subj_words) + " може виконати дію " + " ".join(
                        pred_words) + " за наступних умов: " + ", ".join(condition_class_name_verbal)
                elif str(language) == 'ru':
                    new_property.label = " ".join(subj_words) + " может выполнить действие " + " ".join(
                        pred_words) + " при следующих условиях: " + ", ".join(condition_class_name_verbal)
                else:
                    new_property.label = " ".join(subj_words) + " can do " + " ".join(
                        pred_words) + " at following conditions: " + ", ".join(condition_class_name_verbal)

                if parent_property+condition_class_name not in used_terms:
                    list_of_property.append(new_property)


            '''
            for pred in v_subj_groups[item]:
                for word in pred:
                    current_id = term + stemmer_obj.stem(word).capitalize()
                    if current_id not in used_terms:
                        new_property = OntoProperty(id=current_id, domain_id=term,
                                                    range_id=stemmer_obj.stem(word).capitalize(),
                                                    language=str(language))

                        if str(language) == 'uk':
                            new_property.label = " ".join(item.split('_')) + ' може ' + word
                        elif str(language) == 'ru':
                            new_property.label = " ".join(item.split('_')) + ' может ' + word
                        else:
                            new_property.label = " ".join(item.split('_')) + ' can ' + word
                        list_of_property.append(new_property)
                        used_terms.add(current_id)
            '''


        return (list_of_classes, list_of_property)

    def make_owl(self, document, path):
        list_of_classes, list_of_property = self.create_ontology(document)
        owl_text = '<rdf:RDF xmlns:owl ="http://www.w3.org/2002/07/owl#"\nxmlns:rdf ="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\nxmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"\nxmlns:xsd ="http://www.w3.org/2001/XMLSchema#">\n\t<owl:Ontology rdf:about="">\n'
        owl_text += '\t\t<rdfs:comment>Text ontology for ' + path.split('/')[-1] + '</rdfs:comment>\n'
        owl_text += '\t\t<rdfs:label>' + path.split('/')[-1] + ' ontology</rdfs:label>\n'
        owl_text += '\t</owl:Ontology>\n\n'

        for item in list_of_classes:
            owl_text += item.serialize()

        owl_text += '\n'

        for item in list_of_property:
            owl_text += item.serialize()

        owl_text += '\n'

        owl_text += '</rdf:RDF>\n'

        return owl_text



    def make_json(self, document, path, sentences_n="all"):
        """
        Вызывает поиск именных групп в тексте и возвращает результаты разбора в json
        :param in_file_path:
        :param out_file_path:
        :return:
        """

        out_data, sentences, sent_no = self.preprocessor(document, sentences_n)

        out_json = {
            "encoding": "windows-1251",
            "termsintext": {
                "filepath": path,
                "exporterms": [],
                "sentences": []
            }
        }

        for record in out_data:
            term = {
                "ttype": record.ttype,
                "tname": record.tname,
                "wcount": record.wcount,
                "osn": [],
                "sentpos": []
            }

            for word in record.name_group.get_words_as_obj():
                term["osn"].append(stemmer_obj.stem(word.word))
            for sentpos in record.sentpos():
                term["sentpos"].append(sentpos)

            out_json["termsintext"]["exporterms"].append(term)

        counter = 0
        for sentance in sentences:
            if sent_no is not None:
                if counter not in sent_no:
                    counter += 1
                    continue
            out_json["termsintext"]["sentences"].append(sentance)
            counter += 1

        return json.dumps(out_json, ensure_ascii=False)


    def save_xml_file(self, in_file_path="text.txt", out_file_path="alterms.xml", sentences_n="all"):
        encoding = chardet.detect(open(in_file_path, 'rb').read())["encoding"]
        f = open(in_file_path, 'r', encoding=encoding)
        path = os.path.abspath(in_file_path)
        document = f.read()
        f.close()
        xml_text = self.make_xml(document, path, sentences_n)
        f = open(out_file_path, 'w', encoding=encoding)
        f.write(xml_text)
        f.close()


    def save_owl_file(self, in_file_path="text.txt", out_file_path=""):
        encoding = chardet.detect(open(in_file_path, 'rb').read())["encoding"]
        f = open(in_file_path, 'r', encoding=encoding)
        path = os.path.abspath(in_file_path)
        document = f.read()
        f.close()
        owl_text = self.make_owl(document, path)
        if out_file_path.strip() == "":
            out_file_path = '.'.join(in_file_path.split('.')[0: -1]) + ".owl"
        f = open(out_file_path, 'w', encoding=encoding)
        f.write(owl_text)
        f.close()


    def save_json_file(self, in_file_path="text.txt", out_file_path="alterms.json", sentences_n="all"):
        encoding = chardet.detect(open(in_file_path, 'rb').read())["encoding"]
        f = open(in_file_path, 'r', encoding=encoding)
        path = os.path.abspath(in_file_path)
        document = f.read()
        f.close()
        json_text = self.make_json(document, path, sentences_n)
        f = open(out_file_path, 'w', encoding=encoding)
        f.write(json_text)
        f.close()


def load_owl(path):
    aux_f = AuxiliaryPreprocessors()
    text = open(path, 'r', encoding='utf-8').read()

    '''
    onto = get_ontology(path, ).load()
    a = list(onto.classes())
    b = onto.properties()
    for i in a:
        print(i)
    for i in b:
        print(i)
    '''


    e_allterms = ET.fromstring(text)

    onto_list = {
        "classes": [],
        "properties": []
    }
    for block in list(e_allterms):
        if block.tag.split('}')[-1] == 'Class':
            attributes = block.attrib
            new_class = OntoClass()
            for i in attributes:
                if i.split('}')[-1].lower() == 'id':
                    new_class.id = attributes[i]
                    break
            inner_content = list(block)
            for i in inner_content:
                current_tag = i.tag.split('}')[-1].lower()
                if current_tag == 'label':
                    new_class.label = i.text
                    current_attributes = i.attrib
                    for j in current_attributes:
                        if j.split('}')[-1].lower() == 'lang':
                            new_class.language = current_attributes[j].strip()
                            break
                if current_tag == 'subclassof':
                    current_attributes = i.attrib
                    for j in current_attributes:
                        if j.split('}')[-1].lower() == 'resource':
                            new_class.patent_class_id = current_attributes[j].strip().strip('#')
                            break
                if current_tag == 'intersectionof':
                    intersection = list(i)
                    for j in intersection:
                        current_attributes = j.attrib
                        for attr in current_attributes:
                            if attr.split('}')[-1].lower() == 'about':
                                new_class.interactions.append(current_attributes[attr].strip().strip('#'))
                                break
            onto_list['classes'].append(new_class)
        if block.tag.split('}')[-1].lower() == 'objectproperty':
            attributes = block.attrib
            new_property = OntoProperty()
            for i in attributes:
                if i.split('}')[-1].lower() == 'id':
                    new_property.id = attributes[i]
                    break
            inner_content = list(block)
            for i in inner_content:
                current_tag = i.tag.split('}')[-1].lower()
                if current_tag == 'label':
                    new_property.label = i.text
                    current_attributes = i.attrib
                    for j in current_attributes:
                        if j.split('}')[-1].lower() == 'lang':
                            new_property.language = current_attributes[j].strip()
                            break
                if current_tag == 'subpropertyof':
                    current_attributes = i.attrib
                    for j in current_attributes:
                        if j.split('}')[-1].lower() == 'resource':
                            new_property.parent_id = current_attributes[j].strip().strip('#')
                            break
                if current_tag == 'domain':
                    current_attributes = i.attrib
                    for j in current_attributes:
                        if j.split('}')[-1].lower() == 'resource':
                            new_property.domain_id = current_attributes[j].strip().strip('#')
                            break
                if current_tag == 'range':
                    current_attributes = i.attrib
                    for j in current_attributes:
                        if j.split('}')[-1].lower() == 'resource':
                            new_property.range_id = current_attributes[j].strip().strip('#')
                            break
            onto_list['properties'].append(new_property)
    return  onto_list


def give_comment_info(phrase="", ontology=""):
    graph = load_owl(ontology)
    sentence_analyzer = SentenceAnalyzer()
    sentence_analyzer.analize_sentance(phrase)
    sent_struct = sentence_analyzer.serialyze()
    base_classes = []

    for item in sent_struct:
        if 'word' in item:
            if item['pos'] != 'NPRO':
                p1 = morph.parse(item['word'])
                osn = item['word']
                for w_form in p1:
                    if w_form.tag.POS == item['pos']:
                        n_form = w_form.normal_form
                        if n_form is not None:
                            osn = stemmer_obj.stem(n_form).capitalize()
                            break
                for cl in graph['classes']:
                    if osn == cl.id:
                        base_classes.append(cl)
                        break
        elif 'group_self_characteristics' in item:
            alone_words = []
            group_id = ""
            for word in item['words']:
                p1 = morph.parse(word['word'])
                osn = word['word']
                for w_form in p1:
                    if w_form.tag.POS == word['pos']:
                        n_form = w_form.normal_form
                        if n_form is not None:
                            osn = stemmer_obj.stem(n_form).capitalize()
                            break
                alone_words.append(osn)
            group_id = "".join(alone_words)
            group_found = False
            for cl in graph['classes']:
                if group_id == cl.id:
                    base_classes.append(cl)
                    group_found = True
                    break
            if not group_found:
                for a_w in alone_words:
                    for cl in graph['classes']:
                        if a_w == cl.id:
                            base_classes.append(cl)
                            group_found = True
                            break

    actions_subjects = {}
    existences = {}
    relations_by_prop = {}
    all_rlated_classes = copy.deepcopy(base_classes)


    initial_classes_list_length = len(all_rlated_classes)
    new_classes_list_length = 0

    while initial_classes_list_length - new_classes_list_length != 0:
        initial_classes_list_length = len(all_rlated_classes)

        new_interactions_exist = True
        new_subitems_exist = True

        while new_interactions_exist or new_subitems_exist:
            new_interactions_exist = False
            new_subitems_exist = False
            for item in graph['classes']:
                if len(item.interactions) > 0:
                    for i in all_rlated_classes:
                        if i.id in item.interactions:
                            if item not in all_rlated_classes:
                                all_rlated_classes.append(item)
                                new_interactions_exist = True
            for item in all_rlated_classes:
                if len(item.interactions) > 0:
                    for i in item.interactions:
                        for j in graph['classes']:
                            if j.id == i:
                                if j not in all_rlated_classes:
                                    all_rlated_classes.append(j)
                                    new_subitems_exist = True

        '''
        new_all_rlated_classes = []
        for item in all_rlated_classes:
            is_sub = False
            for item_2 in all_rlated_classes:
                if item.id in item_2.interactions:
                    is_sub = True
                    break
            if not is_sub:
                new_all_rlated_classes.append(item)
        all_rlated_classes = new_all_rlated_classes
    
        del(new_all_rlated_classes)
        '''
        '''
        relations_by_prop = {
            "class_id": {
                "actions": {
                    "action_class_id": "id",
                    "action_prop": ["act prop classes list"],
                    "action_conditions": [["conditions set"]]
                },
                "attributes": ["list of attribute classes"]
            }
            
        }
        '''

        for item in graph['properties']:
            for i in all_rlated_classes:
                if item.domain_id == i.id:
                    if i.id not in relations_by_prop:
                        relations_by_prop[i.id] = {
                            "actions": {
                                "action_class_id": [],
                                "action_prop": {},
                                "action_conditions": {}
                            },
                            "attributes": []
                        }
                        if item.parent_id == "":
                            for cl_item in graph['classes']:
                                if cl_item.id == item.range_id:
                                    if cl_item.patent_class_id == "Action":
                                        if cl_item.id not in relations_by_prop[i.id]["actions"]["action_class_id"]:
                                            relations_by_prop[i.id]["actions"]["action_class_id"].append(cl_item.id)
                                            if cl_item not in all_rlated_classes:
                                                all_rlated_classes.append(cl_item)
                                    elif cl_item.patent_class_id == "Attribute":
                                        if cl_item.id not in relations_by_prop[i.id]["attributes"]:
                                            relations_by_prop[i.id]["attributes"].append(cl_item.id)
                                            if cl_item not in all_rlated_classes:
                                                all_rlated_classes.append(cl_item)
                    else:
                        if item.parent_id == "":
                            for cl_item in graph['classes']:
                                if cl_item.id == item.range_id:
                                    if cl_item.patent_class_id == "Action":
                                        if cl_item.id not in relations_by_prop[i.id]["actions"]["action_class_id"]:
                                            relations_by_prop[i.id]["actions"]["action_class_id"].append(cl_item.id)
                                            if cl_item not in all_rlated_classes:
                                                all_rlated_classes.append(cl_item)
                                    elif cl_item.patent_class_id == "Attribute":
                                        if cl_item.id not in relations_by_prop[i.id]["attributes"]:
                                            relations_by_prop[i.id]["attributes"].append(cl_item.id)
                                            if cl_item not in all_rlated_classes:
                                                all_rlated_classes.append(cl_item)

        for item in relations_by_prop:
            for action in relations_by_prop[item]['actions']['action_class_id']:
                for prop in graph['properties']:
                    if prop.parent_id != "":
                        for sub_prop in graph['properties']:
                            if prop.parent_id == sub_prop.id:
                                if sub_prop.domain_id == item and sub_prop.range_id == action:
                                    if action not in relations_by_prop[item]['actions']["action_conditions"]:
                                        relations_by_prop[item]['actions']["action_conditions"][action] = [prop.range_id]
                                    else:
                                        if prop.range_id not in relations_by_prop[item]['actions']["action_conditions"][action]:
                                            relations_by_prop[item]['actions']["action_conditions"][action].append(prop.range_id)
                                    for cl_item in graph['classes']:
                                        if cl_item.id == prop.range_id:
                                            if cl_item not in all_rlated_classes:
                                                all_rlated_classes.append(cl_item)
                                                break
                    else:
                        for cl_item in graph['classes']:
                            if prop.domain_id == cl_item.id:
                                if action == prop.domain_id:
                                    for cl_item_2 in graph['classes']:
                                        if cl_item_2.id == prop.range_id:
                                            if cl_item_2.patent_class_id == 'Adverb':
                                                if action not in relations_by_prop[item]['actions']["action_prop"]:
                                                    relations_by_prop[item]['actions']["action_prop"][action] = [
                                                        cl_item_2.id]
                                                else:
                                                    if cl_item_2.id not in relations_by_prop[item]['actions']["action_prop"][action]:
                                                        relations_by_prop[item]['actions']["action_prop"][action].append(
                                                            cl_item_2.id)
                                                if cl_item_2 not in all_rlated_classes:
                                                    all_rlated_classes.append(cl_item_2)
                                                    break

        for item in graph['properties']:
            if item.parent_id == "Existence":
                for i in all_rlated_classes:
                    if i.id == item.domain_id:
                        if i.id not in existences:
                            existences[i.id] = []
                for i in graph['classes']:
                    if i.id == item.range_id:
                        if item.domain_id in existences:
                            if i.id not in existences[item.domain_id]:
                                existences[item.domain_id].append(i.id)
                                if i not in all_rlated_classes:
                                    all_rlated_classes.append(i)

        for item in relations_by_prop:
            for action in relations_by_prop[item]['actions']['action_class_id']:
                for prop in graph['properties']:
                    if prop.parent_id != "":
                        if prop.domain_id == action:
                            if action not in actions_subjects:
                                actions_subjects[action] = {}
                                if prop.parent_id not in actions_subjects[action]:
                                    actions_subjects[action][prop.parent_id] = [prop.range_id]
                                else:
                                    if prop.range_id not in actions_subjects[action][prop.parent_id]:
                                        actions_subjects[action][prop.parent_id].append(prop.range_id)
                            else:
                                if prop.parent_id not in actions_subjects[action]:
                                    actions_subjects[action][prop.parent_id] = [prop.range_id]
                                else:
                                    if prop.range_id not in actions_subjects[action][prop.parent_id]:
                                        actions_subjects[action][prop.parent_id].append(prop.range_id)
                            for i in graph['classes']:
                                if i.id == prop.range_id:
                                    if prop.domain_id in relations_by_prop[item]['actions']['action_class_id']:
                                        if i not in all_rlated_classes:
                                            all_rlated_classes.append(i)

        new_classes_list_length = len(all_rlated_classes)

    counter = 0
    for i in list(relations_by_prop):
        if (len(relations_by_prop[i]['actions']['action_class_id']) == 0 and
            len(relations_by_prop[i]['actions']['action_prop']) == 0 and
            len(relations_by_prop[i]['actions']['action_conditions']) == 0 and
            len(relations_by_prop[i]['attributes']) == 0):
            relations_by_prop.pop(i, None)
            counter -= 1
        counter += 1

    output = {
        "base_classes": base_classes,
        "all_rlated_classes": all_rlated_classes,
        "relations": relations_by_prop,
        "actions_subjects": actions_subjects,
        "existences": existences
    }

    return output


def generate_comment_on_phrase(phrase="", ontology=""):
    raw_info = give_comment_info(phrase=phrase, ontology=ontology)
    primary_existences = {}
    primary_relations = {}

    print(raw_info)

    for i in raw_info["base_classes"]:
        for key in raw_info["existences"]:
            if key == i.id:
                primary_existences[key] = raw_info["existences"][key]
            else:
                for cl in raw_info["all_rlated_classes"]:
                    if cl.id == key:
                        for cl_2 in cl.interactions:
                            if cl_2 == i.id:
                                primary_existences[key] = raw_info["existences"][key]
                                break
        for key in raw_info["relations"]:
            if key == i.id:
                primary_relations[key] = raw_info["relations"][key]
            else:
                for cl in raw_info["all_rlated_classes"]:
                    if cl.id == key:
                        for cl_2 in cl.interactions:
                            if cl_2 == i.id:
                                primary_existences[key] = raw_info["relations"][key]
                                break
    if len(primary_relations) == 0:
        for i in primary_existences:
            for key in raw_info["relations"]:
                if key == i:
                    primary_relations[key] = raw_info["relations"][key]
    if len(primary_relations) == 0:
        for i in primary_existences:
            for key in raw_info["relations"]:
                for item in primary_existences[i]:
                    if item == key:
                        primary_relations[key] = raw_info["relations"][key]

    primary_phrases = []
    for i in primary_existences:
        w_2_base_form = []
        for item in raw_info["all_rlated_classes"]:
            if item.id == i:
                if len(item.interactions) == 0:
                    w_2_base_form = [item.label]
                    break
                else:
                    for cl in item.interactions:

                        for item_2 in raw_info["all_rlated_classes"]:
                            if cl == item_2.id and item_2.patent_class_id == 'Thing':
                                if item_2.label not in w_2_base_form:
                                    w_2_base_form.append(item_2.label)
                            elif cl == item_2.id and item_2.patent_class_id != 'Thing':
                                for cl_2 in item_2.interactions:
                                    for item_3 in raw_info["all_rlated_classes"]:
                                        if cl_2 == item_3.id and item_3.patent_class_id == 'Thing':
                                            if item_3.label not in w_2_base_form:
                                               w_2_base_form.append(item_3.label)

        for j in primary_existences[i]:
            for item in raw_info["all_rlated_classes"]:
                if item.id == j:
                    w_base_form = []
                    if len(item.interactions) == 0:
                        w_base_form = [item.label]
                    else:
                        for cl in item.interactions:
                            for item_2 in raw_info["all_rlated_classes"]:
                                if cl == item_2.id and item_2.patent_class_id == 'Thing':
                                    if item_2.label not in w_base_form:
                                        w_base_form.append(item_2.label)
                                elif cl == item_2.id and item_2.patent_class_id != 'Thing':
                                    for cl_2 in item_2.interactions:
                                        for item_3 in raw_info["all_rlated_classes"]:
                                            if cl_2 == item_3.id and item_3.patent_class_id == 'Thing':
                                                if item_3.label not in w_base_form:
                                                    w_base_form.append(item_3.label)
                    current_phrase_text = " ".join(w_base_form).capitalize() + " є "
                    counter = 0
                    for w_2 in w_2_base_form:
                        p1 = morph.parse(w_2)
                        for w_form in p1:
                            if w_form.tag.POS == "NOUN":
                                if counter == 0:
                                    suff_form = w_form.inflect({'ablt'})
                                else:
                                    suff_form = w_form.inflect({'gent'})
                                if suff_form is not None:
                                    current_phrase_text += suff_form.word + " "
                                else:
                                    current_phrase_text += w_2 + " "
                                break
                        counter += 1
                    current_phrase_text = current_phrase_text.strip() + "."
                    if current_phrase_text not in primary_phrases:
                        primary_phrases.append(current_phrase_text)

    for i in primary_relations:
        for item in raw_info["all_rlated_classes"]:
            if item.id == i:
                w_base_form = []
                if len(item.interactions) == 0:
                    w_base_form = [item.label]
                else:
                    for cl in item.interactions:
                        for item_2 in raw_info["all_rlated_classes"]:
                            if cl == item_2.id and item_2.patent_class_id == 'Thing':
                                if item_2.label not in w_base_form:
                                    w_base_form.append(item_2.label)
                            elif cl == item_2.id and item_2.patent_class_id != 'Thing':
                                for cl_2 in item_2.interactions:
                                    for item_3 in raw_info["all_rlated_classes"]:
                                        if cl_2 == item_3.id and item_3.patent_class_id == 'Thing':
                                            if item_3.label not in w_base_form:
                                                w_base_form.append(item_3.label)

                gender = 'masc'
                number = 'sing'
                p1 = morph.parse(w_base_form[0])
                for w_form in p1:
                    if w_form.tag.POS == 'NOUN':
                        if w_form.tag.gender is not None:
                            gender = w_form.tag.gender
                        if w_form.tag.number is not None:
                            number = w_form.tag.number
                        break
                for action in primary_relations[i]['actions']['action_class_id']:
                    current_phtase_text = " ".join(w_base_form).capitalize() + " "
                    for v_item in raw_info["all_rlated_classes"]:
                        if v_item.id == action:
                            w_2_base_form = v_item.label
                            p1 = morph.parse(w_2_base_form)
                            suff_verb_form = w_2_base_form
                            action_prop_word = ""
                            for action_prop in primary_relations[i]['actions']['action_prop']:
                                if action_prop == action:
                                    for v_prop_item in raw_info["all_rlated_classes"]:
                                        for v_prop_test_item in primary_relations[i]['actions']['action_prop'][action_prop]:
                                            if v_prop_item.id == v_prop_test_item:
                                                action_prop_word = v_prop_item.label
                                                break
                            for w_form in p1:
                                if w_form.tag.POS == 'VERB':
                                    suff_form = w_form.inflect({gender, number, 'past'})
                                    if suff_form is None:
                                        suff_form = w_form.inflect({gender, number})
                                    if suff_form is None:
                                        if action_prop_word == "":
                                            suff_form = w_form.inflect({gender})
                                        elif action_prop_word in ['зараз', 'тепер', 'сьогодні']:
                                            p_test = morph.parse('проживає')[0]
                                            suff_form = w_form.inflect({'pres', '3per'})
                                        else:
                                            suff_verb_form = w_2_base_form
                                    if suff_form is None:
                                        suff_form = w_form.inflect({gender})
                                    if suff_form is not None:
                                        suff_verb_form = suff_form.word
                                    break
                            if action_prop_word != "":
                                current_phtase_text += action_prop_word + " " + suff_verb_form
                            else:
                                current_phtase_text += suff_verb_form
                            for action_condition in primary_relations[i]['actions']['action_conditions']:
                                if action_condition == action:
                                    for condition in primary_relations[i]['actions']['action_conditions'][action_condition]:
                                        for cond_item in raw_info["all_rlated_classes"]:
                                            if cond_item.id == condition:
                                                cond_base_form = []
                                                cond_ids = []
                                                if len(cond_item.interactions) == 0:
                                                    cond_base_form = [cond_item.label]
                                                    cond_ids = [cond_item.id]
                                                else:
                                                    for cond_cl in cond_item.interactions:
                                                        for cond_item_2 in raw_info["all_rlated_classes"]:
                                                            if cond_cl == cond_item_2.id and cond_item_2.patent_class_id == 'Thing':
                                                                if cond_item_2.label not in cond_base_form:
                                                                    cond_ids.append(cond_item_2.id)
                                                                    cond_base_form.append(cond_item_2.label)
                                                            elif cond_cl == cond_item_2.id and cond_item_2.patent_class_id != 'Thing':
                                                                for cond_cl_2 in cond_item_2.interactions:
                                                                    for cond_item_3 in raw_info["all_rlated_classes"]:
                                                                        if cond_cl_2 == cond_item_3.id and cond_item_3.patent_class_id == 'Thing':
                                                                            if cond_item_3.label not in cond_base_form:
                                                                                cond_base_form.append(cond_item_3.label)
                                                                                cond_ids.append(cond_item_3.id)

                                                conditions_cases = {}
                                                for sup_actions in raw_info["actions_subjects"]:
                                                    if action == sup_actions:
                                                        for case in raw_info["actions_subjects"][sup_actions]:
                                                            for sup in raw_info["actions_subjects"][sup_actions][case]:

                                                                if sup in cond_ids:
                                                                    conditions_cases[sup] = case

                                                cond_counter = 0
                                                for condition_item in cond_base_form:
                                                    p1 = morph.parse(condition_item)
                                                    for cond_w_form in p1:
                                                        if cond_w_form.tag.POS == "NOUN":
                                                            current_cond_form = cond_w_form

                                                            is_loct = False
                                                            if condition_item.capitalize() not in conditions_cases:
                                                                if cond_counter == 0:
                                                                    current_cond_form = cond_w_form.inflect({'loct'})
                                                                else:
                                                                    current_cond_form = cond_w_form.inflect({'gent'})
                                                            else:
                                                                if conditions_cases[condition_item.capitalize()] == 'GentSup':
                                                                    current_cond_form = cond_w_form.inflect({'gent'})
                                                                elif conditions_cases[condition_item.capitalize()] == 'DatvSup':
                                                                    current_cond_form = cond_w_form.inflect({'datv'})
                                                                elif conditions_cases[condition_item.capitalize()] == 'AccsSup':
                                                                    current_cond_form = cond_w_form.inflect({'accs'})
                                                                elif conditions_cases[condition_item.capitalize()] == 'AbltSup':
                                                                    current_cond_form = cond_w_form.inflect({'ablt'})
                                                                elif conditions_cases[condition_item.capitalize()] == 'LoctSup':
                                                                    current_cond_form = cond_w_form.inflect({'loct'})
                                                                    is_loct = True
                                                            if current_cond_form is not None:
                                                                if cond_counter == 0 or is_loct:
                                                                    current_phtase_text += " у " + current_cond_form.word
                                                                else:
                                                                    current_phtase_text += " " + current_cond_form.word
                                                            else:
                                                                if cond_counter == 0:
                                                                    current_phtase_text += " у " + cond_w_form.word
                                                                else:
                                                                    current_phtase_text += " " + cond_w_form.word
                                                            break
                                                    cond_counter += 1

                                                break
                            if current_phtase_text + "." not in primary_phrases:
                                primary_phrases.append(current_phtase_text + ".")
    intro = ""
    if len(raw_info['base_classes']) > 1:
        intro = "Ви загадували такиі речі як "
        for i in raw_info['base_classes']:
            intro += i.label.lower() + ", "
        intro = intro.strip().strip(',') + ". "
        intro += "От що я можу розповісти. "
    elif len(raw_info['base_classes']) > 0:
        intro = "Ви загадували таку річ як "
        intro += raw_info['base_classes'][0].label.lower() + "."
        intro += " От що я можу розповісти. "
    else:
        intro = "Нажаль я не розбираюся в таких речах. "

    return intro + " ".join(primary_phrases)



if __name__ == '__main__':
    set_language('uk')
    from foreign_libraries import morph, stemmer_obj
    from analitic_tools import SentenceAnalyzer
    #input_phrase = "Який твій улюблений фільм?"
    input_phrase = "Ми пишемо програму."
    print(generate_comment_on_phrase(phrase=input_phrase,
                 ontology="D:/по Величко/untitled1/ont_text/" + "text_2.owl"))


