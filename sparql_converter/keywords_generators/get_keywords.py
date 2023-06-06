# -*- coding: utf8 -*-

import xml.etree.ElementTree as Et
import json
import traceback


def execute(ontology_name, morph):
    with open(ontology_name, 'r', encoding='utf-8') as xml_file:
        ontology = xml_file.read()

    output_entities = get_entities(ontology, morph)

    output_entities = json.dumps(output_entities, ensure_ascii=False, indent=2).encode('utf8').decode()

    f_1 = open('keywords.json', mode='w', encoding='utf-8')
    f_1.write(output_entities)
    f_1.close()

    f_2 = open('converter/keywords.json', mode='w', encoding='utf-8')
    f_2.write(output_entities)
    f_2.close()


def get_entities(input_owl, morph):
    tree = Et.ElementTree(Et.fromstring(input_owl.encode('utf-8').decode('utf-8')))
    root = tree.getroot()
    class_names_dict = dict()
    individual_names_dict = dict()
    pradicates = dict()
    defined_classes = set()
    for i in root:
        if i.tag.split("}")[-1].lower() == "class" or i.tag.split("}")[-1].lower() == "namedindividual":
            class_name = ""
            for attr in i.attrib:
                if attr.split("}")[-1].lower() == "id" or attr.split("}")[-1].lower() == "about":
                    if (i.attrib.get(attr).lower().strip() != "default"
                            and i.attrib.get(attr).lower().strip() != "equivalent"
                            and i.attrib.get(attr).lower().strip() != "linkgroups"
                            and i.attrib.get(attr).lower().strip() != "aspect"
                            and i.attrib.get(attr).lower().strip() != "topic"
                            and i.attrib.get(attr).lower().strip() != "individual"
                            and i.attrib.get(attr).lower().strip() != "chapter"
                            and i.attrib.get(attr).lower().strip() != "subclass"
                            and i.attrib.get(attr).lower().strip() != "graph_data"
                            and i.attrib.get(attr).lower().strip() != "datagroups"):
                        class_name = i.attrib.get(attr)
                        class_name_with_digits = recover_digits(class_name)
                        class_name_clean = class_name_with_digits.replace("_comma_", " ").replace("_apostrof_", "'").replace(
                                "_squote_", "'").replace("_dquote_", " ").replace("_dot_", " ").replace(
                                "_lquote_", " ").replace("_rquote_", " ").replace("_colon_", " ").replace(
                                "_dash_", "").replace("_lbraket_", " ").replace("_rbraket_", " ").replace(
                                "_slash_", " ").replace("_", " ").replace("__", " ")

                        if class_name_clean.strip() != "":
                            class_name_list = [{"text": max(morph.parse(word.strip().lower()),
                                                            key=lambda i: i.score).normal_form,
                                                "POS": max(morph.parse(word.strip().lower()),
                                                           key=lambda i: i.score).tag.POS}
                                               for word in class_name_clean.split()
                                               if len(word.strip().strip("'").lower()) > 0]

                            if i.tag.split("}")[-1].lower() == "class":
                                class_names_dict[class_name] = dict()
                                class_names_dict[class_name]["words"] = class_name_list
                            elif i.tag.split("}")[-1].lower() == "namedindividual":
                                individual_names_dict[class_name] = dict()
                                individual_names_dict[class_name]["words"] = class_name_list
                        break
            for sub_tag in i:
                if (sub_tag.tag.lower().strip().split("}")[-1] != "label"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "type"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "guid"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "shape"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "xpos"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "ypos"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "color"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "subclassof"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "graph_data"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "padding"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "hspacing"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "vspacing"
                        and sub_tag.tag.lower().strip().split("}")[-1] != "nodesize"):
                    predicate_name = sub_tag.tag.split("}")[-1]
                    predicate_name_with_digits = recover_digits(predicate_name)
                    predicate_name_clean = predicate_name_with_digits.replace("_comma_", " ").replace("_apostrof_", "'").replace(
                        "_squote_", "'").replace("_dquote_", " ").replace("_dot_", " ").replace(
                        "_lquote_", " ").replace("_rquote_", " ").replace("_colon_", " ").replace(
                        "_dash_", "").replace("_lbraket_", " ").replace("_rbraket_", " ").replace(
                        "_slash_", " ").replace("_", " ").replace("__", " ")

                    if predicate_name_clean.strip() != "":
                        predicate_name_list = [{"text": max(morph.parse(word.strip().lower()),
                                                            key=lambda i: i.score).normal_form,
                                                "POS": max(morph.parse(word.strip().lower()),
                                                           key=lambda i: i.score).tag.POS}
                                               for word in predicate_name_clean.split()
                                               if len(word.strip().strip("'").lower()) > 0]
                        if predicate_name not in pradicates:
                            pradicates[predicate_name] = {"words": predicate_name_list, "in_class": [class_name]}
                        else:
                            if pradicates.get(predicate_name) is not None and class_name not in pradicates[predicate_name]["in_class"]:
                                pradicates[predicate_name]["in_class"].append(class_name)


    for i in pradicates:
        if i in pradicates[i]['in_class']:
            defined_classes.add(i)

    return {
        "class_names_dict": class_names_dict,
        "individual_names_dict": individual_names_dict,
        "pradicates": pradicates,
        "defined_classes": list(defined_classes)
    }


def replace_digits(input_text):
    return input_text.replace("_one_", "1").replace("2", "_two_").replace("3", "_thre_").replace(
        "4", "_four_").replace("5", "_five_").replace("6", "_six_").replace("7", "_seven_").replace(
        "8", "_eight_").replace("9", "_nine_").replace("0", "_zero_")


def recover_digits(input_text):
    return input_text.replace("_one_", "1").replace("_two_", "2").replace("_thre_", "3").replace(
        "_four_", "4").replace("_five_", "5").replace("_six_", "6").replace("_seven_", "7").replace(
        "_eight_", "8").replace("_nine_", "9").replace("_zero_", "0")














