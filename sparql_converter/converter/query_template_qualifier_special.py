# -*- coding: utf-8 -*-

import xml.etree.ElementTree as Et
import traceback
import json
import time
import copy

# Генераторы файлов со списками слов из онтологии и дерева
from keywords_generators import get_ontology_entities, get_tree_entities, get_keywords

# Объект морфологического анализатора из pymorphy2 (создаётся однократно, так как крупный)
# В данном случае инициализация для украинского языка (для русского: lang='ru')
from foreign_libraries import morph

# morph = pymorphy2.MorphAnalyzer(lang='uk')

# Создать на основе используемой онтологии файл, содеражщий все понятия из назваий вершин
get_ontology_entities.execute("ontology.owl", morph)
# Создать файл, содеращий все понятия (слова), находящиеся в условиях перехода дерева принятия решений
get_tree_entities.execute(morph)
# Создать файл, содержащий словарь соответствия названий вершин онтологии и входящих в них отдельных слов
# с предварительной разметкой по частям речи
get_keywords.execute("ontology.owl", morph)
# Освободить память от подгруженных модулей, которые далее не потребуются
del get_ontology_entities
del get_tree_entities
del get_keywords

keywords = dict()
ontology_entities = list()
tree_entities = list()
abbreviations_dict = dict()

# Считать файлы со списками слов
with open('keywords.json', 'r', encoding='utf-8') as keywords_file:
    keywords = json.loads(keywords_file.read())

with open('ontology_entities.json', 'r', encoding='utf-8') as ontology_entities_file:
    ontology_entities = json.loads(ontology_entities_file.read())

with open('tree_entities.json', 'r', encoding='utf-8') as tree_entities_file:
    tree_entities = json.loads(tree_entities_file.read())

# Считать словарь аббревиатур (предварительно создаётся вручную)
with open('abbreviations_dict.json', 'r', encoding='utf-8') as abbreviations_dict_file:
    abbreviations_dict = json.loads(abbreviations_dict_file.read())


class QualifierConfig:
    __instance = None

    def __init__(self):
        if not QualifierConfig.__instance:
            self.tree = []
            self.specific_words_beginning = []
            self.specific_words_everywhere = []
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="tree.xml"):
        if not cls.__instance:
            cls.__instance = QualifierConfig()
            cls.__instance.config_file = config_file
            with open(config_file, 'r', encoding='utf-8') as xml_file:
                xml_file_data = xml_file.read()
                tree = Et.ElementTree(Et.fromstring(xml_file_data.encode('utf-8').decode('utf-8')))

            root = tree.getroot()

            for i in root:
                if i.tag == "tree":
                    for level in i:
                        if level.tag == "condition_level":
                            new_level = {"id": level.attrib.get("id"),
                                         "positions": dict()}
                            for position in level:
                                if position.tag == "position":
                                    new_position = {"id": position.attrib.get("id"),
                                                    "conditions": dict()}
                                    for condition in position:
                                        if condition.tag == "condition" or "default":
                                            if condition.tag == "condition":
                                                new_condition_id = condition.attrib.get("id")
                                                new_condition = {"id": new_condition_id}
                                            else:
                                                new_condition_id = position.attrib.get("id") + "_default"
                                                new_condition = {"id": new_condition_id}
                                            for tag in condition:
                                                if tag.tag == "words_list":
                                                    new_words_list = []
                                                    for wd in tag:
                                                        if wd is not None and wd.text is not None:
                                                            new_words_list.append(wd.text.strip())
                                                    new_condition["words_list"] = new_words_list
                                                if tag.tag == "next_position" and tag.text is not None:
                                                    new_condition["next_position"] = tag.text
                                                if tag.tag == "result":
                                                    new_result = dict()
                                                    for res in tag:
                                                        if res.tag == "query_type":
                                                            if res.text is not None:
                                                                if new_result.get("query_type") is None:
                                                                    new_result["query_type"] = [res.text.strip()]
                                                                else:
                                                                    new_result["query_type"].append(res.text.strip())
                                                        if res.tag == "input_entity":
                                                            if "input_entity" not in new_result:
                                                                if res.text is not None:
                                                                    new_result["input_entity"] = [res.text.strip()]
                                                            else:
                                                                if res.text is not None:
                                                                    new_result["input_entity"].append(res.text.strip())
                                                    if tag.text is not None:
                                                        new_result["value"] = tag.text.strip()
                                                    new_condition["result"] = new_result
                                            new_position["conditions"][new_condition_id] = new_condition
                                    new_level["positions"][position.attrib.get("id")] = new_position
                            cls.__instance.tree.append(new_level)
                if i.tag == "specific_words":
                    for j in i:
                        if j.tag == "beginning":
                            for item in j:
                                cls.__instance.specific_words_beginning.append(item.text)
                        if j.tag == "everywhere":
                            for item in j:
                                cls.__instance.specific_words_everywhere.append(item.text)
        # print(cls.__instance.tree)
        return cls.__instance


def find_ontology_entity(word_list, chapters="all"):
    if isinstance(chapters, str):
        if chapters.lower().strip == "all":
            chapters = ["class_names_dict", "individual_names_dict", "pradicates"]
        elif chapters.lower().strip in ["class_names_dict", "individual_names_dict", "pradicates"]:
            chapters = [chapters]
        else:
            chapters = ["class_names_dict", "individual_names_dict", "pradicates"]
    elif isinstance(chapters, list) or isinstance(chapters, set):
        chapters = chapters
    else:
        chapters = ["class_names_dict", "individual_names_dict", "pradicates"]
    max_metric = -1.0
    if isinstance(word_list, list) or isinstance(word_list, set) or isinstance(word_list, tuple):
        output = " ".join(word_list)
    elif isinstance(word_list, str):
        output = word_list
    else:
        return "", -1.0

    word_list_pool = [copy.deepcopy(word_list)]

    # print("word_list burum-burum ", word_list)

    for key in abbreviations_dict:
        word_str = " ".join(copy.deepcopy(word_list)).strip().lower()
        if (key.strip().lower() + " " in word_str or " " + key.strip().lower() in word_str or key.strip().lower() == word_str):
            word_list_pool.append(word_str.replace(key.strip().lower(), abbreviations_dict[key].strip().lower()).split())

    firts_time = True
    # print("word_list_pool ", word_list_pool)
    for current_word_list in word_list_pool:
        # print(current_word_list)
        for chapter in chapters:
            if chapter in keywords:
                for entity in keywords[chapter]:
                    nouns_match = 0
                    adj_match = 0
                    verb_match = 0
                    other_match = 0
                    nouns_extra = 0
                    adj_extra = 0
                    verb_extra = 0
                    other_extra = 0
                    not_found_words = set()
                    nouns_not_found = 0
                    adj_not_found = 0
                    verb_not_found = 0
                    other_not_found = 0

                    total_words = len(current_word_list)
                    total_entity_words = len(keywords[chapter][entity]["words"])

                    total_words_weighed_1 = 0.0
                    total_words_weighed_2 = 0.0
                    total_entity_words_weighed_1 = 0.0
                    total_entity_words_weighed_2 = 0.0

                    for word in current_word_list:
                        # print("word ", word)
                        input_word_found = False
                        p = morph.parse(word)
                        for cnt, form in enumerate(p):
                            # print(form.normal_form)
                            if cnt == 0:
                                if form.tag.POS is None:
                                    total_words_weighed_1 += 0.43
                                    total_words_weighed_2 += 0.44
                                elif form.tag.POS == "NOUN":
                                    total_words_weighed_1 += 0.43
                                    total_words_weighed_2 += 0.44
                                elif form.tag.POS == "ADJF":
                                    total_words_weighed_1 += 0.26
                                    total_words_weighed_2 += 0.22
                                elif form.tag.POS == "VERB":
                                    total_words_weighed_1 += 0.18
                                    total_words_weighed_2 += 0.22
                                else:
                                    total_words_weighed_1 += 0.13
                                    total_words_weighed_2 += 0.12
                            for word_2 in keywords[chapter][entity]["words"]:
                                entity_word_found = False
                                entity_word_found_factor = 1.0
                                if cnt == 0:
                                    if word_2["POS"] is None:
                                        total_entity_words_weighed_1 += 0.43
                                        total_entity_words_weighed_2 += 0.5
                                    if word_2["POS"] == "NOUN" or word_2["POS"] == None:
                                        total_entity_words_weighed_1 += 0.43
                                        total_entity_words_weighed_2 += 0.5
                                    elif word_2["POS"] == "ADJF":
                                        total_entity_words_weighed_1 += 0.26
                                        total_entity_words_weighed_2 += 0.25
                                    elif word_2["POS"] == "VERB":
                                        total_entity_words_weighed_1 += 0.18
                                        total_entity_words_weighed_2 += 0.13
                                    else:
                                        total_entity_words_weighed_1 += 0.13
                                        total_entity_words_weighed_2 += 0.12

                                    for word_3 in current_word_list:
                                        p_2 = morph.parse(word_3)

                                        for form_2 in p_2:
                                            # if form_2.normal_form == word_2["text"]:
                                            #     print(form_2.normal_form, word_2["text"], not_found_words)
                                            #     print(form_2.tag.POS, word_2["POS"])
                                            if form_2.normal_form in not_found_words:
                                                entity_word_found = False
                                                break
                                            if form_2.normal_form == word_2["text"] and form_2.tag.POS == word_2["POS"]:
                                                # print("burum-burum ")
                                                entity_word_found = True
                                                break
                                        if entity_word_found:
                                            # Если установлено, что слово из базы есть во фразе мользователя, дальше
                                            # перебирать слова из фразы пользователя нет смысла
                                            break
                                    if not entity_word_found and word_2["text"] not in not_found_words:
                                        not_found_words.add(word_2["text"])
                                        if word_2["POS"] == "NOUN" or word_2["POS"] == None:
                                            nouns_not_found += 1.0
                                        elif word_2["POS"] == "ADJF":
                                            adj_not_found += 1.0
                                        elif word_2["POS"] == "VERB":
                                            verb_not_found += 1.0
                                        else:
                                            other_not_found += 1.0

                                normal_forms = [frm.normal_form for frm in p]
                                pos_list = [frm.tag.POS for frm in p]
                                # if entity_word_found:
                                #     print("normal_forms, pos_list", normal_forms, pos_list)
                                # if entity_word_found and form.normal_form == word_2["text"] and form.tag.POS == word_2["POS"]:
                                # if entity_word_found and word_2["text"] in normal_forms and word_2["POS"] in pos_list:
                                if entity_word_found and word_2["text"] in normal_forms and word_2["POS"] in pos_list:
                                    input_word_found = True
                                    if word_2["POS"] == "NOUN" or word_2["POS"] == None:
                                        nouns_match += 1.0
                                    elif word_2["POS"] == "ADJF":
                                        adj_match += 1.0
                                    elif word_2["POS"] == "VERB":
                                        verb_match += 1.0
                                    else:
                                        other_match += 1.0
                                    break

                            if not input_word_found:
                                current_pos = p[0].tag.POS
                                if current_pos == "NOUN" or word_2["POS"] == None:
                                    nouns_extra += 1
                                elif current_pos == "ADJF":
                                    adj_extra += 1
                                elif current_pos == "VERB":
                                    verb_extra += 1
                                else:
                                    other_extra += 1
                                break


                    current_metric = (2.0 * float((0.43 * nouns_match + 0.26 * adj_match + 0.18 * verb_match
                                                   + 0.13 * other_match) / (total_words_weighed_1 + total_entity_words_weighed_1)) +
                                      0.5 * float((-0.44 * nouns_extra - 0.22 * adj_extra - 0.22 * verb_extra
                                                   - 0.12 * other_extra) / total_words_weighed_2) +
                                      0.5 * float((-0.5 * nouns_not_found - 0.25 * adj_not_found - 0.13 * verb_not_found
                                                   - 0.12 * other_not_found) / total_entity_words_weighed_2))

                    if entity == "Біла_Книга_з_Фізичної_та_Реабілітаційної_Медицини__lbraket_ФРM_rbraket__в_Європі":
                        print(current_word_list)
                        print(keywords[chapter][entity]["words"])
                        print("not found ", nouns_not_found, adj_not_found, verb_not_found, other_not_found)
                        print("extra ", nouns_extra, adj_extra, verb_extra, other_extra)
                        print("match ", nouns_match, adj_match, verb_match, other_match)
                        print(nouns_not_found, adj_not_found, verb_not_found, other_not_found)
                        print(current_metric)
                    '''
                    if word == 'реабілітація':
                        print(keywords[chapter][entity]["words"])
                        print(word_2)
                        print("not found ", nouns_not_found, adj_not_found, verb_not_found, other_not_found)
                        print("extra ", nouns_extra, adj_extra, verb_extra, other_extra)
                        print("match ", nouns_match, adj_match, verb_match, other_match)
                        print(current_metric)
                    '''

                    if firts_time or current_metric > max_metric:
                        max_metric = current_metric
                        output = entity
                        firts_time = False
                        if (nouns_extra + adj_extra + verb_extra + other_extra == 0 and
                            nouns_not_found + adj_not_found + verb_not_found + other_not_found == 0 and
                            nouns_match + adj_match + verb_match + other_match > 0 and
                            total_entity_words == total_words):
                            return output, max_metric

        # print("max_metric", max_metric, output)
    return output, max_metric



def clean_phrase(input_str="", qualifier_config=None):
    work_str = input_str.replace(".", "").replace(",", "").replace(";", "").replace("!", "").replace("?", "").replace(
        "/", "").replace("\\", "").replace("@", "").replace("#", "").replace("№", "").replace("$", "").replace(
        "%", "").replace("^", "").replace("&", "").replace("*", "").replace("(", "").replace(")", "").replace(
        "_", "").replace("+", "").replace("=", "").replace("'", "").replace('"', "").replace(":", "").replace(
        "<", "").replace(">", "").replace("`", "").replace("~", "")
    for word in qualifier_config.specific_words_beginning:
        if work_str[:len(word + " ")].lower().strip() + " " == word.strip() + " ":
            # print(work_str[:len(word + " ")].lower().strip() + " ")
            work_str = work_str[len(word):].strip()
    for word in qualifier_config.specific_words_everywhere:
        work_str = work_str.lower().replace(" " + word + " ", " ")
        if work_str[:len(word + " ")] == word + " ":
            work_str = work_str[len(word):]
        if work_str[len(work_str) - len(word + " "):] == " " + word:
            work_str = work_str[:len(work_str) - len(word + " ")]
    return work_str.strip()

def remove_unknuwn_words(words_list):
    global tree_entities, ontology_entities
    out_words_list = list()
    for word in words_list:
        if word in tree_entities:
            out_words_list.append(word)
            continue
        elif word in ontology_entities:
            out_words_list.append(word)
            continue
        else:
            w_find = False
            p = morph.parse(word)
            for form in p:
                if form.normal_form in tree_entities or form.normal_form in ontology_entities:
                    out_words_list.append(word)
                    w_find = True
                    break
            if w_find:
                continue
    return out_words_list


def replace_digits(input_text):
    return input_text.replace("1", "_one_").replace("2", "_two_").replace("3", "_thre_").replace(
        "4", "_four_").replace("5", "_five_").replace("6", "_six_").replace("7", "_seven_").replace(
        "8", "_eight_").replace("9", "_nine_").replace("0", "_zero_")


def choise_query_template(input_str="", qualifier_config=None):
    result = dict()
    work_str_list = remove_unknuwn_words(clean_phrase(input_str=input_str, qualifier_config=qualifier_config).split())
    # print("work_str_list", work_str_list)
    extracted_entities = dict()
    sutable_condition = {"max_length": 0, "next_position": "unknown", "next_start": 0}
    # print(qualifier_config.tree)
    for counter, level in enumerate(qualifier_config.tree):
        if counter == 0:
            for position in level["positions"]:
                if "conditions" in level["positions"][position]:
                    for condition in level["positions"][position]["conditions"]:
                        # print(condition)
                        if "words_list" in level["positions"][position]["conditions"][condition]:
                            name_list = []
                            for wd in level["positions"][position]["conditions"][condition]["words_list"]:
                                current_wd_list = wd.strip().split()
                                current_wd_length = len(current_wd_list)
                                is_sutable = True
                                # print(44444444, not (wd.lower().strip() == "any_words" and extracted_entities.get(position) is None))
                                if wd.lower().strip() == "any_words" and extracted_entities.get(position) is None:
                                    # print("any_words at level  1", work_str_list)
                                    for w_2 in work_str_list:
                                        p = morph.parse(w_2.strip())
                                        for frm in p:
                                            if frm.normal_form in ontology_entities:
                                                name_list.append(frm.normal_form)
                                                break
                                    is_sutable = True
                                elif wd.lower().strip() == "any_noun" and sutable_condition["max_length"] == 0:
                                    is_sutable = False
                                    if sutable_condition["next_start"] < len(work_str_list):
                                        w = work_str_list[sutable_condition["next_start"]]
                                        p = morph.parse(w.strip())
                                        for form in p:
                                            if form.tag.POS == "NOUN" or form.tag.POS == "ADJF":
                                                is_sutable = True
                                                break
                                        if is_sutable:
                                            for w_2 in work_str_list[sutable_condition["next_start"]:]:
                                                p = morph.parse(w_2.strip())
                                                more_nouns = False
                                                for form in p:
                                                    # print(form.tag.POS, w_2.strip(), form.normal_form)
                                                    if form.tag.POS == "NOUN" or form.tag.POS == "ADJF":
                                                        name_list.append(form.normal_form)
                                                        more_nouns = True
                                                        break
                                                if not more_nouns:
                                                    break
                                else:
                                    # print(current_wd_length, len(work_str_list))
                                    if current_wd_length > len(work_str_list):
                                        is_sutable = False
                                        continue
                                    if extracted_entities.get(position) is not None:
                                        # print(current_wd_length, extracted_entities.get(position))
                                        if current_wd_length <= len(extracted_entities.get(position).split()):
                                            is_sutable = False
                                            continue
                                    for c, w in enumerate(current_wd_list):
                                        # print(c, w, work_str_list[c])
                                        compare_1 = w.lower().strip()
                                        compare_2 = work_str_list[c].lower().strip()
                                        if compare_1 != compare_2:
                                            p_1 = morph.parse(compare_1)
                                            p_2 = morph.parse(compare_2)
                                            lemma_match = False
                                            for variant_1 in p_1:
                                                for variant_2 in p_2:
                                                    if variant_1.normal_form == variant_2.normal_form:
                                                        lemma_match = True
                                                        break
                                                if lemma_match:
                                                    break
                                            if not lemma_match:
                                                is_sutable = False
                                                break

                                # print("is_sutable", is_sutable)
                                if not is_sutable:
                                    continue
                                elif (is_sutable and sutable_condition["max_length"] < current_wd_length and
                                      "result" not in level["positions"][position]["conditions"][condition]):
                                    # print(11111111111111)
                                    sutable_condition["max_length"] = current_wd_length
                                    if level["positions"][position]["conditions"][
                                        condition].get("next_position"):
                                        sutable_condition["next_position"] = level["positions"][position]["conditions"][
                                            condition]["next_position"]
                                    else:
                                        continue
                                    sutable_condition["next_start"] = current_wd_length
                                    extracted_entities[position] = wd.strip()
                                elif (is_sutable and sutable_condition["max_length"] < current_wd_length and
                                      "result" in level["positions"][position]["conditions"][condition]):
                                    # print(3333333333)
                                    if len(name_list) > 0:
                                        position_n = sutable_condition["next_position"]
                                        extracted_entities[position] = name_list
                                        sutable_condition["max_length"] = len(name_list)
                                    else:
                                        extracted_entities[position] = wd.strip()
                                    # print("extracted_entities", extracted_entities)
                                    sutable_condition["next_position"] == "final"

                                    result["query_type"] = level["positions"][position]["conditions"][condition][
                                        "result"].get(
                                        "query_type")
                                    input_entity_n = level["positions"][position]["conditions"][condition][
                                        "result"].get(
                                        "input_entity")

                                    if input_entity_n is not None:
                                        result["input_entity"] = [extracted_entities.get(ent) for ent in input_entity_n]
                                    else:
                                        result["input_entity"] = None
                                    break

                        # print("result", result)
            # print("next_position 11111", sutable_condition["next_position"])
            if sutable_condition["next_position"] == "final":
                break
            # print(sutable_condition)
            # print(extracted_entities)

        else:
            position_n = sutable_condition["next_position"]
            sutable_condition["max_length"] = 0
            sutable_condition["next_position"] = "unknown"
            # print("position_n", position_n)
            if position_n != "unknown" and position_n != "final":
                next_position = level["positions"].get(position_n)
                # print("next_position 22222", next_position)
                if next_position is not None and "conditions" in next_position:
                    for condition in next_position["conditions"]:
                        if "words_list" in next_position["conditions"][condition]:
                            name_list = []
                            for wd in next_position["conditions"][condition]["words_list"]:
                                is_sutable = True
                                if wd.lower().strip() == "any_words" and sutable_condition["max_length"] == 0:
                                    is_sutable = False
                                    # print(sutable_condition["next_start"], len(work_str_list))
                                    if sutable_condition["next_start"] < len(work_str_list):
                                        is_sutable = True
                                    if is_sutable:
                                        for w_2 in work_str_list[sutable_condition["next_start"]:]:
                                            p = morph.parse(w_2.strip())[0]
                                            name_list.append(p.normal_form)
                                        # print("name_list 1", name_list)
                                elif wd.lower().strip() == "any_undefined" and sutable_condition["max_length"] == 0:
                                    is_sutable = False
                                    # print(sutable_condition["next_start"], len(work_str_list))
                                    if sutable_condition["next_start"] < len(work_str_list):
                                        is_sutable = True
                                        # if is_sutable:
                                        w = work_str_list[sutable_condition["next_start"]]
                                        p = morph.parse(w.strip())[0]
                                        name_list.append(p.normal_form)
                                        # print("name_list 1", name_list)

                                elif wd.lower().strip() == "any_noun" and sutable_condition["max_length"] == 0:
                                    is_sutable = False
                                    if sutable_condition["next_start"] < len(work_str_list):
                                        w = work_str_list[sutable_condition["next_start"]]
                                        p = morph.parse(w.strip())
                                        for form in p:

                                            if form.tag.POS == "NOUN" or form.tag.POS == "ADJF":
                                                is_sutable = True
                                                break
                                        if is_sutable:
                                            for w_2 in work_str_list[sutable_condition["next_start"]:]:
                                                p = morph.parse(w_2.strip())
                                                more_nouns = False
                                                for form in p:
                                                    # print(form.tag.POS, w_2.strip(), form.normal_form)
                                                    if form.tag.POS == "NOUN":
                                                        name_list.append(form.normal_form)
                                                        more_nouns = True
                                                        break
                                                    elif form.tag.POS == "ADJF":
                                                        if (len(form.normal_form) > 4 and
                                                                form.normal_form[len(form.normal_form) - 4:] == "ький"):
                                                            name_list.append(form.normal_form)
                                                            more_nouns = True
                                                            break
                                                        elif (len(form.normal_form) > 3 and
                                                              form.normal_form[len(form.normal_form) - 3:] == "ька"):
                                                            name_list.append(form.normal_form)
                                                            more_nouns = True

                                                if not more_nouns:
                                                    break

                                elif wd.lower().strip() == "year_str":
                                    is_sutable = False
                                    if sutable_condition["next_start"] < len(work_str_list):
                                        w = work_str_list[sutable_condition["next_start"]]
                                        if len(w) == 4 and w.isdigit():
                                            is_sutable = True
                                    else:
                                        is_sutable = False
                                elif wd.lower().strip() == "not_noun" and sutable_condition["max_length"] == 0:
                                    # print("not_noun")
                                    # print(sutable_condition["next_start"] + 1 >= len(work_str_list))
                                    if sutable_condition["next_start"] + 1 >= len(work_str_list):
                                        is_sutable = True
                                    else:
                                        w = work_str_list[sutable_condition["next_start"]]
                                        p = morph.parse(w.strip())
                                        for form in p:
                                            if form.tag.POS == "NOUN" or form.tag.POS == "ADJF":
                                                is_sutable = False
                                                break
                                else:
                                    is_sutable = False
                                # print(is_sutable, work_str_list[sutable_condition["next_start"]])
                                if not is_sutable:
                                    # print("qwerty")
                                    is_sutable = True
                                    current_wd_list = wd.strip().split()
                                    current_wd_length = len(current_wd_list)

                                    if current_wd_length > (len(work_str_list) - sutable_condition["next_start"]):
                                        is_sutable = False
                                        continue
                                    for c, w in enumerate(current_wd_list):
                                        # print(work_str_list[c + sutable_condition["next_start"]], w)
                                        if w != work_str_list[c + sutable_condition["next_start"]]:
                                            is_sutable = False
                                            break
                                    if not is_sutable:
                                        continue
                                    else:
                                        if is_sutable and sutable_condition["max_length"] < current_wd_length:
                                            sutable_condition["max_length"] = current_wd_length
                                            sutable_condition["next_position"] = next_position["conditions"][
                                                condition].get("next_position")
                                            extracted_entities[position_n] = wd.strip()
                                            # print("extracted_entities[position_n]", extracted_entities[position_n])
                                else:
                                    if len(name_list) > 0:
                                        sutable_condition["max_length"] = len(name_list)
                                        sutable_condition["next_position"] = next_position["conditions"][
                                            condition].get("next_position")
                                        extracted_entities[position_n] = name_list
                                        # print("name_list", name_list)
                                    elif wd.lower().strip() == "year_str":
                                        sutable_condition["max_length"] = 1
                                        sutable_condition["next_position"] = next_position["conditions"][
                                            condition].get("next_position")
                                        extracted_entities[position_n] = "Year_" + work_str_list[
                                            sutable_condition["next_start"]]
                                    elif wd.lower().strip() == "any_undefined":
                                        sutable_condition["max_length"] = 0
                                        sutable_condition["next_position"] = next_position["conditions"][
                                            condition].get("next_position")
                                        extracted_entities[position_n] = work_str_list[sutable_condition["next_start"]]
                                    elif wd.lower().strip() == "not_noun":
                                        sutable_condition["max_length"] = 0
                                        sutable_condition["next_position"] = next_position["conditions"][
                                            condition].get("next_position")
                                        if sutable_condition["next_start"] + 1 >= len(work_str_list):
                                            extracted_entities[position_n] = ""
                                        else:
                                            extracted_entities[position_n] = work_str_list[
                                                sutable_condition["next_start"]]

                        if (sutable_condition["next_position"] is None and "result" in next_position[
                            "conditions"][condition]):
                            # print(extracted_entities)
                            # print(next_position["conditions"][condition]["result"])
                            result["query_type"] = next_position["conditions"][condition]["result"].get("query_type")
                            input_entity_n = next_position["conditions"][condition]["result"].get("input_entity")
                            if input_entity_n is not None:
                                result["input_entity"] = [extracted_entities.get(ent) for ent in input_entity_n]
                            else:
                                result["input_entity"] = None
                            break

                if len(result) > 0:
                    break

                sutable_condition["next_start"] += sutable_condition["max_length"]
                # print(sutable_condition)
            elif position_n == "unknown" and result.get("query_type") is None:
                result["query_type"] = 'unknown'
                break
            else:
                break

    # print(extracted_entities)

    return result


def fit_input_entities(raw_result):
    # print("raw_result ", raw_result)
    chapters_included = ["class_names_dict", "individual_names_dict"]
    if isinstance(raw_result, dict) and 'input_entity' in raw_result and\
            (isinstance(raw_result.get('input_entity'), list) or isinstance(raw_result.get('input_entity'), set)):
        if "query_type" in raw_result:
            if ("certain_predicate_query" in raw_result["query_type"] or
                  "predicate_query" in raw_result["query_type"] or
                  "predicate_definition" in raw_result["query_type"]):
                chapters_included.append("pradicates")

        raw_result['input_entity'] = [find_ontology_entity(word_list=ent, chapters=chapters_included) if isinstance(ent, list) or ent is None else
                                      find_ontology_entity(word_list=ent.split(), chapters=chapters_included) for ent in raw_result.get('input_entity')]

    return raw_result












if __name__ == "__main__":
    config = QualifierConfig.get_instance()
    t_0 = time.time()
    cleaned_phrase = choise_query_template(input_str="таблиця іа з розділу 2",
                                  qualifier_config=config)
    d_t = time.time() - t_0
    print(d_t)
    print(cleaned_phrase)
    result = fit_input_entities(cleaned_phrase)
    print(result)

# "Що відомо тобі про те, які листи отримував О. Гончар 1956 року?"