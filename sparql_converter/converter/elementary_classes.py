
import copy
try:
    from converter.foreign_libraries import morph
except:
    from foreign_libraries import morph

class WordsCluster:
    """
        Класс, представляющий группу связанных слов
    """
    def __init__(self, words):
        self.words = words  # Список слов (представляются классом Word)


class Word:
    """
        Класс, представляющий слово и его связи
    """
    def __init__(self, word="", preposition=["", 0], particle=["", 0], id=0):
        self.word = word # Само слово
        self.dependent_words = [] # Список зависимых от него слов (представляются классом Word)
        self.dependens_on = []  # Список слов, от которого завсит данное слово (представляются классом Word)
        self.probably_dependent_words = []  # Список вероятно зависимых от него слов (представляются классом Word)
        self.probably_dependens_on = []  # Список слов, от которого, вероятно, завсит данное слово (представляются классом Word)
        self.preposition = preposition  # Предлог, стоящий перед словом
        self.particle = particle
        self.pos = None
        self.id = id

    def get_word(self):
        # Возвращает слово вместе с его предлогом и отрицательной частицей (при их наличии) в иде строки
        return self.particle[0].strip() + " " + self.preposition[0].strip() + " " + self.word

    def serialyze(self):
        # Возвращает JSON с характеристиками слова, включая его ID и списки связанных с ним слов
        return {
            "word": self.word,
            "preposition": self.preposition,
            "particle": self.particle,
            "dependent_words": [(w[0].word, w[0].id, w[1]) for w in self.dependent_words],
            "probably_dependent_words": [(w[0].word, w[0].id, w[1]) for w in self.probably_dependent_words],
            "dependens_on": [(w[0].word, w[0].id, w[1]) for w in self.dependens_on],
            "probably_dependens_on": [(w[0].word, w[0].id, w[1]) for w in self.probably_dependens_on],
            "pos": self.pos,
            "id": self.id
        }


class NameGroup(Word):
    """
        Класс, представляющий именную группу
    """
    def __init__(self, main_word=Word()):
        Word.__init__(self, main_word.word, main_word.preposition, main_word.particle)
        self.main_word = main_word  # Главное слово
        self.pos = "NOUN"
        self.inner_dependent = []
        self.word = self.main_word.word

    def normalize(self):
        """
        Приводит слова именой группы к нормальному виду в возвращаемом объекте
        :return:
        """
        normalized_obj = copy.deepcopy(self) # Создаётся копия объекта
        # Убираются пробелы и приводятся к нижнему регистру предог и частицу при гравном сове группы
        normalized_obj.main_word.preposition[0] = normalized_obj.main_word.preposition[0].strip().lower()
        normalized_obj.main_word.particle[0] = normalized_obj.main_word.particle[0].strip().lower()

        # Убираются пробелы и приводятся к нижнему регистру слова, связанные с главным словом
        for w in normalized_obj.main_word.dependent_words:
            w[0].word = w[0].word.strip().lower()

        # Убираются пробелы и приводятся к нижнему регистру остальные слова из группы
        for w in normalized_obj.inner_dependent:
            w[0].word = w[0].word.strip().lower()

        p = morph.parse(normalized_obj.main_word.word) # Получаем варианты морфологического разбора главного слова
        for form in p:
            if form.tag.POS == "NOUN" or form.tag.POS == "NPRO":
                # Нас интересуем тот вариант, при котором главное слово - это существительное
                normalized_obj.main_word.word = form.inflect({"nomn"}).word # Ставим его в именитальеый падеж
                return normalized_obj
        return normalized_obj

    def normalized(self):
        '''
        Приводит группу к нормальному виду. Изменяет объект. Возвращает сам изменённый объект
        :return: normalized object
        '''
        # Приводим главное слово и его предлог к нижнему регистру
        self.main_word.preposition[0] = self.main_word.preposition[0].strip().lower()
        self.main_word.particle[0] = self.main_word.particle[0].strip().lower()

        # Приводим группу непосредственно зависящих от главного слов
        # к нижнему регистру и очищаем от крайних пробелов
        for w in self.main_word.dependent_words:
            w[0].word = w[0].word.strip().lower()

        # Приводим все внутриннее зависимые слова к нижнему регистру
        # и убираем крайние пробелы
        for w in self.inner_dependent:
            w[0].word = w[0].word.strip().lower()

        p = morph.parse(self.main_word.word) # Получаем варианты разбора главного слова
        to_continue = True
        i = 0
        for form in p: # Перебираем варианты разблоа
            if form.tag.POS == "NOUN": # Нас интересуют только вариаты разбора для являющиеся существительными
                try:
                    if len(self.main_word.dependent_words) == 0:
                        try:
                            self.main_word.word = form.normal_form
                        except:
                            self.main_word.word = form.inflect({"nomn"}).word
                    else:
                        self.main_word.word = form.inflect({"nomn"}).word
                except:
                    return None
                gender = form.tag.gender
                numb = form.tag.number
                for w in self.main_word.dependent_words:
                    p_w = morph.parse(w[0].word)
                    for form_2 in p_w:
                        if form_2.tag.POS == "ADJF" or form_2.tag.POS == "NUMR":
                            if numb != "plur":
                                try:
                                    w[0].word = form_2.inflect({'nomn', gender}).word
                                    to_continue = False
                                    break
                                except:
                                    return None
                            else:
                                try:
                                    w[0].word = form_2.inflect({'nomn', 'plur'}).word
                                    to_continue = False
                                    break
                                except:
                                  pass
                if not to_continue:
                    return self
            i += 1
        return self

    def get_word(self):
        """
        Выводит тексти именной группы в виде строки
        :return:
        """
        phrase = self.main_word.preposition[0].strip()
        phrase = phrase.strip()
        if self.main_word.preposition[0].strip() != "":
            phrase += " "
        phrase += self.main_word.particle[0].strip()
        phrase = phrase.strip()
        for w in self.main_word.dependent_words:
            if w[0].pos == "ADJF" or w[0].pos == "NUMR" or w[0].pos == "COMP" or w[0].pos == "ADVB" or w[0].pos == "PRED":
                for w_2 in w[0].dependent_words:
                    phrase += " " + w_2[0].word.strip()
                    phrase = phrase.strip()
                phrase += " " + w[0].word.strip()
                phrase = phrase.strip()
        phrase += " " + self.main_word.word.strip()
        phrase = phrase.strip()
        for w in self.inner_dependent:
            if w[0].pos == "NOUN":
                phrase += " " + w[0].preposition[0].strip()
                phrase = phrase.strip()
                for d_w in w[0].dependent_words:
                    if d_w[0].pos == "ADJF"  or d_w[0].pos == "NUMR" or d_w[0].pos == "COMP" or d_w[0].pos == "ADVB" or d_w[0].pos == "PRED":
                        phrase += " " + d_w[0].word.strip()
                        phrase = phrase.strip()
                phrase += " " + w[0].word.strip()
                phrase = phrase.strip()
        return phrase

    def get_clean_group(self):
        phrase = ""
        for w in self.main_word.dependent_words:
            if w[0].pos == "ADJF" or w[0].pos == "NUMR" or w[0].pos == "COMP" or w[0].pos == "ADVB" or w[0].pos == "PRED":
                for w_2 in w[0].dependent_words:
                    phrase += " " + w_2[0].word.strip()
                    phrase = phrase.strip()
                phrase += " " + w[0].word.strip()
                phrase = phrase.strip()
        phrase += " " + self.main_word.word.strip()
        phrase = phrase.strip()
        for w in self.inner_dependent:
            if w[0].pos == "NOUN":
                phrase += " " + w[0].preposition[0].strip()
                phrase = phrase.strip()
                for d_w in w[0].dependent_words:
                    if d_w[0].pos == "ADJF" or d_w[0].pos == "NUMR" or d_w[0].pos == "COMP" or d_w[0].pos == "ADVB" or \
                                    d_w[0].pos == "PRED":
                        phrase += " " + d_w[0].word.strip()
                        phrase = phrase.strip()
                phrase += " " + w[0].word.strip()
                phrase = phrase.strip()
        return phrase

    def get_words_as_obj(self):
        # Выводит список свлов группы в форме объектов
        w_list = []
        for w in self.main_word.dependent_words:
            if w[0].pos == "ADJF" or w[0].pos == "NUMR" or w[0].pos == "COMP" or w[0].pos == "ADVB" or w[0].pos == "PRED":
                for w_2 in w[0].dependent_words:
                    w_list.append(w_2[0])
                w_list.append(w[0])
        w_list.append(self.main_word)

        for w in self.inner_dependent:
            if w[0].pos == "NOUN":
                for d_w in w[0].dependent_words:
                    if d_w[0].pos == "ADJF" or d_w[0].pos == "NUMR" or d_w[0].pos == "COMP" or d_w[0].pos == "ADVB" or \
                                    d_w[0].pos == "PRED":
                        w_list.append(d_w[0])
                w_list.append(w[0])
        return w_list

    def serialyze(self):
        # Выводит характеристики группы и входящих в неё слов (всключа связи) в форме JSON
        obj_list = self.get_words_as_obj()
        output = {
                "id": self.id,
                "words": [],
                "group_self_characteristics": {
                "main_word": self.main_word.word,
                "dependent_words": [(w[0].word, w[0].id, w[1]) for w in self.dependent_words],
                "probably_dependent_words": [(w[0].word, w[0].id, w[1]) for w in self.probably_dependent_words],
                "dependens_on": [(w[0].word, w[0].id, w[1]) for w in self.dependens_on],
                "probably_dependens_on": [(w[0].word, w[0].id, w[1]) for w in self.probably_dependens_on],
                "pos": self.pos,
                "id": self.id
            }
        }
        counter = 0
        for obj in obj_list:
            serialyzed_word = obj.serialyze()
            output["words"].append(serialyzed_word)
            if serialyzed_word["word"] == self.main_word.word and self.id == serialyzed_word["id"]:
                output["words"][counter]["dependent_words"] = output["group_self_characteristics"]["dependent_words"]
                output["words"][counter]["probably_dependent_words"] = output["group_self_characteristics"]["probably_dependent_words"]
                output["words"][counter]["dependens_on"] = output["group_self_characteristics"]["dependens_on"]
                output["words"][counter]["probably_dependens_on"] = output["group_self_characteristics"]["probably_dependens_on"]
            counter += 1

        return output

class OutRecordFactory:
    """
    Класс для производства объектов класса OutRecord на основе объектов класса NameGroup
    """
    def get_new_out_record(self, name_group):
        if isinstance(name_group, NameGroup):
            if name_group.normalized() is not None:
                return OutRecord(name_group)
        return None

class OutRecord:
    """
    Класс, хранящий информацию об именной группе в удобной для вывода в файл форме.
    """
    def __init__(self, name_group):
        self.ttype = "" # Части речи через _
        self.name_group = name_group.normalized() # Объект именной группы
        try:
            self.wcount = len(self.name_group.get_words_as_obj()) # Количество слов в группе

            # Получаем список слов как объектов и пребираем их
            for word in self.name_group.get_words_as_obj():
                # Группы построены так, что в них есть только существительные и прилагательные
                # На основании данных о частях речи для каждого из слов, входящих в группу формируем поле ttype
                if word.pos == "NOUN":
                    self.ttype += "noun_"
                else:
                    self.ttype += "adj_"

            self.ttype = self.ttype.strip("_").title() # Убираем крайние символы "_"
            self.tname = name_group.get_clean_group().strip() # Получаем список слов группы, разделённый пробелами
                                                          # (крайние пробелы убираем)
        except (AttributeError):
            self.wcount = 0
            self.tname = ""
        self.__sentpos__ = [] # Список пар номер предложения (от 0) / номер слова в предложении (от 1).
                              # Список, так как слово сожет встречаться несколько раз.
        self.sent_number = 0  # Номер предложения
        self.reldown = []
        self.relup = []


    def sentpos(self):
        '''
        Формирует список пар номер предложения (от 0) / номер слова в предложении (от 1), если он ещё не сформирован
        и возвращает его
        :return:
        '''
        if len(self.__sentpos__) < 1:
            for word in self.name_group.get_words_as_obj(): # Перебираем все слова, входящие в группу,
                                                            # представленные как объекты калсса Word
                self.__sentpos__.append((self.sent_number, word.id)) # Добавляем в выходной список пару
                                                                     # номер предложения / номер слова в предложении
        return self.__sentpos__

    def add_sentpos(self, sentpos):
        '''
        Функция для дополнения писка __sentpos__ новыми элементами
        :param sentpos:
        :return:
        '''
        if isinstance(sentpos, tuple):
            if len(sentpos) == 2:
                if sentpos not in self.__sentpos__:
                    self.__sentpos__.append(sentpos)


class OntoClass:
    def __init__(self, id="Thing", patent_class_id="", interactions=None, union=None, label="", language="uk"):
        if union is None:
            union = []
        if interactions is None:
            interactions = []
        self.id = id.strip()
        self.patent_class_id = patent_class_id.strip()
        self.interactions = interactions
        self.union = union
        self.label = label.strip()
        self.language = language.strip()

    def serialize(self):
        if self.patent_class_id.strip() == "" and len(self.interactions) == 0 and len(self.union) == 0 and self.label.strip() == "" and self.language.strip() == "":
            return '\t<owl:Class rdf:ID="' + self.id.strip() + '"/>\n'

        owl_text = '\t<owl:Class rdf:ID="' + self.id.strip() + '">\n'
        if self.patent_class_id.strip() != "":
            owl_text += '\t\t<rdfs:subClassOf rdf:resource="#' + self.patent_class_id.strip() + '"/>\n'
        if len(self.interactions) > 1:
            owl_text += '\t\t<owl:intersectionOf rdf:parseType="Collection">\n'
            for item in self.interactions:
                owl_text += '\t\t\t<owl:Class rdf:about="#' + item.strip() + '"/>\n'
            owl_text += '\t\t</owl:intersectionOf>\n'
        if len(self.union) > 1:
            owl_text += '\t\t<owl:unionOf rdf:parseType="Collection">\n'
            for item in self.union:
                owl_text += '\t\t\t<owl:Class rdf:about="#' + item.strip() + '"/>\n'
            owl_text += '\t\t</owl:unionOf>\n'
        if self.label.strip() != "":
            owl_text += '\t\t<rdfs:label xml:lang="' + self.language.strip() + '">' + self.label.strip() + '</rdfs:label>\n'
        else:
            owl_text += '\t\t<rdfs:label xml:lang="' + self.language.strip() + '">' + self.id.strip() + '</rdfs:label>\n'
        owl_text += '\t</owl:Class>\n'
        return owl_text


class OntoProperty:
    def __init__(self, id="", domain_id="", range_id="Thing", parent_id="", label="", language="uk"):
        self.id = id
        self.domain_id = domain_id
        self.range_id = range_id
        self.parent_id = parent_id
        self.label = label
        self.language = language

    def serialize(self):
        owl_text = '\t<owl:ObjectProperty rdf:ID="' + self.id.strip() + '">\n'
        if self.parent_id.strip() != "":
            owl_text += '\t\t<rdfs:subPropertyOf rdf:resource="#' + self.parent_id.strip() + '"/>\n'
        if self.domain_id.strip() != "":
            owl_text += '\t\t<rdfs:domain rdf:resource="#' + self.domain_id.strip() + '"/>\n'
        owl_text += '\t\t<rdfs:range rdf:resource="#' +  self.range_id.strip() + '"/>\n'
        owl_text += '\t\t<rdfs:label xml:lang="' + self.language.strip() + '">' + self.label.strip() + '</rdfs:label>\n'
        owl_text +=  '\t</owl:ObjectProperty>\n'
        return owl_text









