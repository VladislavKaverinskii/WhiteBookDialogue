# -*- coding: utf8 -*-

import xml.etree.ElementTree as Et
import json
import traceback



def execute(ontology_name, morph):
    with open(ontology_name, 'r', encoding='utf-8') as xml_file:
        ontology = xml_file.read()
    output_entities =get_entities(ontology, morph)

    output_entities = json.dumps(list(set(output_entities)), ensure_ascii=False, indent=2).encode('utf8').decode()
    f_1 = open('ontology_entities.json', mode='w', encoding='utf-8')
    f_1.write(output_entities)
    f_1.close()
    f_2 = open('converter/ontology_entities.json', mode='w', encoding='utf-8')
    f_2.write(output_entities)
    f_2.close()


def get_entities(input_owl, morph):
    tree = Et.ElementTree(Et.fromstring(input_owl.encode('utf-8').decode('utf-8')))

    # tree = Et.parse(input_owl)
    root = tree.getroot()
    ontology_entities = list()
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
                        class_name_clean = class_name.replace("_comma_", " ").replace("_apostrof_", "'").replace(
                            "_squote_", "'").replace("_dquote_", " ").replace("_dot_", " ").replace(
                            "_lquote_", " ").replace("_rquote_", " ").replace("_colon_", " ").replace(
                            "_dash_", "").replace("_lbraket_", " ").replace("_rbraket_", " ").replace(
                            "_slash_", " ").replace("_", " ").replace("__", " ")
                        if class_name_clean.strip() != "":
                            class_name_list = [max(morph.parse(word.strip().lower()),
                                                   key=lambda i: i.score).normal_form
                                               for word in class_name_clean.split()
                                               if len(word.strip().strip("'").lower()) > 0]
                            ontology_entities += class_name_list
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
                    predicate_name_clean = predicate_name.replace("_comma_", " ").replace("_apostrof_", "'").replace(
                        "_squote_", "'").replace("_dquote_", " ").replace("_dot_", " ").replace(
                        "_lquote_", " ").replace("_rquote_", " ").replace("_colon_", " ").replace(
                        "_dash_", "").replace("_lbraket_", " ").replace("_rbraket_", " ").replace(
                        "_slash_", " ").replace("_", " ").replace("__", " ")
                    if predicate_name_clean.strip() != "":
                        predicate_name_list = [max(morph.parse(word.strip().lower()),
                                                   key=lambda i: i.score).normal_form
                                               for word in predicate_name_clean.split()
                                               if len(word.strip().strip("'").lower()) > 0]
                        ontology_entities += predicate_name_list

    return list(set(ontology_entities))
