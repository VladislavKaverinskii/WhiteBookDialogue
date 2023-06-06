# -*- coding: utf-8 -*-

import networkx as nx # Для работы с графами (устанавливается отдельно через pip)
import pylab as plt # Для визуализации графа (устанавливается отдельно через pip)
import xml.etree.ElementTree # Парсер для xml
import nltk
from converter.elementary_classes import * # Импортируем классы для объектов элементарных сущностей (слов, именных групп, записей)
from converter.foreign_libraries import morph

def check_advb_by_fections(word):
    # Вспомагательная функция для проверки, является ли слово прилагательным по характерным флексиям
    ADVB_flections = ["ий", "ого", "ому", "им", "их", "им", "ими", "их", "ої", "ій", "ою", "ій"] # Окончания прилагательных
    if 'ADJF' in [i.tag.POS for i in morph.parse(word)]: # Определение может ли являться слово прилагательным на основе pymprphy
        return True
    for i in reversed(range(1, 4)): # Отделяем потенциальные окончания
        if word[-i:] in ADVB_flections: # Если такое окончание есть в списке, считаем слово прилагательным
            return True
    return False


class AmbiguitySolvers:
    """
    Класс, содержащий функции для решения неоднозначностей в отношении части речи на основе анализа соседних слов
    """

    def __init__(self):
        self.prepositions_of_cases = {}
        # Считываетм из xml-файла 'cases_prep.xml' данные о предлогоах, характеорных для падежей.
        # Для этого используем персер xml файлов.
        e = xml.etree.ElementTree.parse('cases_prep.xml').getroot()
        for case in list(e):
            self.prepositions_of_cases[case.get("id")] = [word.text for word in case.findall('item')]

    def __fetch_word_to_Word_class__(self, counter, list_of_words):
        """
        Функция для приведения слова из скиска к классу Word
        :param counter: номер слова в списке
        :param list_of_words: список слов
        :return:
        """
        word = list_of_words[counter]  # Анализируемое слово
        if not isinstance(word, Word): # Если слово не является объектом класса Word
            if isinstance(word, str): # Если слово из списка - строка
                return Word(word=word)
            elif isinstance(word, dict): # Если слово из списка - словарь
                return Word(word=word["word"])
            return None # Случай если по ошибке передали что-то непонятное
        return word # Если слово из списка уже и так является объектом класса Word

    def noun_or_prep(self, counter, list_of_words):
        # Неоднаозначность "существительное или предлог"
        # Если это предлог, то после него должно идти существительное или прилагательное (или их группа), за которым
        # идёт существительное. Падеж существительного должен соответствовать предлогу.
        # Предлоги идут перед словами, поэтому назад смысла двигаться нет.
        word = self.__fetch_word_to_Word_class__(counter, list_of_words) # Приводим слово к объекту Word
        if word is None: return "neither" # Если приведение к объекту Word не удалось, возвращаем "neither"

        local_counter = counter + 1
        to_continue = True
        while local_counter < len(list_of_words) and to_continue: # Перебираем слова из списка начиная со следующего за данным слова
            current_word = self.__fetch_word_to_Word_class__(local_counter, list_of_words) # Приводим каждое перибираемое слово из списка к объекту Word
            if current_word is None: return "neither"

            p_1 = morph.parse(current_word.word) # Поучаем варанты морфологического разбора для данного слова

            # Прверяем, является ли существительным или местоимением данное слово
            to_continue = False # Продолжать ли перебор слов. Останавливаем продвижение, если пришли к слову,
                                # которое не существительное, не прилагательное, не местоимение, ни числительное,
                                # ни компаратив, ни наречие, ни предикатив, ни частица
            for i in p_1: # Перебираем варианты разбора слова
                # Если слово в каком-то из своих вариантов разбора является существительным, местоимением, прилагательным или числительным,
                # считаем, что в списке вариантов разбора есть именное слово
                if i.tag.POS == 'NOUN' or i.tag.POS == "NPRO" or i.tag.POS == 'ADJF' or i.tag.POS == 'NUMR':
                    to_continue = True
                    # Проверяем, может есть ли такой падеж в списке предлогов, характерных для падежей
                    if i.tag.case in self.prepositions_of_cases:
                        # Если исследуемое слово содержится в скиске предлогов, характерных для данного падежа следующего слова,
                        # считаем это слово предлогом
                        if word.word.lower() in self.prepositions_of_cases[i.tag.case]:
                            return "PREP"
                # Если слово слово в каком-то из своих вариантов разбора является компаративом, наречием, предекативом или частицей,
                # продолжаем перебор, но имеем в виду, что эти слова ещё не являются определяющими
                elif i.tag.POS == 'COMP' or i.tag.POS == "ADVB" or i.tag.POS == 'PRED' or i.tag.POS == "PRCL":
                    to_continue = True

            if not to_continue: # Если вдруг встретели слово, перед которым не может быть предлога, проверяем,
                                #  может ли данное слово быть существительным
                if "NOUN" in [j.tag.POS for j in morph.parse(word.word)]:
                    return 'NOUN'
                else:
                    return "neither"
            local_counter += 1
        # Если перебрали все слова, но слово перед которым может быть такой предлог не нашли,
        # проверяем, может ли данное слово быть существительным
        if "NOUN" in [j.tag.POS for j in morph.parse(word.word)]:
            return 'NOUN'
        return "neither"

    def noun_or_prcl(self, counter, list_of_words):
        # Неоднаозначность "существительное или частица"
        # Приводим каждое перибираемое слово из списка к объекту Word
        word = self.__fetch_word_to_Word_class__(counter, list_of_words) # Приводим каждое перибираемое слово из списка к объекту Word
        if word is None: return "neither"

        # Прверяем на сооответствие послеующих шаблонов, где это будет частица
        # Шаблон 1: частица + (факультативно) наречие, компаратив или частица +
        # существительное или местоимение в дательном местном или родительном падеже +
        # (факультативно) наречие, компаратив или частица +
        # (факультативно) существительное в винительном падеже +
        #  (факультативно) наречие, компаратив или частица + инфинитив глагола
        # Например (со всеми факультативными словами): Як краще мені швидко дерево дійсно знайти
        was_noun = False # Встрелилось ли среди последующих слов существительное
        was_inf = False # Встретился ли среди последующих инфинитив
        template_fit = True # Соответствие шаблону
        # Перебираем слова из списка начинае со следующего за расматриваемым словом
        local_counter = counter + 1
        while local_counter < len(list_of_words):
            current_word = self.__fetch_word_to_Word_class__(local_counter, list_of_words) # Приводим каждое перибираемое слово из списка к объекту Word
            if current_word is None: return "neither"

            p_1 = morph.parse(current_word.word) # Получаем все варианты морфологического разбора каждлго из слов
            for i in p_1: # Перебираем варианты разбора
                if i.tag.POS == "ADVB" or i.tag.POS == "COMP" or i.tag.POS == "PRCL" or i.tag.POS == "PREP" or i.tag.POS == "PRED":
                    # Наличие наречия, компаратива, частицы, предлога или пердикатива на любой из позиций не нарушает шаблона
                    template_fit = True
                    break
                elif i.tag.POS == "NOUN" or i.tag.POS == "NPRO":
                    # Существительные или местоимения для соответствия данному шаблону должны стоять в дательном,
                    # местном, родительном или винительном падеже. При этом, только дательный, местный и роительный
                    # являются соответствующими одному из достаточных условий
                    if i.tag.case == "datv" or i.tag.case == "loct" or i.tag.case == "gent":
                        was_noun = True
                        template_fit = True
                        break
                    elif i.tag.case == "accs":
                        template_fit = True
                        break
                    else:
                        template_fit = False # Наличе в послеовательности слов существительного или
                                             # местоимения в ругом падеже ставит сомнение на соответствие шаблону,
                                             # которое может быть снятот только другим вариантом разбора,
                                             # если таковой имеется
                # Если существительное в дательном, местном или родительном паеже уже встретилось,
                # проверяем слово на то, что это инфинитив
                # Особенность pymorphy: инфинетив может быть иентифицирован как "INFN" или как "VERB",
                # но со свойством "infn" в поле tag
                elif was_noun and (i.tag.POS == "INFN" or (i.tag.POS == "VERB" and "infn" in i.tag)):
                    was_inf = True
                    template_fit = True
                    break
                else: # Не соответствие ни одному из вариантов повод для предположения несоответствия шаблону,
                      # которое мжет быть снято только другим вариантом разбора
                    template_fit = False
            if not template_fit:  # Если идентифицированно несоответствие шаблону, дальнейший перебор не имеет смысла
                break

            if was_inf and was_noun: # Если выполнены достаточные условия для соответствия шаблону,
                                     # дальнейший перебор слов можно прекратить и вернуть,
                                     # то, что анализируемое слово является частицей
                return "PRCL"

            local_counter += 1

        # Шаблон 2: частица + (факультативно) прилагательное +
        # (факультативно) наречие, компаратив или частица
        # (факультативно) прилагательное
        # существительное или местоимение в именительном падеже +
        # (факультативно) существительное или местоимение +
        # (факультативно) наречие, компаратив или частица + глагол
        # Например (со всеми факультативными словами): Як гарно професійний художник це схоже намалював
        # сокрвщённый пример: Як він працює
        was_noun = False # Встрелилось ли среди последующих слов существительное в именительном падеже
        was_verb = False # Встрелся ли среди последующих слов глагод
        template_fit = True # Признак соответствия шаблону
        local_counter = counter + 1 # Перевымтавляем счётчик
        while local_counter < len(list_of_words):
            current_word = self.__fetch_word_to_Word_class__(local_counter,
                                                             list_of_words)  # Приводим каждое перибираемое слово
                                                                             # из списка к объекту Word
            if current_word is None: return "neither"

            p_1 = morph.parse(current_word.word)  # Получаем варианты разбора для каждого из последующих слов

            for i in p_1: # Анализируем варианты разбора
                if i.tag.POS == "ADVB" or i.tag.POS == "COMP" or i.tag.POS == "PRCL" or i.tag.POS == "PREP" or i.tag.POS == "PRED":
                    # Наличие наречия, компаратива, частицы, предлога или пердикатива на любой из позиций не нарушает шаблона
                    template_fit = True
                    break
                elif i.tag.POS == "VERB": # Одним из необхоимых условий является наличие глагола
                    was_verb = True
                    template_fit = True
                    break
                elif i.tag.POS == "NOUN" or i.tag.POS == "NPRO": # Другим необходимым условием является наличие
                                                                 # существительного или местоимения
                                                                 # в именительонм падеже
                    if i.tag.case == "nomn": # Проверка на падеж
                        was_noun = True
                        template_fit = True
                        break
                elif i.tag.POS == "ADJF":
                    # Наличие прилагательного не нарушает шаблона
                    template_fit = True
                    break
                else:
                    template_fit = False

            if not template_fit:  # Если идентифицированно несоответствие шаблону, дальнейший перебор не имеет смысла
                break

            if was_verb and was_noun:  # Если выполнены достаточные условия для соответствия шаблону,
                                       # дальнейший перебор слов можно прекратить и вернуть,
                                       # то, что анализируемое слово является частицей
                return "PRCL"

            local_counter += 1

        # Шаблон 3: частица + (факультативно) наречие, компаратив или частица +
        # (факультативно) прилагательное
        # (факультативно)существительное или местоимение в родительном падеже +
        # существительное или местоимение в именительном падеже
        was_noun = False # Встрелилось ли среди последующих слов существительное в именительном падеже
        template_fit = True # Признак соответствия шаблону
        local_counter = counter + 1
        while local_counter < len(list_of_words):
            current_word = self.__fetch_word_to_Word_class__(local_counter,
                                                             list_of_words)  # Приводим каждое перибираемое слово
                                                                             # из списка к объекту Word
            if current_word is None: return "neither"

            p_1 = morph.parse(current_word.word) # Получаем варианты разбора для каждого из последующих слов

            for i in p_1: # Анализируем варианты разбора
                if i.tag.POS == "ADJF" or i.tag.POS == "ADVB" or i.tag.POS == "COMP" or i.tag.POS == "PRCL" or i.tag.POS == "PREP" or i.tag.POS == "PRED":
                    # Наличие прилагательного, наречия, компаратива, частицы, предлога или пердикатива на любой из позиций не нарушает шаблона
                    template_fit = True
                    break
                elif i.tag.POS == "NOUN" or i.tag.POS == "NPRO":
                    # Допускается наличие существительного только в именительном пажеде (достаточное условие)
                    # или в родительном падеже (необходимое условие)
                    if i.tag.case == "nomn":
                        was_noun = True
                        template_fit = True
                        break
                    elif i.tag.case == "gent":
                        template_fit = True
                        break
                else:
                    template_fit = False

            if not template_fit: # Если идентифицированно несоответствие шаблону, дальнейший перебор не имеет смысла
                break

            if was_noun: # Если выполнены достаточные условия для соответствия шаблону,
                         # дальнейший перебор слов можно прекратить и вернуть,
                         # то, что анализируемое слово является частицей
                return "PRCL"

            local_counter += 1

        return "NOUN"

    def noun_or_npro(self, counter, list_of_words):
        """
        Разрешение неоднозначности существительное или местоимение
        :param counter:
        :param list_of_words:
        :return:
        """

        word = self.__fetch_word_to_Word_class__(counter,
                                                         list_of_words)  # Приводим каждое перибираемое слово
        # из списка к объекту Word
        if word is None: return "neither"

        # Прверяем на сооответствие послеующих шаблонов, где это будет местоимение
        was_noun = False # Наличие существительного после рассматриваемого слова
        template_fit = True # Соответствие шаблону
        local_counter = counter + 1
        while local_counter < len(list_of_words) and template_fit: # Перебираем последующие слова из списка,
                                                                   # пока он не будет окончен или будет
                                                                   #  поределно несоответствие шаблону
            current_word = self.__fetch_word_to_Word_class__(local_counter,
                                                     list_of_words)  # Приводим каждое перибираемое слово
                                                                     # из списка к объекту Word
            if current_word is None: return "neither"

            p_1 = morph.parse(current_word.word) # Получаем варианты разбора для каждого из перебираемых слов

            for i in p_1:  # Перебираем варианты разбора
                # Наречье, компаратив, частица, предлог, предикатив не противоречат шаблону, но не являются определяющими
                if i.tag.POS == "ADVB" or i.tag.POS == "COMP" or i.tag.POS == "PRCL" or i.tag.POS == "PREP" or i.tag.POS == "PRED":
                    template_fit = True
                    # break
                elif i.tag.POS == "NOUN" or i.tag.POS == "NPRO":  # Если встретилось существительное или местоимение
                    test_case = i.tag.case  # Определяем падеж перибираемого слова
                    # Определяем возможные варианты падежей проверяемого слова (получаем список)
                    word_possible_cases = [w.tag.case for w in morph.parse(word.word) if w.tag.case is not None]
                    if test_case in word_possible_cases:  # Наличие существительного или местоимения
                                                          # в соответствующем падеже является признаком местоимения
                        was_noun = True
                        template_fit = True
                        break
                    else: # Наличие существительного в другом падеже - это признак несоответствия шаблону
                        template_fit = False
                        # break
                else:
                    template_fit = False

            if was_noun:
                return "NPRO"

            local_counter += 1

        was_verb = False  # Признак наличия глагода
        template_fit = True  # Соответствие шаблону
        local_counter = counter + 1
        while local_counter < len(list_of_words) and template_fit:
            current_word = self.__fetch_word_to_Word_class__(local_counter,
                                                             list_of_words)  # Приводим каждое перибираемое слово
                                                                             # из списка к объекту Word
            if current_word is None: return "neither"

            p_1 = morph.parse(current_word.word)  # Получаем варианты разбора

            for i in p_1:
                # Наречье, компаратив, частица, предлог, предикатив не противоречат шаблону, но не являются определяющими
                if i.tag.POS == "ADVB" or i.tag.POS == "COMP" or i.tag.POS == "PRCL" or i.tag.POS == "PREP" or i.tag.POS == "PRED":
                    template_fit = True
                    # break
                elif i.tag.POS == "VERB":  # Если обнаружен глагол
                    test_number = i.tag.number  # Определяем число этого глагола
                    test_gender = i.tag.gender  # Определяем род глагола
                    # Получаем возможные варианты числа и рода рассматриваемого слова
                    word_possible_numbers = [w.tag.number for w in morph.parse(word.word) if w.tag.number is not None]
                    word_possible_genders = [w.tag.gender for w in morph.parse(word.word) if w.tag.gender is not None]
                    # Проверяем возможность соответствия рассматриваемого слова роду и числу обнаруженного глагола
                    if test_number in word_possible_numbers:
                        was_verb = True
                        template_fit = True
                        break
                    elif test_gender in word_possible_genders:
                        was_verb = True
                        template_fit = True
                        break
                    else: # Несоответствие по чилслу и роду является признаком несоответствия шаблону
                        template_fit = False
                        break
                else:
                    template_fit = False

            if was_verb: # Начичие соглвасованного галгола считаем признаком того,
                         # что рассматриваемое слово является всё-таки местоимением
                return "NPRO"

            local_counter += 1

        return "NOUN"

    def noun_or_adj(self, counter, list_of_words):
        # Неоднаозначность прилагательное или существительное (самая распространённая)
        # Если это прилагательное, то оно должно быть связанно с существительным или местоимением
        # Ищем существительное или местоимение после этого предполагаемого прилагательного
        # Оно должно иметь тот же падеж, род и число

        word = copy.deepcopy(list_of_words[counter]) # Создаём копию объекта слова из списка

        if not isinstance(list_of_words[counter], Word): # Приводим слово к объекту класса Word
            word = Word(word=word["word"])

        p = morph.parse(word.word)  # Поучаем варианты морфологического разбора слова
        local_counter = counter + 1
        is_noun = True # Признак того, что после рассматриваемого слова встретилось существительное
        while local_counter < len(list_of_words):  # Перебираем последующие слова из переданного списка
            if isinstance(list_of_words[local_counter], Word):
                p_1 = morph.parse(list_of_words[local_counter].word)
            else:
                p_1 = morph.parse(list_of_words[local_counter]["word"])
            # Прверяем, является ли существительным или местоимением данное слово из списка
            for i in p_1:
                if i.tag.POS == 'NOUN' or i.tag.POS == "NPRO":  # Если встетилось существительное или местоимение
                    # Проверяем соответствие по падежу и роду
                    if i.tag.case in [j.tag.case for j in p if
                                      (j.tag.POS != 'NOUN' or j.tag.POS != "NPRO") and i.tag.gender == j.tag.gender]:
                        return 'ADJF'
            local_counter += 1
        if is_noun: # Если согласованного существительного не найдено, считаем слово существительным
            return 'NOUN'

    def noun_or_verb(self, counter, list_of_words):
        # Иногда существительное можно перепутать с глаголом
        # Проверяем наличие других глаголов
        # Если они есть, то это однородные глагольные сказуемые они должны стоять в одной форме
        # ВОзможно также наличие инфинитива
        # Ищем вперёд

        word = copy.deepcopy(list_of_words[counter]) # Создаём копию объекта слова из списка

        if not isinstance(list_of_words[counter], Word): # Приводим слово к объекту класса Word
            word = Word(word=word["word"])

        local_counter = counter + 1
        other_verb_exists = False  # Наличие других глаголов
        while local_counter < len(list_of_words):
            verb_is_sutible, other_verb_exists = self.__verb_test__(word, list_of_words, local_counter, other_verb_exists) # Проверка наличия согласованного глагола
            if verb_is_sutible: # Проверка наличия согласованного глагола
                return 'VERB'
            local_counter += 1

        if not other_verb_exists: # Если не был однаружен глагол,
                                              # перибираем список слова в обратном направлении
            local_counter = counter - 1
            while local_counter >= 0:
                verb_is_sutible, other_verb_exists = self.__verb_test__(word, list_of_words, local_counter, other_verb_exists) # Проверка наличия согласованного глагола
                if verb_is_sutible:
                    return 'VERB'
                local_counter -= 1

        if not other_verb_exists:
            return 'VERB'
        else:
            return 'NOUN'

    def __check_verb__(self, current_word, test_word_obj):
        """
        Проверка глаголов на согласованность
        :return:
        """
        p = morph.parse(test_word_obj.word)
        if current_word.tag.person in [j.tag.person for j in p if j.tag.POS == 'VERB']:
            if current_word.tag.number in [j.tag.number for j in p if j.tag.POS == 'VERB']:
                if current_word.tag.tense in [j.tag.tense for j in p if j.tag.POS == 'VERB']:
                    return True
        return False

    def __verb_test__(self, word, list_of_words, local_counter, other_verb_exists):
        """
        Поиск согласованного глагола
        :param word: Тестируемое слово
        :param list_of_words: Список слов предложения
        :param local_counter: # Номер слова в списке, с которым сравнивается тестируемое слово
        :return:
        """
        #other_verb_exists = False
        if isinstance(list_of_words[local_counter], Word):
            p_1 = morph.parse(list_of_words[local_counter].word)
        else:
            p_1 = morph.parse(list_of_words[local_counter]["word"])
        # Прверяем, является ли глаголом данное слово
        for i in p_1:
            if i.tag.POS == 'VERB':  # Если обнаружен глагол
                try:
                    if not "infn" in i.tag:  # Проверяем, что обнаруженный глагол не является инфенитивом
                        other_verb_exists = True
                        if self.__check_verb__(i, word):
                            return True, other_verb_exists
                except ValueError:
                    other_verb_exists = True
                    if self.__check_verb__(i, word):
                        return True, other_verb_exists
        return False, other_verb_exists

    def verb_or_adjf(self, counter, list_of_words):
        # Неоднаозначность глагол или прилагательное
        # Если это глагол то в предложении (или этой его части) или нет других галголов или, если они есть,
        # то имеют ту же форму, что и данный

        word = copy.deepcopy(list_of_words[counter])  # Создаём копию объекта слова из списка

        if not isinstance(list_of_words[counter], Word):  # Приводим слово к объекту класса Word
            word = Word(word=word["word"])

        p = morph.parse(word.word)  # Поучаем варианты морфологического разбора слова
        for n in range(2):
            if n == 0:
                local_counter = counter + 1
            else:
                local_counter = counter - 1
            while local_counter < len(list_of_words):  # Перебираем последующие слова из переданного списка
                if isinstance(list_of_words[local_counter], Word):
                    p_1 = morph.parse(list_of_words[local_counter].word)
                else:
                    p_1 = morph.parse(list_of_words[local_counter]["word"])
                # Прверяем, является ли глаголом данное слово из списка
                for i in p_1:
                    if i.tag.POS == 'VERB':  # Если встетился глагол
                        # Проверяем соответствие по чмслу и роду
                        if i.tag.number in [j.tag.number for j in p if i.tag.gender == j.tag.gender and j.tag.POS == "VERB"]:
                            return 'VERB'
                        else:
                            return 'ADJF'
                if n == 0:
                    local_counter += 1
                else:
                    local_counter -= 1

        # Если согласованного существительного не найдено, считаем слово существительным
        print()
        return 'VERB'


class WordLinkers:
    """
    Класс предоставляющий инструменты для нахождения и построениея связей между словами в синтаксический граф
    """

    def find_reference_phrase(self, words_objects, clusters, word_counter, current_cluster, groups_exist):
        """
        Поиск опорного словосочетания
        (Параметры передаются в функцию в виде ссылок и поэтому могут притерпевать изменения в ходе работы функции)
        :param words_objects: Список несгруппированных слов предложения
        :param clusters: Список кластеров слов
        :param word_counter: Счетсик слов в предложении
        :param current_cluster: Текущий кластер
        :param groups_exist: Признак наличия групп связанных слов в предложении
        :return:
        """

        groups_is_found = False # По-умолчанию группы связаннях слов не найдены
        while word_counter < len(
                words_objects) - 1:  # Перебираем список слов (в дальнейшем, слов не вошедщих ни в одну группу)
            # Берём каждый раз два соседних слова
            w_1 = words_objects[word_counter].word
            w_2 = words_objects[word_counter + 1].word
            # Проверяем наличие связи между словами и при этом получаем её тип
            if words_objects[word_counter].pos is not None and words_objects[word_counter + 1].pos is not None:
                is_linked, link_type = self.check_if_words_obj_linked(words_objects[word_counter],
                                                                      words_objects[word_counter + 1])
            else: # Запасной вариант, если слова не являются объектами класса Word TO DELETE
                is_linked, link_type = False, None

            if is_linked:
                # Метим слова, какое от какого зависит
                words_objects[word_counter].dependent_words.append((words_objects[word_counter + 1], link_type))
                words_objects[word_counter + 1].dependens_on.append((words_objects[word_counter], link_type))
                clusters.append(WordsCluster([words_objects[word_counter],
                                              words_objects[word_counter + 1]]))  # Добавляем найденную группу в список
                #current_cluster += 1
                # Удаляем найденные и сгруппированные слова из списка несгрупированных ещё слов (чтобы не путались дальше)
                words_objects.remove(words_objects[word_counter])
                words_objects.remove(words_objects[word_counter])
                groups_is_found = True
                current_cluster += 1
                break
            else:
                if words_objects[word_counter].pos is not None and words_objects[word_counter + 1].pos is not None:
                    is_linked, link_type = self.check_if_words_obj_linked(words_objects[word_counter + 1],
                                                                          words_objects[word_counter])
                else:
                    is_linked, link_type =  False, None
                if is_linked:  # Проверяем наличие связи, предполагая первое зависимым, а второе главным
                    # Метим слова, какое от какого зависит
                    words_objects[word_counter].dependens_on.append((words_objects[word_counter + 1], link_type))
                    words_objects[word_counter + 1].dependent_words.append((words_objects[word_counter], link_type))
                    clusters.append(WordsCluster([words_objects[word_counter], words_objects[
                        word_counter + 1]]))  # Добавляем найденную группу в список
                    #current_cluster += 1
                    # Удаляем найденные и сгруппированные слова из списка несгрупированных ещё слов (чтобы не путались дальше)
                    words_objects.remove(words_objects[word_counter])
                    words_objects.remove(words_objects[word_counter])
                    groups_is_found = True
                    current_cluster += 1
                    break
            word_counter += 1

        if not groups_is_found:  # Если при проходе всего предложения не нашлось ни одной пары связанных слов, что это уже не предложение, а набор
            # несвязанных слов, или оставшийся "хвост" из "неприкаянных" слов. Это является критерием выхода из цикла анализа предложения.
            groups_exist = False
        return (words_objects, clusters, groups_exist, word_counter)

    def group_expansion(self, back_word_counter, to_continue, groups_exist, clusters, current_cluster, words_objects, word_counter):
        """
        Расширение группы новыми совами
        :param back_word_counter: обратный счётчик слов
        :param to_continue: имеет ли смысл продолжать разбор
        :param groups_exist: признак существования групп
        :param clusters: список кластеров (групп) слов
        :param current_cluster: текущий кластер
        :param words_objects: список ещё не сгруппированных слов предложения
        :param word_counter: пряпой счётчик слов
        :return:
        """
        # Перебираем слова влево
        while back_word_counter >= 0 and to_continue and groups_exist:
            to_continue = False # Имеет ли смысл продолжать
            counter_in_cluster = 0 # Текущий кластер (группа слов)
            for i in clusters[current_cluster].words:  # Перибираем слова в формируемой (расширяемой) группе:
                if len(words_objects) > 0 and abs(back_word_counter) <= len(words_objects) - 1:
                    # Если слова в списке ещё имеются и мы не дошли до конца списка
                    w_1 = words_objects[back_word_counter].word # Получаем текстовую часть текущего слова из несгруппированных слов
                    w_2 = i.word # Получаем текстовую часть слова из слов, входящих в группу
                    # Проверяем на связанность слова из группы с ещё не сгрупированными словами
                    if i.pos is not None and words_objects[back_word_counter].pos is not None:
                        is_linked, link_type = self.check_if_words_obj_linked(words_objects[back_word_counter], i)
                    else:
                        is_linked, link_type =  False, None
                    if is_linked:  # Проверка на наличие связи, если первое главное, второе зависимое
                        # Если всязь имеется, метим слова, какое от какого зависит и дополняем группу новым словом
                        if len(clusters[current_cluster].words[counter_in_cluster].dependens_on) < 1:
                            words_objects[back_word_counter].dependent_words.append((i, link_type))
                            clusters[current_cluster].words[counter_in_cluster].dependens_on.append(
                                (words_objects[back_word_counter], link_type))
                            clusters[current_cluster].words.append(words_objects[back_word_counter])
                            words_objects.remove(words_objects[back_word_counter])  # Добавленное в группу слово удаляется
                                                                                    # из списка несгруппированных
                            word_counter -= 1
                            to_continue = True  # Если нашли зависисое слово, то есть смысл поискать их ещё
                        else:
                            is_linked = False
                    if not is_linked:
                        # Если связь не определена, пробуем поменять местами предполагаемые главное и зависимое слово и проверить ещё раз
                        # Проверка на наличие связи, если первое зависимое, второе  главное
                        if i.pos is not None and words_objects[back_word_counter].pos is not None:
                            is_linked, link_type = self.check_if_words_obj_linked(i, words_objects[back_word_counter])
                        else:
                            is_linked, link_type =  False, None
                        if is_linked: # Если наличие связи определено, метим эти связи
                            if len(words_objects[back_word_counter].dependens_on) < 1:
                                clusters[current_cluster].words[counter_in_cluster].dependent_words.append(
                                    (words_objects[back_word_counter], link_type))
                                words_objects[back_word_counter].dependens_on.append((i, link_type))
                                clusters[current_cluster].words.append(
                                    words_objects[back_word_counter])  # Добавление нового слова в группу
                                words_objects.remove(words_objects[
                                                         back_word_counter])  # Добавленное в группу слово удаляется из списка несгруппированных
                                word_counter -= 1
                                to_continue = True  # Если нашли зависисое слово, то есть смысл поискать их ещё
                counter_in_cluster += 1
            back_word_counter -= 1
        return (back_word_counter, to_continue, groups_exist, clusters, current_cluster, words_objects, word_counter)

    def collect_junk_words(self, words_objects, clusters):
        """
        Иногда бывает так, что после построения групп остаётся набор отдельных несвязанных слов
        Их можно попытаться подвязать к группам
        :param words_objects:
        :param clusters:
        :return:
        """
        if len(words_objects) > 0:  # Если после всего остались несгрупированные слова, собираем их в отдельную группу чисто механически
            extra_cluster = WordsCluster([])
            for i in words_objects:
                extra_cluster.words.append(i)
            # Пытаемся растыкать несгрупированные слова в группы (возможность связать далеко отстоящие слова)
            extra_words_counter = 0 # Счётчик по списку несгруппированных слов
            to_delete = [] # Слова, добавленные в группы, еоторые надо удалить из списка несгруппированных слов
            if len(clusters) > 0: # Добавлять слова в группы можно только в том случае, если эти группы имеются
                for i in extra_cluster.words: # Перебираем список несгруппированных слов
                    current_cluster = 0
                    for j in clusters: # Перебираем имеющиеся группы слов
                        inner_counter = 0
                        for k in j.words: # Перебираем слова из каждой из групп
                            w_1 = i.word
                            w_2 = k.word
                            if len(extra_cluster.words) - 1 >= abs(extra_words_counter):
                                # Если несгрупприованные слова ещё остались
                                # Проверяем возможность наличия связи между
                                # словом из несгруппированных и словом из группы
                                if i.pos is not None and k.pos is not None:
                                    is_linked, link_type = self.check_if_words_obj_linked(i, k)
                                else:
                                    is_linked, link_type =  False, None
                                if link_type == "gen" and k.preposition[0] != "" and (i.pos == "NOUN" or i.pos == "NPRO"):
                                    # Дополнения родительного падежа при этом не предполагается
                                    inner_counter += 1
                                    continue
                                if (k.pos == "NOUN" or k.pos == "NPRO") and (
                                        ('v_subj' in [lnk[1] for lnk in k.dependent_words]) or
                                            ('s_subj' in [lnk[1] for lnk in k.dependent_words])):
                                    # Возможность наличия в несгруппированных словах
                                                      # глагольных сказуемых не предполагается
                                    inner_counter += 1
                                    continue
                                if is_linked:  # Проверка на наличие связи, если первое главное, второе зависимое
                                    # Если всязь имеется, метим слова, какое от какого зависит и дополняем группу новым словом
                                    # В рамках данной концепции не допускаем у слова более одного от которого оно зависит
                                    # Это обеспечивает древовидную структуру и предотвращает установление ложных связей
                                    if (len(clusters[current_cluster].words[inner_counter].probably_dependens_on) < 1
                                        and len(clusters[current_cluster].words[inner_counter].dependens_on) < 1):
                                        extra_cluster.words[extra_words_counter].probably_dependent_words.append(
                                            (k, link_type))
                                        clusters[current_cluster].words[inner_counter].probably_dependens_on.append(
                                            (i, link_type))
                                        if extra_cluster.words[extra_words_counter] not in clusters[current_cluster].words:
                                            clusters[current_cluster].words.append(extra_cluster.words[extra_words_counter])
                                            to_delete.append(extra_cluster.words[extra_words_counter])
                                    else:
                                        is_linked = False
                                if not is_linked:
                                    # Проверяем на наличие связи поменяв обратно главное и зависимое
                                    if k.pos is not None and i.pos is not None:
                                        is_linked, link_type = self.check_if_words_obj_linked(k, i)
                                    else:
                                        is_linked, link_type =   False, None
                                    if link_type == "gen" and i.preposition[0] != "" and (k.pos == "NOUN" or k.pos == "NPRO"):
                                        is_linked = False
                                    if (i.pos == "NOUN" or i.pos == "NPRO") and (
                                                ('v_subj' in [lnk[1] for lnk in i.dependent_words]) or
                                                ('s_subj' in [lnk[1] for lnk in i.dependent_words])):
                                        is_linked = False

                                    if is_linked:  # Проверка на наличие связи, если первое зависимое, второе  главное
                                        # В рамках данной концепции не допускаем у слова более одного от которого оно зависит
                                        # Это обеспечивает древовидную структуру и предотвращает установление ложных связей
                                        if (len(extra_cluster.words[extra_words_counter].probably_dependens_on) < 1
                                            and len(extra_cluster.words[extra_words_counter].dependens_on) < 1):
                                            extra_cluster.words[extra_words_counter].probably_dependens_on.append(
                                                (k, link_type))
                                            clusters[current_cluster].words[inner_counter].probably_dependent_words.append(
                                                (i, link_type))
                                            if extra_cluster.words[extra_words_counter] not in clusters[current_cluster].words:
                                                clusters[current_cluster].words.append(extra_cluster.words[extra_words_counter])
                                                to_delete.append(extra_cluster.words[extra_words_counter])

                            inner_counter += 1
                        current_cluster += 1

                    extra_words_counter += 1
            for obj in to_delete: # Удалиляем из списка несгруппированных слов, те слова, которые были добавлены в группы
                if obj in extra_cluster.words:
                    extra_cluster.words.remove(obj)
            clusters.append(extra_cluster) # Всё равно несгруппированные слова добавляем как отдельную группу
        return (words_objects, clusters)

    def link_clusters(self, clusters):
        """
        Функция, пртающаяся укрупнить группы слов, находя связи между ними (точнее, между словами входящими в разные группы)
        :param clusters: список групп слов
        :return:
        """
        # Пытаемся установить связи между группами, ища наличие связей между словами из разных группп
        for cluster in clusters: # Перебираем группы слов
            for w_1 in cluster.words: # Перебираем слова в группе
                for cluster_2 in clusters: # Во вложенном цикле тоже перебираем группы
                    if cluster != cluster_2: # Связь слов группы с самими с собой искать смысла нет
                        for w_2 in cluster_2.words: # Перебираем слова из второй группы
                            # Проверяем пары слов на связанность
                            # При этом используем специальную функцию определения связи между гуппами
                            if w_1.pos is not None and w_2.pos is not None:
                                is_linked, link_type = self.check_transcluster_if_words_obj_linked(w_1, w_2)
                            else:
                                is_linked, link_type = False, None
                            # Если поределено наличие связи, прописываем эту связь
                            if is_linked:
                                # Связь прописываем только если у потенциально зависимого
                                # слова нет слов от которого оно зависит
                                if len(w_2.probably_dependens_on) == 0 and len(w_2.dependens_on) == 0:
                                    w_1.probably_dependent_words.append((w_2, link_type))
                                    w_2.probably_dependens_on.append((w_1, link_type))
                            else:
                                # Если всязь не определена, пробуем поределить связь
                                # поменяв местами проедполагаемые главное и зависимое слова
                                if w_1.pos is not None and w_2.pos is not None:
                                    is_linked, link_type = self.check_transcluster_if_words_obj_linked(w_2, w_1)
                                else:
                                    is_linked, link_type = False, None
                                # Если поределено наличие связи, прописываем эту связь
                                if is_linked:
                                    # Связь прописываем только если у потенциально зависимого слова
                                    # нет слов от которого оно зависит
                                    if len(w_1.probably_dependens_on) == 0 and len(w_1.dependens_on) == 0:
                                        w_2.probably_dependent_words.append((w_1, link_type))
                                        w_1.probably_dependens_on.append((w_2, link_type))
        return clusters

    def check_transcluster_if_words_obj_linked(self, main_word, dependent_word):
        """
        Функция для проверки наличия связи между словами
        Применяется для анализа спязей между кластерами.
        Не предполагает поиска связей определения и связей между существительными.
        Эти связи редко бывают далеко отстоящими и обычно оказываются внутри именных групп,
        которые определяются на предыдущем этапе.
        :param main_word:
        :param dependent_word:
        :return:
        """
        # Получаем варианты разбора и отставляем из них те, которые соотвестввуют определённым ранее частям речи
        p_1 = morph.parse(main_word.word) # Получаем варианты разбора главного слова
        p_main = p_1[0] # По умолчанию берём превый вариант разбора
        for i in p_1: # Выполняем перебор вариантов разбора
            if i.tag.POS == main_word.pos: # Если часть речи для некоторого варианта разбора соавадает
                                           # с частью речи объекта Word, переданного в поле main_word
                                           # выбираем этот вариант разбора
                p_main = i
                break
        p_2 = morph.parse(dependent_word.word) # Получаем варианты разбора зависимого слова
        p_dependent = p_2[0] # По умолчанию берём превый вариант разбора
        for i in p_2: # Выполняем перебор вариантов разбора
            if i.tag.POS == dependent_word.pos: # Если часть речи для некоторого варианта разбора соавадает
                                                # с частью речи объекта Word, переданного в поле dependent_word
                                                # выбираем этот вариант разбора
                p_dependent = i
                break
        if main_word.pos == "NOUN" or main_word.pos == "NPRO": # Главное слово - существительное или местоимение
            case_1 = p_main.tag.case # Определяем падеж главного слова
            if dependent_word.pos == "VERB": # Если зависисое слово - глагол
                if case_1 == "nomn": # Если существительное стоит в именительном падеже - связь есть (как подлежащие и сказуемое)
                    return (True, "v_subj")
            else:
                case_2 = p_dependent.tag.case
                if case_1 == "nomn" and case_2 == "nomn": # Вариант связи именного сказуемого
                    return (True, "n_subj")
        if main_word.pos == "VERB" or main_word.pos == "INFN": # Главное слово - глагол
            if dependent_word.pos == "NOUN" or dependent_word.pos == "NPRO": # Если зависисое слово - существительное или местоимение
                case = p_dependent.tag.case # Определяем падеж зависимого слова
                if case != "nomn":
                    # return (True, "sup")  # Дополнение
                    if case is not None:
                        return (True, "sup_" + case)
                    else:
                        return (True, "sup_accs")
            if dependent_word.pos == "ADVB" or dependent_word.pos == "PRED":
                return (True, "occ")  # Обстоятельство
            if dependent_word.pos == "ADJF":  # Если зависимое слово - прилагательное
                case = p_dependent.tag.case  # Определяем падеж этого прилагательного
                if case == 'ablt':  # Прилагательное должно быть в творительном падеже
                    return (True, "occ")
            if dependent_word.pos == "INFN":
                return (True, "verb_sup")  # Глагольное дополнение

            # Возможны и другие варианты связанных сочетаний, но их пока не рассматриваем

        return (False, None)

    def check_if_words_obj_linked(self, main_word, dependent_word):
        """
        Функция для проверки наличия связи между словами.
        Если связь предполагается, то возвращает (True, "предполагаемый тип саязи")
        :param main_word:
        :param dependent_word:
        :return:
        """

        # Получаем варианты морфологического разбора для главного (p_1) и зависимого слова (p_2)
        p_1 = morph.parse(main_word.word)
        p_2 = morph.parse(dependent_word.word)

        for p_main in p_1: # Перибираем варанты разбора главного слова
            for p_dependent in p_2: # Перибираем варанты разбора зависимого слова
                # Фильтруем только те варианы разбора, для которых части речи соответствуют
                # определённым ранее определённым значениям
                if ((p_dependent.tag.POS == dependent_word.pos and p_main.tag.POS == main_word.pos) or
                    ((p_dependent.tag.POS == "VERB" and dependent_word.pos == "INFN") and p_main.tag.POS == main_word.pos) or
                    (p_dependent.tag.POS == dependent_word.pos and (p_main.tag.POS == "VERB" and main_word.pos == "INFN"))):

                    if main_word.pos == "NOUN" or main_word.pos == "NPRO":  # Главное слово - существительное или личное местоимение
                        case_1 = p_main.tag.case  # Определяем падеж главного слова
                        if dependent_word.pos == "ADJF" or dependent_word.pos == "NUMR":  # Если зависисое слово - прилагательное
                            case_2 = p_dependent.tag.case  # Определяем падеж прилагательного (зависимого слова)
                            # возможные сочетания падежей: одинаковый падеж, или сочетание местного с дательным
                            # также необходимо согласование в роде (tag.gender) и числе .tag.number
                            if ((case_1 == case_2 or (case_1 == "loct" and case_2 == "datv") or (
                                            case_1 == "datv" and case_2 == "loct"))
                                and p_dependent.tag.gender == p_main.tag.gender
                                and ((p_dependent.tag.number == p_main.tag.number) or (
                                        p_main.tag.number == "sing" and p_dependent.tag.number == None))):  # Если падеж, род и число совпадают - саязь есть
                                return (True, "def")  # Связь определения
                        if dependent_word.pos == "NOUN" or main_word.pos == "NPRO":  # Если зависисое слово тоже существительное или личное местоимение
                            case_2 = p_dependent.tag.case  # Определяем падеж зависимого слова
                            # "gen" - связь дополнения родительного падежа
                            if case_2 == "gent" and case_1 == "loct":  # При сочетании родительного падежа с местным предполагаем связь
                                return (True, "gen")
                            # Варианты дополнеий родительного падежа
                            if case_1 == "nomn" and case_2 == "gent":
                                return (True, "gen")
                            if case_1 == "datv" and case_2 == "gent":
                                return (True, "gen")
                            if case_1 == "accs" and case_2 == "gent":
                                return (True, "gen")
                            if case_1 == "ablt" and case_2 == "gent":
                                return (True, "gen")
                            else:
                                # Вариант связи типа именного сказуемого
                                if case_1 == "nomn" and case_2 == "nomn":
                                    return (True, "n_subj")
                        if dependent_word.pos == "VERB":  # Если зависисое слово - глагол
                            if case_1 == "nomn":  # Если существительное стоит в именительном падеже - связь есть (как подлежащие и сказуемое)
                                                  # "v_subj" - связь глагольного сказуемого
                                return (True, "v_subj")
                    if main_word.pos == "VERB" or main_word.pos == "INFN": # Если главное слово - глагол
                        if dependent_word.pos == "NOUN" or dependent_word.pos == "NPRO": # Если зависимое слово - существительное
                            case = p_dependent.tag.case # Определяем падеж этого существительного
                            if case != "nomn": # Если падеж косвенный - то это дополнение
                                # return (True, "sup")  # Дополнение, шифруем как "sup"
                                if case is not None:
                                    return (True, "sup_" + case)  # Указываем падеж дополнения как тип связи
                                else:
                                    return (True, "sup_accs")
                        if ((dependent_word.pos == "ADVB" or dependent_word.pos == "COMP" or dependent_word.pos == "PRED")
                            or (dependent_word.pos == "PRCL" and 'ADVB' in [w.tag.POS for w in p_2])):
                            # Если зависимое слово наречие, компаратив, преликатив или может выступать как частица или наречие
                            return (True, "occ")  # Обстоятельство, шифрует как "occ"
                        if dependent_word.pos == "INFN": # Если зависимое слово инфинитив
                            return (True, "occ")
                        if dependent_word.pos == "ADJF": # Если зависимое слово - прилагательное
                            case = p_dependent.tag.case  # Определяем падеж этого прилагательного
                            if case == 'ablt': # Прилагательное должно быть в творительном падеже
                                return (True, "occ")
                        if dependent_word.pos == "VERB": # Другой вариант проверки зависимого слова на инфинитив
                            try:
                                if "infn" in p_dependent.tag:
                                    return (True, "occ")
                            except ValueError:
                                pass
                    if main_word.pos == "ADJF": # Если главное слово - прилагательное
                        # Зависимые слова можно считать связанными если они являются наречием, помпаративом или предикативом
                        if dependent_word.pos == "ADVB" or dependent_word.pos == "COMP" or dependent_word.pos == "PRED":
                            return (True, "occ")

                            # Возможны и другие варианты связанных сочетаний, но их пока не рассматриваем

        return (False, None)


class SentenceAnalyzer:
    """
    Класс, содержащий функции непосредственного анализа предложения
    """
    def __init__(self):
        self.current_sentance = ""
        self.current_structure = None
        self.ambiguity = AmbiguitySolvers()
        self.linker = WordLinkers()


    def find_name_groups_and_nous(self, list_of_words_obj, sent_number=0):
        '''
        Находит в предложении существитльные и варианты именных групп (в том числе и вложенные)
        :param list_of_words_obj: список слов
        :sent_number: номер предложения
        :return:
        '''

        out_records = [] # Список объектов, представляющих именные группы в удобном для дальнейшей обработке виде
        counter = 0

        out_obj_factory = OutRecordFactory() # Фабрика объектов именных групп

        while counter < len(list_of_words_obj): # Перебираем все слова из переданного списка (слова предложения)
            word = list_of_words_obj[counter] # Извлекаем объект слова
            name_group_exist = False # Индикатор существования именной группы
            current_name_group = NameGroup(word) # Создаём работчий объект именной группы инициальизированный найденным
                                                 # существительным
            if word.pos == "NOUN": # Именные группы всегда содержат существительное
                new_name_group = copy.deepcopy(current_name_group) # Оздаём копию объекта именной группы
                # Создаём на основе созданной именной группы объект именной группы для внешнего вывода
                new_record = out_obj_factory.get_new_out_record(name_group=copy.deepcopy(new_name_group))
                if new_record is not None:
                    new_record.sent_number = sent_number # Указваем номер предложения
                    out_records.append(new_record) # Добавляем объект в список (это объект из одного существительного)
                # Пробуем найти именные группы на основе данного существительного
                # Проверяем на связанность предыдущие слова
                local_counter = counter - 1
                while local_counter >= 0:
                    # Если слова являются связанными прилагательными или числительным, пытаемся присоединить их к именной группе
                    if list_of_words_obj[local_counter].pos == 'ADJF' or list_of_words_obj[local_counter].pos == 'NUMR':
                        # Проверяем перебираемые слова на связанность с потенциально главным в группе
                        is_linked, link_type = self.linker.check_if_words_obj_linked(word, list_of_words_obj[local_counter])
                        if is_linked: # Если связь обнаружена
                            # Прописываем связи между словами
                            word.dependent_words.append((list_of_words_obj[local_counter], link_type))
                            list_of_words_obj[local_counter].dependens_on.append((word, link_type))
                            # Записываем объект слова в скпиок слов именной группы (связи записываются вместе с ним)
                            current_name_group.inner_dependent.append((list_of_words_obj[local_counter], link_type))
                            if not name_group_exist:
                                # Если эта именная группа раньше не создавалась (новая) добавляем подменяем в списке слов
                                # рассматриваемое слово на именную группу
                                list_of_words_obj[counter] = current_name_group

                            new_name_group = copy.deepcopy(current_name_group) # Создаём гопию именной группы
                            for w in new_name_group.inner_dependent: # Перебираем зависимые слова именной группы
                                p_w = morph.parse(w[0].word) # Получаем варианты морфологического разбора слова
                                for form in p_w: # Анализирувем варианты разбора
                                    # Если этот вариант соответствует прилагательному или числительному
                                    if form.tag.POS == 'ADJF' or form.tag.POS == 'NUMR':
                                        w[0].word = form.inflect({'nomn'}).word # Ставим слово в именительный падеж,
                                                                                # так как основное слово группы
                                                                                # автоматически ставится
                                                                                # в именительный падеж
                                        break
                            # оздаём новый объект для хранения запими об именной группе
                            # (инициаллизируем его новой расширенной именной группе)
                            new_record = out_obj_factory.get_new_out_record(name_group=copy.deepcopy(new_name_group))
                            if new_record is not None: # Если новый объект успешно создан
                                new_record.sent_number = sent_number # Прописываем номер предложения
                                out_records.append(new_record) # Добавляем новую группу в список
                            # Удаляем добавленное в группу слово из общего списка
                            list_of_words_obj.remove(list_of_words_obj[local_counter])
                            name_group_exist = True # Указываем, что именная группа
                                                    # (именно группа, а не отдельное слово) существует
                            counter -= 1
                        else: # Если предыдущее слово оказалось не прилагательным, останавливаем перебор
                            break
                    elif ((list_of_words_obj[local_counter].pos == 'COMP' or
                          list_of_words_obj[local_counter].pos == 'ADVB' or
                          list_of_words_obj[local_counter].pos == 'PRED') and
                          name_group_exist): # Компаративы, наречия и предикативы тоже присоединяем к группе
                                             # (связи сторим от прилагательных и числительным)
                        # Если в именной группе обнаружено прилагательное или числительное
                        if current_name_group.inner_dependent[-1][0].pos == 'ADJF' or current_name_group.inner_dependent[-1][0].pos == 'NUMR':
                            test_adj = current_name_group.inner_dependent[-1][0] # Берём это прилагательное
                            # Пытаемся установить связь между словами
                            is_linked, link_type = self.linker.check_if_words_obj_linked(test_adj,
                                                                                  list_of_words_obj[local_counter])
                            if is_linked: # Если связь обнаружена
                                # рописываем связи
                                current_name_group.inner_dependent[-1][0].dependent_words.append((list_of_words_obj[local_counter], link_type))
                                list_of_words_obj[local_counter].dependens_on.append((test_adj, link_type))
                                # ДОбавляем слово в группу (вязи добавляются вместе со словом)
                                current_name_group.inner_dependent.append((test_adj, link_type))
                                # Удаляем слово из общего списка
                                list_of_words_obj.remove(list_of_words_obj[local_counter])

                                new_name_group = copy.deepcopy(current_name_group) # Создаём копию именной группы
                                # ПРиводим связанные с основным слова к именительному падежу
                                for w in new_name_group.main_word.dependens_on:
                                    p_w = morph.parse(w[0].word)
                                    for form in p_w:
                                        if form.tag.POS == 'ADJF' or form.tag.POS == 'NUMR':
                                            w[0].word = form.inflect({'nomn'}).word
                                            break
                                # Создаём новый объект, для хранения информации о группе
                                new_record = out_obj_factory.get_new_out_record(name_group=copy.deepcopy(new_name_group))
                                if new_record is not None: # Если объект создан
                                    new_record.sent_number = sent_number # ПРоставляем номер предложения
                                    out_records.append(new_record) # Добавляем объект в список
                                counter -= 1
                            else:
                                break
                    else:
                        break
                    local_counter -= 1

                # Продвигаемся вперёд
                # Если встерченное слово является связанным с главным словом - прлилагательное, присовокупливаем его
                # Как только встретили не прилагательное, прешращаем поиск зависимых от главного слова прилагательных
                # Иногда прилагательные идут после существительных
                local_counter = counter + 1
                while local_counter < len(list_of_words_obj): # Перебираем слова вперёд
                    # Интересуют только прилагательные или числительные
                    if list_of_words_obj[local_counter].pos == 'ADJF' or list_of_words_obj[local_counter].pos == 'NUMR':
                        # Проверяем наличие связи
                        is_linked, link_type = self.linker.check_if_words_obj_linked(word, list_of_words_obj[local_counter])
                        if is_linked: # Если связь установлена
                            # Прописываем связи в паре слов
                            word.dependent_words.append((list_of_words_obj[local_counter], link_type))
                            list_of_words_obj[local_counter].dependens_on.append((word, link_type))
                            # Добавляем слово к группе
                            current_name_group.inner_dependent.append((list_of_words_obj[local_counter], link_type))
                            if not name_group_exist:
                                list_of_words_obj[counter] = current_name_group
                            # Удаляем объект из общего списка
                            list_of_words_obj.remove(list_of_words_obj[local_counter])

                            new_name_group = copy.deepcopy(current_name_group) # Создаём копию объекта группы
                            # Связанные с главным словом прилагательные ставятся в именительный падеж
                            for w in new_name_group.main_word.dependens_on:
                                p_w = morph.parse(w.word)
                                for form in p_w:
                                    if form.tag.POS == 'ADJF' or form.tag.POS == 'NUMR':
                                        w.word = form.inflect({'nomn'}).word
                                        break
                            # Создаём новй объект хранящий информацию о группе инициализируем
                            # её текущеим состоянием именном группы
                            new_record = out_obj_factory.get_new_out_record(name_group=copy.deepcopy(new_name_group))
                            if new_record is not None:
                                new_record.sent_number = sent_number # Присваиваем объекту нопер предложения
                                out_records.append(new_record) # Добавляем объект в список

                            name_group_exist = True
                        else: # Наличие неспязанного прилагательного повод остановить поиск дальнейших связанных прилагательных
                            break
                    else:
                        break # Наличие слова, не являющегося прилагательным
                              # повод остановить поиск дальнейших связанных прилагательных
                    local_counter += 1

                # Прдвигаемся вперёд
                # Если слово является прилагательным в родительном падеже, двигаемя дальше
                # Если слово является существительным в родительном падеже, проверяем его на связанность
                local_counter = counter + 1
                local_agjs = []
                while local_counter < len(list_of_words_obj): # Перебираем список слов
                    if (list_of_words_obj[local_counter].pos == 'ADJF' or list_of_words_obj[local_counter].pos == 'NUMR' or
                        list_of_words_obj[local_counter].pos == 'COMP' or list_of_words_obj[local_counter].pos == 'ADVB' or
                        list_of_words_obj[local_counter].pos == 'PRED'):
                        local_agjs.append(list_of_words_obj[local_counter]) # Копим прилагательные в отдельном списке,
                                                                            # если встретим потом существительное,
                                                                            # попробуем их присоединить к нему
                    # Если слово является существительным или местоимением
                    elif list_of_words_obj[local_counter].pos == 'NOUN' or word.pos == "NPRO":
                        p = morph.parse(list_of_words_obj[local_counter].word) # Получаем варианты разбора
                        link_found = False # Признак того, что связь найдена
                        for i in p: # Перебираем варианты разбора
                            if i.tag.POS == 'NOUN': # Анализ выполняем для того аврианта разбора, который явялется существительным
                                # Создаём объекты для локальных мелких групп
                                local_name_group = NameGroup(copy.deepcopy(list_of_words_obj[local_counter]))

                                new_name_group = copy.deepcopy(local_name_group) # Создаём копию этойй именной группы
                                # Создаём объект, хранящий информацию об именной группе
                                new_record = out_obj_factory.get_new_out_record(name_group=copy.deepcopy(new_name_group))
                                if new_record is not None:
                                    new_record.sent_number = sent_number
                                    out_records.append(new_record)

                                if i.tag.case == "gent": # Если падеж существительного родительный
                                    # Проверяем наличие связи
                                    is_linked, link_type = self.linker.check_if_words_obj_linked(word, list_of_words_obj[
                                        local_counter])
                                    if is_linked: # Если связь между словами установлена
                                        link_found = True # Наличие связи подтверждено
                                        # Прописываем связи между парой слов
                                        word.dependent_words.append((list_of_words_obj[local_counter], link_type))
                                        list_of_words_obj[local_counter].dependens_on.append((word, link_type))
                                        # Добавляем слово к группе
                                        current_name_group.inner_dependent.append(
                                            (list_of_words_obj[local_counter], link_type))
                                        if not name_group_exist:
                                            list_of_words_obj[counter] = current_name_group

                                        new_name_group = copy.deepcopy(current_name_group) # Создаём копию объекта группы
                                        # Создаём объект, хранящий информацию об именной группе
                                        new_record = out_obj_factory.get_new_out_record(name_group=copy.deepcopy(new_name_group))
                                        if new_record is not None:
                                            new_record.sent_number = sent_number # Указываем номер предложения
                                            out_records.append(new_record) # Добавляем группу к списку

                                        name_group_exist = True
                                        for j in local_agjs: # Перебираем слова, сохранённые в списке прилагательных
                                            # ДОбавляем к именной группе связи с прилагательными из списка
                                            list_of_words_obj[local_counter].dependent_words.append((j, "def"))

                                            new_name_group = copy.deepcopy(current_name_group) # Создаём копию объекта группы
                                            # Создаём объект, хранящий информацию об именной группе
                                            new_record = out_obj_factory.get_new_out_record(name_group=copy.deepcopy(new_name_group))
                                            if new_record is not None:
                                                new_record.sent_number = sent_number # Указываем номер предложения
                                                out_records.append(new_record) # Добавляем группу к списку

                                        for j in local_agjs: # Перебираем список собранных прилагательных
                                            current_adj = copy.deepcopy(j) # Создаём копию прилагательного
                                            current_j_p = morph.parse(current_adj.word) # Получаем копию списка вариантов разбора
                                            for form in current_j_p: # Перебираем варианты разбора
                                                # Если вариант разбора соответствует прилагательным, числительным или компаративом,
                                                # считаем его подходящим
                                                if form.tag.POS == 'ADJF' or form.tag.POS == 'NUMR' or form.tag.POS == 'COMP':
                                                    current_adj.word = form.inflect({'nomn'}).word
                                                    local_name_group_2 = copy.deepcopy(local_name_group)
                                                    local_name_group_2.main_word.dependent_words.append((current_adj, "def"))
                                                    local_name_group_2.inner_dependent.append((current_adj, "def"))

                                                    new_record = out_obj_factory.get_new_out_record(name_group=copy.deepcopy(local_name_group_2))
                                                    if new_record is not None:
                                                        new_record.sent_number = sent_number
                                                        out_records.append(new_record)

                                                    break

                                        local_agjs = []
                                        # Удаляем слово из списка
                                        list_of_words_obj.remove(list_of_words_obj[local_counter])
                                        local_counter -= 1

                                        for j in local_agjs: # Удаляем список прилагательных из основноо списка
                                            if j in list_of_words_obj:
                                                list_of_words_obj.remove(j)
                                                local_counter -= 1
                                        break

                        if not link_found: # Если связь не установлена, перебор можно прикратить
                            break
                    else:
                        break
                    local_counter += 1
            counter += 1
        return out_records

    def define_pos_in_sentanse(self, list_of_words):
        """
        Определить, какими частями речи являются слова в предложении
        :param list_of_words:
        :return:
        """
        counter = 0
        for word in list_of_words: # Пребираем слова из списка
            p = morph.parse(word.word) # Получаем варианты морфодлогического разбора для каждого слова
            if len(p) > 1: # Если вариатов разбора больше чем 1
                # Составляем список того, какой частью речи божет быть данное слово
                pos = []
                for i in p:
                    if i.tag.POS not in pos: # Добавляем условное название части речи в список, тольо если таковой в нём нету
                        pos.append(i.tag.POS)
                if len(pos) > 1: # Если этот список состоит из более чем одного элемента, то исеет место неоднозначновть
                    # Решаем неоднозначности
                    if 'NOUN' in pos and 'ADJF' in pos:
                        word.pos = self.ambiguity.noun_or_adj(counter, list_of_words)
                    elif 'NOUN' in pos and 'VERB' in pos:
                        word.pos = self.ambiguity.noun_or_verb(counter, list_of_words)
                    elif 'NOUN' in pos and 'PREP' in pos:
                        word.pos = self.ambiguity.noun_or_prep(counter, list_of_words)
                    if 'NOUN' in pos and 'PRCL' in pos:
                        word.pos = self.ambiguity.noun_or_prcl(counter, list_of_words)
                    elif 'NOUN' in pos and 'NPRO' in pos:
                        word.pos = self.ambiguity.noun_or_npro(counter, list_of_words)
                    elif "VERB" in pos and "ADJF" in pos:
                        word.pos = self.ambiguity.verb_or_adjf(counter, list_of_words)
                    elif 'PRCL' in pos and 'CONJ' in pos:
                        if counter == 0:
                            word.pos = 'CONJ'
                        else:
                            word.pos = 'PRCL'
                    elif 'COMP' in pos and 'ADJF' in pos:
                        word.pos = 'ADJF'
                    elif 'CONJ' in pos and 'NPRO' in pos:
                        word.pos = 'CONJ'
                    elif "VERB" in pos and "INFN" in pos:
                        word.pos = "INFN"
                    elif "PRCL" in pos and "NPRO" in pos:
                        word.pos = "NPRO"
                    elif "NUMR" in pos:
                        word.pos = "NUMR"
                    elif "ADVB" in pos and "COMP" in pos:
                        word.pos = "ADVB"
                    elif "ADVB" in pos:
                        word.pos = "ADVB"

                else:
                    if pos[0] == "VERB":
                        try:
                            if "infn" in p[0].tag: # Инфинитив глагола может метиться по разному, поэтому такая проверка
                                word.pos = "INFN"
                            else:
                                word.pos = "VERB"
                        except ValueError:
                            word.pos = "VERB"
                    else:
                        word.pos = pos[0]
            else:
                if p[0].tag.POS == "VERB":
                    try:
                        if "infn" in p[0].tag:
                            word.pos = "INFN"
                        else:
                            word.pos = "VERB"
                    except ValueError:
                        word.pos = "VERB"
                else:
                    word.pos = p[0].tag.POS
            counter += 1

        return list_of_words

    def translate_pos(self, in_name):
        '''
        Функция, которая переводит термины названий частей речи из pymorphy в принятую в институте кибернетики систему
        :param in_name:
        :return:
        '''
        d = {
            "NOUN": "S1",
            "ADJF": "S2",
            "CONJ": "U",
            "PNCT": "98",
            "COMP": "S20",
            "PRED": "S19",
            "LATN": "S29",
            "NUMR": "S7",
            "NUMB": "S7",
            "intg": "S7",
            "real": "S7",
            "ROMN": "S7",
            "INTJ": "S21",
            "GRND": "S24",
            "PRCL": "S9",
            "NPRO": "S5",
            "PRTF": "S14",
            "PRTS": "S14",
            "VERB": "S4",
            "INFN": "S4",
            "PREP": "P",
            "UNKN": "99",
            "ADVB": "S16",
            "ADJS": "S17"
        }
        if in_name in d:
            return d[in_name]
        return "99"

    def define_spech(self, list_of_words):
        """
        Определить, какими частями речи являются слова в предложении согласно шифрованной классификации
        :param list_of_words:
        :return:
        """
        output_list = []
        counter = 0
        for word in list_of_words:
            p = morph.parse(word["word"])
            if len(p) > 1:
                pos = []
                for i in p:
                    if i.tag.POS not in pos:
                        pos.append(i.tag.POS)
                if len(pos) > 1:
                    # Решаем неоднозначности
                    if word["word"].lower() == "не":
                        output_list.append((word["word"].lower(), "S9", word['id']))
                    elif "anim" in p[0].tag and "NPRO" in pos:
                        output_list.append((word["word"].lower(), "S5", word['id']))
                    elif 'NOUN' in pos and 'ADJF' in pos:
                        current_pos = self.ambiguity.noun_or_adj(counter, list_of_words)
                        output_list.append((word["word"].lower(), self.translate_pos(current_pos), word['id']))
                    elif 'NOUN' in pos and 'VERB' in pos:
                        current_pos = self.ambiguity.noun_or_verb(counter, list_of_words)
                        output_list.append((word["word"].lower(), self.translate_pos(current_pos), word['id']))
                    elif 'NOUN' in pos and 'PREP' in pos:
                        current_pos = self.ambiguity.noun_or_prep(counter, list_of_words)
                        output_list.append((word["word"].lower(), self.translate_pos(current_pos), word['id']))
                    elif 'NOUN' in pos and 'NPRO' in pos:
                        current_pos = self.ambiguity.noun_or_npro(counter, list_of_words)
                        output_list.append((word["word"].lower(), self.translate_pos(current_pos), word['id']))
                    elif 'NOUN' in pos and 'PRCL' in pos:
                        current_pos = self.ambiguity.noun_or_prcl(counter, list_of_words)
                        output_list.append((word["word"].lower(), self.translate_pos(current_pos), word['id']))
                    elif 'PRCL' in pos and 'CONJ' in pos:
                        output_list.append((word["word"].lower(), "U", word['id']))
                    elif 'COMP' in pos and 'ADJF' in pos:
                        output_list.append((word["word"].lower(), "S20", word['id']))
                    elif 'CONJ' in pos and 'NPRO' in pos:
                        output_list.append((word["word"].lower(), "S11", word['id']))
                    elif "VERB" in pos and "INFN" in pos:
                        output_list.append((word["word"].lower(), "S4", word['id']))
                    elif "VERB" in pos and "ADJF" in pos:
                        output_list.append((word["word"].lower(), "S23", word['id']))
                    elif "NUMR" in pos:
                        output_list.append((word["word"].lower(), "S7", word['id']))
                    elif "ADVB" in pos and "COMP" in pos:
                        output_list.append((word["word"].lower(), "S20", word['id']))
                    elif "ADVB" in pos and 'NPRO' in pos:
                        output_list.append((word["word"].lower(), "S10", word['id']))
                    elif 'PREP' in pos and 'ADVB' in pos:
                        output_list.append((word["word"].lower(), "S16", word['id']))
                    elif "NPRO" in pos:
                        output_list.append((word["word"].lower(), "S12", word['id']))
                    else:
                        output_list.append((word["word"].lower(), self.translate_pos(pos[0]), word['id']))

                elif len(pos) == 1:
                    if word["word"].lower() == "не":
                        output_list.append((word["word"].lower(), "S9", word['id']))
                    elif p[0].tag.animacy is not None and pos[0] == "NPRO":
                        output_list.append((word["word"].lower(), "S5", word['id']))
                    else:
                        output_list.append((word["word"].lower(), self.translate_pos(pos[0]), word['id']))
                else:
                    output_list.append((word["word"].lower(), "99", word['id']))
            else:
                pos = p[0].tag.POS
                if pos is None:
                    pos = str(p[0].tag).split(",")[0]
                if word["word"].lower() == "не":
                    output_list.append((word["word"].lower(), "S9", word['id']))
                elif p[0].tag.animacy is not None and pos == "NPRO":
                    output_list.append((word["word"].lower(), "S5", word['id']))
                else:
                    output_list.append((word["word"].lower(), self.translate_pos(str(pos)), word['id']))
            counter += 1
        return output_list

    def make_obj_list(self, sentance):
        '''
        Делает из предложения список объектов Word
        При этом убирает знаки припинания и прикрепляет предлоги и отрицатлеьные к значащим словам
        :param sentance:
        :return:
        '''
        # Получаем список слов
        if isinstance(sentance, list):
            list_of_words = sentance # Если это спсок то просто копируем его
        elif isinstance(sentance, str): # Если это строка
            list_of_words = nltk.word_tokenize(sentance)  # Разбиваем предложение на слова и знаки
        else: # В другом случае имеет мето передача непредвиденного объекта. Формируем просто пустой список
            list_of_words = []

        words_objects = []  # Список слов, представленных как объекты

        counter = 0
        tmp = ["", 0]
        particle = ["", 0]
        # Уберём из списка слов "мусор" и сформируем список значащих слов как список объектов:
        list_of_words = self.remove_words_from_list(in_list=list_of_words, to_remove=[".", ",", ":", ";", "?", "!", "-"])

        for word in list_of_words: # Перебираем слова в спимке
            p = morph.parse(word['word']) # Получем варианты разбора слова
            is_prep = False # Слово является предлогом
            is_particle = False # Слово является частицей (отрицательной)
            # Проверяем, является ли слово предлогом
            if self.ambiguity.noun_or_prep(counter, [w['word'] for w in list_of_words]) == "PREP":
                is_prep = True

            # Проверяем, евляется ли слово отрицательной частицей "не" или "ні"
            if word['word'].lower() == "не" or word['word'].lower() == "ні":
                is_particle = True

            if not is_prep and not is_particle:  # Если слово не является предлогом, записываем его
                # Проверяем, что слово является существительным
                word_type_code = 0  # 1 - существительное или местоимение, 2 - прилагательное или наречие или числительное
                for i in p:
                    if i.tag.POS == "NOUN" or i.tag.POS == "NPRO":
                        word_type_code = 1
                        # Уточняем, не прилагательное ли это на самом деле
                        if self.ambiguity.noun_or_adj(counter, list_of_words) == "ADJF":
                            word_type_code = 2
                    elif (i.tag.POS == "ADJF" or i.tag.POS == "COMP" or i.tag.POS == "PRTF"
                          or i.tag.POS == "NUMR" or i.tag.POS == "ADVB" or i.tag.POS == "PRED"
                          or i.tag.POS == "PRCL"):
                        # Если слово - прилагательное, или числительное или компаратив или предикатив или частица
                        if counter < len(list_of_words) - 1:
                            # Получаем и проверяем следующее слово
                            next_word = morph.parse(list_of_words[counter + 1]['word'])
                            for j in next_word:
                                if (j.tag.POS == "NOUN" or j.tag.POS == "NPRO" or j.tag.POS == "ADJF"
                                    or i.tag.POS == "NUMR" or i.tag.POS == "ADVB" or i.tag.POS == "PRED"
                                    or i.tag.POS == "PRCL"):
                                    word_type_code = 2
                                    break
                            #(word_type_code)
                        if word_type_code != 2:
                            # Проверяем, не является ли слово всё-таки прилагательным проверяяя предидущие слова
                            if counter > 0:
                                prew_word = morph.parse(list_of_words[counter - 1]['word'])
                                for j in prew_word:
                                    if j.tag.POS == "NOUN" or j.tag.POS == "NPRO" or j.tag.POS == "ADJF":
                                        word_type_code = 2
                                        break
                        if word_type_code != 2:
                            word_type_code = 1
                        break
                    elif (i.tag.POS == "ADJS" or i.tag.POS == "VERB" or i.tag.POS == "INFN"
                          or i.tag.POS == "PRTS" or i.tag.POS == "GRND" or i.tag.POS == "INTJ"
                          or i.tag.POS == "PRCL"): # Прочие части речи шифруем как 3
                        word_type_code = 3
                        break
                    elif check_advb_by_fections(word['word']): # Подозрение о том, что слово прилагательное
                                                               # по характерному окончанию
                        if counter < len(list_of_words) - 1:
                            next_word = morph.parse(list_of_words[counter + 1]['word'])
                            # Анализируем какие есть варианты разбора для следующего слова
                            # Считаем, что прилагательные идут перед существительными, местоимениями или другими прилагателными.
                            for j in next_word:
                                if j.tag.POS == "NOUN" or j.tag.POS == "NPRO" or j.tag.POS == "ADJF":
                                    if j.tag.case == i.tag.case:
                                        word_type_code = 2
                                        break
                        if word_type_code != 2:
                            word_type_code = 1
                        break
                    else:
                        word_type_code = 0 # Слово неучттённого редкого типа

                if word_type_code == 1:
                    # Если это существительное, то привязываем к нему сохранённый ранее предлог (если таковой имеется есть)
                    # После этого сам сохранённый предлог обнуляем
                    if (Word(word=word['word'], preposition=tmp, particle=particle, id=word['id']) not in words_objects):
                        words_objects.append(Word(word=word['word'], preposition=tmp, particle=particle, id=word['id']))
                    tmp = ["", 0]  # Обнуляем запомненый предлог
                elif word_type_code == 2:
                    # К прилагательным приделываем отрицательные частицы (если таковая встречалась)
                    # Предлог храним, ожидая встретить существительое
                    if (Word(word=word['word'], particle=particle, id=word['id']) not in words_objects):
                        words_objects.append(Word(word=word['word'], particle=particle, id=word['id']))
                else:
                    # К прочим совам тоже можно приделать отрицательную частицу
                    if (Word(word=word['word'], particle=particle, id=word['id']) not in words_objects):
                        words_objects.append(Word(word=word['word'], particle=particle, id=word['id']))
                    #tmp = ["", 0]  # Обнуляем запомненый предлог
            elif is_prep:  # Если же это предлог, то запоминаем его, чтобы прикрепить к следующему слову
                tmp = [word['word'], word['id']]
            elif is_particle:
                particle = [word['word'], word['id']]
            counter += 1
        return words_objects

    def check_if_sentence_is_complex(self, sentance):
        """
        Проверка на то является ли предложение сложным
        Части предложения на письме отделяются запятой.
        В предложении должно быть более одной основы.
        :param sentance: список слов
        :return:
        """
        list_of_words = nltk.word_tokenize(sentance)  # Разбиваем предложение на слова и знаки
        counter = 1
        while counter <= len(list_of_words): # Переводим предложения в свисок словарей виде {"word": текст слова, "id": id-слова}
                                             # Идентификаторы нужны для нумерации слов даже почле удаления знаков
                                             # припинания, разбиения на части, удаления предлогов и т. п.
            list_of_words[counter-1] = {"word": list_of_words[counter-1], "id": counter}
            counter += 1
        # Предположим, что запятая всё же есть
        parts_of_sentance = [[]]
        counter = 0
        for i in list_of_words: # выполняем перебор слов и знаков припинания
            if i["word"] != "," and i["word"] != ";": # разделителями частей предложения могут выступать "," или ";"
                parts_of_sentance[counter].append(i) # собираем часть предложения до характерного знака припинания
            else:
                parts_of_sentance.append([])
                counter += 1
        # Запятыми разделяются не только дасти сложного предложения
        # Ищим части, в которыхе есть подлежащие и сказуемое
        indexes_of_subsentances = []
        counter = 0
        for i in parts_of_sentance: # Перебираем предролагаемые части предложения
            subject_found = False # Признак того, что найдено подлежащее
            predicate_found = False # Признак того, что найдено сказуемое
            for j in i: # Перебираем слова в каждой из частей
                options = morph.parse(j['word']) # Получаем варианты морфологического разбора слова
                for p in options:
                    if p.tag.POS == "NOUN" or p.tag.POS == "NPRO": # Полдежащим как правило выступает существительное или местоимение
                        if p.tag.case == "nomn": # Оно должно иметь именительный падеж
                            subject_found = True # Считаем, что подлежащие найдено
                            continue
                    if p.tag.POS == "VERB": # Наличие глагола - признак глагольного сказуемого
                        predicate_found = True
                    if subject_found:
                        # Признак именного сказуемого (отределяется только если найдено подлежащее)
                        if p.tag.POS == "NOUN" or p.tag.POS == "NPRO":
                            if p.tag.case == "nomn":
                                # При идентификации наличия именного сказуемого исключаем варианты однородных подлежащих
                                if i[counter - 1]['word'] != "і" and i[counter - 1]['word'] != "й" and i[counter - 1]['word'] != "та" and i[counter - 1]['word'] != ",":
                                    predicate_found = True
                                    break
            if subject_found and predicate_found:
                # Если найдена основа, метим данную часть
                indexes_of_subsentances.append(counter)

            counter += 1

        # Собираем части редложения
        output = []
        for i in indexes_of_subsentances:
            # обираем части предложения, в которых определены отдельные основы в список для выовда
            output.append(parts_of_sentance[i])

        for i in output:
            # Удаляем части имеющие основы из превоначального списка
            parts_of_sentance.remove(i)

        # Из оставшихся слов, если таковае имеются формируем отдельную чать
        if len(parts_of_sentance) > 0:
            output.append([])
            for i in parts_of_sentance:
                for j in i:
                    output[-1].append(j)

        return output

    def remove_words_from_list(self, in_list=[], to_remove=[]):
        '''
        Удаляет заданный набор слов из списка
        :param in_list: Исходный спимок слов
        :param to_remove: Список слов, которые нало удалить во всех вхождениях
        :return:
        '''

        counter = 0
        while counter < len(in_list):
            if in_list[counter]['word'] in to_remove:
                in_list.remove(in_list[counter])
                counter -= 1
            counter += 1

        return in_list

    def define_name_group(self, list_of_words_obj):
        '''
        Находит в предложении именные группы и формирует из них объект
        Данная функци собирает максимально полную именную группу без формирования полгрупп
        :param list_of_words_obj: Список слов (в виде обїектов класса Word)
        :return: Список слов, где некоторые из слов собраны в именные группы, ведущие себя аналогияно отдельным совам
        '''
        counter = 0

        for word in list_of_words_obj: # Перебираем все слова из списка
            name_group_exist = False # Идентификатор существоавания именной группы
            current_name_group = NameGroup(word) # Пытаемся создать именную группу на основе каждого из слов
            current_name_group.id = word.id # id именной группы соответствует (равен) id главного слова этой группы
            if word.pos == "NOUN" or word.pos == "NPRO": # Главным словом именной группы может быть только
                                                         # существительное или метоимение
                # Проверяем на связанность предыдущие слова
                # Если они являются связанными прилагательными, присовокупливаем их
                local_counter = counter - 1
                while local_counter >= 0: # Перебираем слова влево от заданного
                    # Если встретилось прилагательное или числительное
                    if list_of_words_obj[local_counter].pos == 'ADJF' or list_of_words_obj[local_counter].pos == 'NUMR':
                        # Проверяем наличие связи
                        is_linked, link_type = self.linker.check_if_words_obj_linked(word, list_of_words_obj[local_counter])
                        if is_linked: # Если связь установена
                            # Прописываем связи между словами
                            word.dependent_words.append((list_of_words_obj[local_counter], link_type))
                            list_of_words_obj[local_counter].dependens_on.append((word, link_type))
                            # Добавляем новое зависимое слово в именную группу
                            current_name_group.inner_dependent.append((list_of_words_obj[local_counter], link_type))
                            if not name_group_exist:
                                list_of_words_obj[counter] = current_name_group # Подставляем в список на место главного
                                                                                # слова именную группу
                            list_of_words_obj.remove(list_of_words_obj[local_counter]) # Удаляем зависимое слово из списка
                            name_group_exist = True # В этом случе именная группа существует
                            #local_counter -= 1
                            counter -= 1
                        else:
                            break
                    elif ((list_of_words_obj[local_counter].pos == 'COMP' or
                          list_of_words_obj[local_counter].pos == 'ADVB' or
                          list_of_words_obj[local_counter].pos == 'PRED') and
                          name_group_exist):
                        # Компаративы, наречия и редикативы пироединяются к прилагательным, входящих в именную группу
                        if current_name_group.inner_dependent[-1][0].pos == 'ADJF' or current_name_group.inner_dependent[-1][0].pos == 'NUMR':
                            # Эти части речи обычно не отстоят далеко от опредиляемых слов, поэтому проверяем соседние слова
                            test_adj = current_name_group.inner_dependent[-1][0]
                            # Проверяем наличие связи
                            is_linked, link_type = self.linker.check_if_words_obj_linked(test_adj,
                                                                                  list_of_words_obj[local_counter])
                            if is_linked: # Если наличие и тип связи установлены
                                # Прописываем эту связь
                                current_name_group.inner_dependent[-1][0].dependent_words.append((list_of_words_obj[local_counter], link_type))
                                list_of_words_obj[local_counter].dependens_on.append((test_adj, link_type))
                                # Добавляем данное слово в список слов именной группы
                                current_name_group.inner_dependent.append((test_adj, link_type))
                                # Удаляем добавленное слово из основного списка
                                list_of_words_obj.remove(list_of_words_obj[local_counter])
                                counter -= 1
                            else:
                                break
                    else:
                        # В случае обнаружения других частей речи прекращаем поиск связанных
                        # с главним словом группы прилагательных, стоящих слева
                        break
                    local_counter -= 1

                # Продвигаемся вперёд
                # Если встерченное слово является связанным с главным словом прлилагательным, присовокупливаем его
                # Как только встретили не прилагательное, прекращаем поиск зависимых от главного слова прилагательных
                local_counter = counter + 1
                while local_counter < len(list_of_words_obj): # Выполняем перебор слов вправо
                    # Слово должно быть прилагательным или числительным
                    if list_of_words_obj[local_counter].pos == 'ADJF' or list_of_words_obj[local_counter].pos == 'NUMR':
                        # роверяем наличие связи
                        is_linked, link_type = self.linker.check_if_words_obj_linked(word, list_of_words_obj[local_counter])
                        if is_linked: # Если связь установлено
                            # Связываем объекты соответствующих слов
                            word.dependent_words.append((list_of_words_obj[local_counter], link_type))
                            list_of_words_obj[local_counter].dependens_on.append((word, link_type))
                            # Добавляем слово в список слов именной группы
                            current_name_group.inner_dependent.append((list_of_words_obj[local_counter], link_type))
                            if not name_group_exist:
                                # Если существование данной именной группы показано только на данном этапе,
                                # заменяем в обшем списке главное слово этой именной группы на объект саой группы
                                # Его поведение аналогияно объекту класса Word
                                list_of_words_obj[counter] = current_name_group
                            # Удаляем добавленное слово из обзщего списка
                            list_of_words_obj.remove(list_of_words_obj[local_counter])
                            name_group_exist = True
                        else:
                            break
                    else:
                        # В случае обнаружения других частей речи прекращаем поиск связанных
                        # с главним словом группы прилагательных, стоящих справа
                        break
                    local_counter += 1
                # Прдвигаемся вперёд
                # Если слово является прилагательным в родительном падеже, двигаемся дальше
                # Если слово является существительным в родительном падеже, проверяем его на связанность
                local_counter = counter + 1
                local_agjs = []
                while local_counter < len(list_of_words_obj):
                    if (list_of_words_obj[local_counter].pos == 'ADJF' or list_of_words_obj[local_counter].pos == 'NUMR' or
                        list_of_words_obj[local_counter].pos == 'COMP' or list_of_words_obj[local_counter].pos == 'ADVB' or
                        list_of_words_obj[local_counter].pos == 'PRED'):
                        # Если слово является прилагательным, числительным, компаративом, наречием, или предикативом
                        # копим эти слоав в отдельном списке, пока не найдём существительное или местоимение
                        local_agjs.append(list_of_words_obj[local_counter])
                    elif list_of_words_obj[local_counter].pos == 'NOUN' or word.pos == "NPRO":
                        # Если обнаружили существительное или местоимение
                        p = morph.parse(list_of_words_obj[local_counter].word) # Получаем варианты морфологического разбора
                        link_found = False
                        for i in p: # Перебираем варианты разбора
                            # ас интересуют только те варианты, которые соответствуют ранее определённым частям речи,
                            # к которой относится данное слово
                            if i.tag.POS == 'NOUN' or word.pos == "NPRO":
                                if i.tag.case == "gent": # Нас инетерсуют только существительные в родительном падеже
                                    # Проверяем наличие связи между главнм словом группы и данныи существительным
                                    is_linked, link_type = self.linker.check_if_words_obj_linked(word, list_of_words_obj[
                                        local_counter])
                                    if is_linked:  # Если связь установлена
                                        link_found = True # Считаем, что именная группв существует
                                        # Прописываем связи между словаим
                                        word.dependent_words.append((list_of_words_obj[local_counter], link_type))
                                        list_of_words_obj[local_counter].dependens_on.append((word, link_type))
                                        # Вносим найденное слово в список именной группы
                                        current_name_group.inner_dependent.append(
                                            (list_of_words_obj[local_counter], link_type))
                                        if not name_group_exist:
                                            # Если имення группа определена только на этом этапе, подменяем в
                                            # основном списке главное слово этой группы на объект самой группы
                                            # Его поведение аналогияно объекту класса Word
                                            list_of_words_obj[counter] = current_name_group

                                        name_group_exist = True
                                        for j in local_agjs:
                                            # рисоединяем к найденному слову идущую перед ним цепочку прилагательных
                                            list_of_words_obj[local_counter].dependent_words.append((j, "def"))
                                            j.dependens_on.append((list_of_words_obj[local_counter], link_type))
                                        # Удаляем доьвленное существительное из основного списка
                                        list_of_words_obj.remove(list_of_words_obj[local_counter])
                                        local_counter -= 1
                                        # Удаляем присоединённые к добавленному существительному прилагательные
                                        # из основного списка
                                        for j in local_agjs:
                                            if j in list_of_words_obj:
                                                list_of_words_obj.remove(j)
                                                local_counter -= 1
                                        break
                        if not link_found:
                            break
                    else:
                        break
                    local_counter += 1

            counter += 1
        return list_of_words_obj

    def get_nouns_and_name_groups(self, sentance, sent_number):
        """
        Функция для анализа текста и построения графа связей между группами и отдельными словами в группах
        :param sentance: предложение
        :return:
        """
        self.current_sentance = sentance
        parts = self.check_if_sentence_is_complex(sentance) # Разбиение предложений на части для сложных предложений
        out = []
        for list_of_words in parts:
            # Для каждой из частей предложения выполняем преобразование её в список объекстов класса Word
            # о определяем для каждого солва, какой частью речи он является
            words_objects = self.define_pos_in_sentanse(self.make_obj_list(list_of_words))
            # Для каждой из частей выпролняем поиск именных групп и подгрупп
            # Полученные для каждой из частей списки именных групп объединяем
            # в один результирующий список для данного предложения
            if len(out) < 1:
                out = self.find_name_groups_and_nous(words_objects, sent_number=sent_number)
            else:
                out += self.find_name_groups_and_nous(words_objects, sent_number=sent_number)
        return out

    def get_subject_predicate_groups(self, sentance):
        """
        Получение групп полдежащих с их сказуемыми
        :param sentance:
        :param sent_number:
        :return:
        """
        self.current_sentance = sentance
        parts = self.check_if_sentence_is_complex(sentance)  # Разбиение предложений на части для сложных предложений
        out = []
        for list_of_words in parts:
            print(list_of_words)
            # Для каждой из частей предложения выполняем преобразование её в список объекстов класса Word
            # о определяем для каждого солва, какой частью речи он является
            words_objects = self.define_pos_in_sentanse(self.make_obj_list(list_of_words))
            # Для каждой из частей выпролняем поиск именных групп и подгрупп
            # Полученные для каждой из частей списки именных групп объединяем
            # в один результирующий список для данного предложения
            if len(out) < 1:
                out = self.find_subject_and_predicate(words_objects, list_of_words)
            else:
                out += self.find_subject_and_predicate(words_objects, list_of_words)
        return out

    def find_subject_and_predicate(self, list_of_words_obj, list_of_words):
        output = [{"subjects": [], "predicates": []}]
        dash_place = len(list_of_words)
        for i in list_of_words:
            if i['word'] == '-' or i['word'] == '—':
                dash_place = i['id']
                break
        was_dash = False
        counter = 0
        while counter < len(list_of_words_obj):
            # print(list_of_words_obj[counter].serialyze())
            if counter > 0:
                if list_of_words_obj[counter].id - list_of_words_obj[counter - 1].id > 1:
                    was_dash = True

            if list_of_words_obj[counter].pos == 'NOUN':
                p = morph.parse(list_of_words_obj[counter].word)
                for i in p:  # Перебираем варианты разбора
                    if i.tag.POS == 'NOUN':
                        if i.tag.case == 'nomn':
                            if not was_dash:
                                output[0]["subjects"].append(i.normal_form)
                            elif len(output[0]["subjects"]) == 0:
                                output[0]["subjects"].append(i.normal_form)
                            else:
                                output[0]["predicates"].append(i.normal_form)
                    if i.tag.POS == 'VERB':
                        output[0]["predicates"].append(i.normal_form)

            counter += 1

        return output


    def analize_sentance(self, sentance):
        """
        Функция для анализа текста и построения графа связей меджу группами и отдельными словами в группах
        :param sentance: предложение
        :return:
        """
        self.current_sentance = sentance
        parts = self.check_if_sentence_is_complex(sentance) # Разбиение предложений на части для сложных предложений
        structure = []
        for list_of_words in parts:
            clusters = []  # Спсок найденных групп слов
            cluster_links = []  # Список связей между группами слов
            words_objects = self.define_pos_in_sentanse(self.make_obj_list(list_of_words))
            words_objects = self.define_name_group(words_objects)
            groups_exist = True
            current_cluster = -1
            while len(words_objects) > 0 and groups_exist:
                # Ищим первое (опорное словосочетание). Это должны быть два соседних слова, имеющих связь.
                word_counter = 0
                words_objects, clusters, groups_exist, word_counter = self.linker.find_reference_phrase(words_objects, clusters, word_counter, current_cluster, groups_exist)
                # Расширяем найденную группу влево
                back_word_counter = word_counter - 1 # Новый счётчик цикла, который будет работать на уменьшение (движене влево по списку слов)
                to_continue = True # Есть ли смысл продолжать дальше
                back_word_counter, to_continue, groups_exist, clusters, current_cluster, words_objects, word_counter = self.linker.group_expansion(back_word_counter, to_continue, groups_exist, clusters, current_cluster,
                                    words_objects, word_counter)

            words_objects, clusters = self.linker.collect_junk_words(words_objects, clusters)

            # Пытаемся укрупнить (объединить группы)
            clusters = self.linker.link_clusters(clusters)
            structure.append((clusters, cluster_links))

        self.current_structure = structure # Сформированный граф хранится как поле калсса structure
        return structure

    def print_graph(self, struct=None):
        '''
        Выводит на консоль схему графа предложения
        :param struct:
        :return:
        '''
        if struct is None:
            struct = self.current_structure
        n = 1
        for clusters in struct:
            clusters = clusters[0]
            nodes = []
            # Собираем и выводим на консоль схему найденного синтаксического графа следующим образом:
            # для каждого слова выводим список слов, зависящих от него, и слов от которых оно зависит
            # Именные группы при такого рода выводе не разворачиваются (но они имею свою внутреннюю структуру)
            print("part ", n)
            for i in clusters:
                for j in i.words:
                    nodes.append((j.get_word(), j.get_word(), 1.0))
                    for k in j.dependent_words:
                        nodes.append((j.word, k[0].get_word(), 1.0))
                    for k in j.probably_dependent_words:
                        nodes.append((j.word, k[0].get_word(), 0.5))
                    print(j.get_word(), j.pos)
                    print("\tdependent words: ", [(k[0].get_word(), k[1]) for k in j.dependent_words])
                    print("\tdependens on:", [(k[0].get_word(), k[1])  for k in j.dependens_on])
                    print("\tprobably dependent words: ", [(k[0].get_word(), k[1]) for k in j.probably_dependent_words])
                    print("\tprobably dependens on:", [(k[0].get_word(), k[1]) for k in j.probably_dependens_on])
                    print()
            n += 1

    def serialyze(self, struct=None):
        '''
        Возвращает синтаксичкский граф предложения в формате JSON (в том числе и внутреннюю структуру именных групп)
        :param struct:
        :return:
        '''
        if struct is None:
            struct = self.current_structure
        output = []

        for clusters in struct:
            clusters = clusters[0]
            # Собираем и выводим на консоль схему найденного синтаксического графа следующим образом:
            # для каждого слова выводим список слов, зависящих от него, и слов от которых оно зависит
            for i in clusters:
                for j in i.words:
                    serialyzed_obj = j.serialyze()
                    if serialyzed_obj not in output:
                        output.append(j.serialyze())

        return output

    def graw_graph(self, struct=None, file_name=None):
        '''
        Визуализирует граф. Стрелки направлены от главных слов к зависимым.
        :param struct:
        :return:
        '''
        if struct is None:
            struct = self.current_structure
        nodes = []
        # Указываем для построения вершины графа и связи между ними
        for clusters in struct:
            clusters = clusters[0]
            for i in clusters:
                for j in i.words:
                    nodes.append((j.get_word(), j.get_word(), 1.0))
                    for k in j.dependent_words:
                        nodes.append((j.get_word(), k[0].get_word(), 1.0))
                    for k in j.probably_dependent_words:
                        nodes.append((j.get_word(), k[0].get_word(), 0.5))
        g = nx.DiGraph() # Объект графа
        g.add_weighted_edges_from(nodes) # Инициализируем объект графа списком верши и связей
        # Задаём характерисики отображения графа
        nx.draw_shell(g, with_labels=True,
            node_size=15,
            node_color='g',
            node_shape='.',
            font_size=10,
            font_color='r',
            font_family='monospace',
            font_weight='book',
            horizontalalignment='left',
            verticalalignment='center')

        plt.show() # тривовываем граф
        if file_name is not None:
            plt.savefig(file_name) # Сохраняем графическую схему графа в виде файла
        plt.close()

    def define_sentance_type(self, sentance):
        """
        Функция для определения типа предложения
        (типа высказывания по наличию в нём характерных слов
        Список этих слов-маркеров прдгружается из внешнего xml-файла marker_words.xml
        :param sentance:
        :return:
        """
        # Подгружаем список слов-маркеров
        e = xml.etree.ElementTree.parse('marker_words.xml').getroot()

        # Вопросительный знак в конце - признак поросительного предложения.
        is_question = False
        if sentance.strip()[-1] == "?":
            is_question = True

        # Убираем знаки препинания, чтобы не мешались
        if sentance[-1] == "." or sentance[-1] == "?" or sentance[-1] == "!":
            tmp_sent = " " + sentance.lower()
            tmp_sent = tmp_sent.replace(".", " ", -1)
            tmp_sent = tmp_sent.replace("?", " ", -1)
            tmp_sent = tmp_sent.replace("!", " ", -1)
        else:
            tmp_sent = " " + sentance.lower() + " "
        tmp_sent = tmp_sent.replace(",", "")
        types = {}
        for type_sentence in list(e):
            # Берём признаки либо для утвердительных, либо для вопросительных предложений
            if type_sentence.tag == "question" and not is_question:
                continue
            if type_sentence.tag == "statement" and is_question:
                continue
            # Проверяем наличие в предложении характерных слов
            # предложение может быть одновременно отнесено к нескольким типам
            for words_type in list(type_sentence):
                for word in words_type.findall('item'):
                    if word.text in tmp_sent:
                        if type_sentence.tag not in types:
                            types[type_sentence.tag] = [words_type.tag]
                        else:
                            if words_type.tag not in types[type_sentence.tag]:
                                types[type_sentence.tag].append(words_type.tag)
        return types