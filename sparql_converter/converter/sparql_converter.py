# -*- coding: utf8 -*-

import json
import xml.etree.ElementTree as Et
from argparse import ArgumentParser
import random
import time
import statistics
import text_analysis_handlers
import foreign_libraries
try:
    import query_template_qualifier_special
except:
    import converter.query_template_qualifier_special as query_template_qualifier_special


qualifier_config = query_template_qualifier_special.QualifierConfig.get_instance(
        config_file="tree.xml")

class QueryTemplates:
    __instance = None

    def __init__(self):
        if not QueryTemplates.__instance:
            self.templates = []
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="query_template.xml"):
        if not cls.__instance:
            cls.__instance = QueryTemplates()
            cls.__instance.config_file = config_file
            with open(config_file, 'r', encoding='utf-8') as xml_file:
                tree = Et.fromstring((xml_file).read().encode('utf-8').decode('utf-8'))
            for query_template in tree:
                if query_template.tag == "template":
                    new_template = {}
                    for item in query_template:
                        if item.tag == "language":
                            new_template["language"] = item.text.strip()
                        elif item.tag == "type":
                            new_template["type"] = item.text.strip()
                        elif item.tag == "marker_words":
                            if len(item) > 0:
                                new_template["marker_words"] = [m_word.text.strip() for m_word in item]
                            else:
                                new_template["marker_words"] = []
                        elif item.tag == "variables":
                            variables = {}
                            for variable in item:
                                if variable.tag == "variable":
                                    var_name = variable.find("name").text.strip()
                                    if var_name is not None:
                                        variables[var_name] = {
                                            "name": var_name,
                                            "type": variable.find("var_type").text.strip(),
                                            "destination": variable.find("destination").text.strip(),
                                            "allow_list": variable.find("allow_list").text.strip()
                                        }
                            new_template["variables"] = variables
                        elif item.tag == "query_base":
                            new_template["query_base"] = item.text.strip()
                        elif item.tag == "conditions":
                            if len(item) > 0:
                                new_template["conditions"] = [condition.text.strip() for condition in item]
                            else:
                                new_template["conditions"] = []
                        elif item.tag == "ordering":
                            new_template["ordering"] = item.text.strip()
                    cls.__instance.templates.append(new_template)

        return cls.__instance


class InputVarsNames:
    __instance = None

    def __init__(self):
        if not InputVarsNames.__instance:
            self.any = ""
            self.marker_word = ""
            self.action_entity = ""
            self.object_entity = ""
            self.number_entity = ""
            self.adjective_entity = ""
            self.adverb_entity = ""
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="converter_config.xml"):
        if not cls.__instance:
            cls.__instance = InputVarsNames()
            cls.__instance.config_file = config_file
            tree = Et.parse(config_file)
            root = tree.getroot()
            for item in root:
                if item.tag == "input_variables_names_description":
                    for variable in item:
                        if variable.find("destination") is not None:
                            if variable.find("destination").text.strip() == "any":
                                if variable.find("name") is not None:
                                    cls.__instance.any = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "marker_word":
                                if variable.find("name") is not None:
                                    cls.__instance.marker_word = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "action_entity":
                                if variable.find("name") is not None:
                                    cls.__instance.action_entity = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "object_entity":
                                if variable.find("name") is not None:
                                    cls.__instance.object_entity = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "number_entity":
                                if variable.find("name") is not None:
                                    cls.__instance.number_entity = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "adjective_entity":
                                if variable.find("name") is not None:
                                    cls.__instance.adjective_entity = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "adverb_entity":
                                if variable.find("name") is not None:
                                    cls.__instance.adverb_entity = variable.find("name").text.strip()
        return cls.__instance


class MarkerWords:
    __instance = None
    def __init__(self):
        if not MarkerWords.__instance:
            self.marker_words = {}
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="marker_words.xml"):
        if not cls.__instance:
            cls.__instance = MarkerWords()
            cls.__instance.config_file = config_file
            f = open(config_file, 'r', encoding='utf-8')
            tree = Et.ElementTree(Et.fromstring(f.read()))
            root = tree.getroot()
            for i in root:
                if i.tag == "item":
                    word = i.find("word").text.strip()
                    type = i.find("type").text.strip()
                    cls.__instance.marker_words[word] = type
        return cls.__instance

class Prefixes:
    __instance = None

    def __init__(self):
        if not Prefixes.__instance:
            self.prefixes = ""
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="prefixes.json"):
        if not cls.__instance:
            cls.__instance = Prefixes()
            cls.__instance.config_file = config_file
            with open(config_file, 'r', encoding='utf-8') as json_file:
                prefixes_json = json.loads(json_file.read().encode('utf-8').decode('utf-8'))
            for key in prefixes_json:
                cls.__instance.prefixes += "PREFIX " + key + ": " + prefixes_json[key] + " "
                if key.lower() == "base":
                    cls.__instance.prefixes += "PREFIX " + " : " + prefixes_json[key] + " "
        return cls.__instance




def form_query(query_template=None, prefixes=None, input_vars=None):
    var_value_metric = -1.0
    if prefixes is None:
        current_prefixes = ""
    else:
        current_prefixes = prefixes.prefixes
    if query_template is not None and input_vars is not None:
        # print("input_vars: ", input_vars)
        if isinstance(query_template, dict) and isinstance(input_vars, dict):
            query_base = query_template.get("query_base")
            for variable in query_template.get("variables"):
                # print("destination", query_template.get("variables").get(variable).get("destination").lower())
                if query_template.get("variables").get(variable).get("destination").lower() == "result":
                    # print(query_template.get("variables").get(variable).get("name"))
                    if "[" + query_template.get("variables").get(variable).get("name") + "]" in query_base:
                        query_base = query_base.replace(
                            "[" + query_template.get("variables").get(variable).get("name") + "]",
                            "?" + query_template.get("variables").get(variable).get("name"))
            template_text = current_prefixes + query_base
            # print(input_vars)
            key_to_del = [key for key in input_vars if len(input_vars[key]) < 1]
            for key in key_to_del:
                del input_vars[key]
            # if len(input_vars) < 1:
            #    return ""
            if len(query_template.get("conditions")) > 0:
                template_text += " WHERE {"
                for condition in query_template.get("conditions"):
                    new_condition_string = condition
                    if len(condition) > 0:
                        if condition[-1] != ".":
                            new_condition_string += "."
                        for variable in query_template.get("variables"):
                            if ((query_template.get("variables").get(variable).get("destination").lower() ==
                                 "inner")
                                or (query_template.get("variables").get(variable).get("destination").lower() ==
                                    "result")):
                                if "["+query_template.get("variables").get(variable).get("name") + "]" in condition:
                                    new_condition_string = new_condition_string.replace(
                                        "[" + query_template.get("variables").get(variable).get("name") + "]",
                                        "?" + query_template.get("variables").get(variable).get("name"))
                            elif query_template.get("variables").get(variable).get("destination").lower() == "input":
                                for input_var in input_vars:
                                    # print("input_var: ", input_var, input_vars.get(input_var), type(input_vars.get(input_var)))
                                    if input_var == query_template.get("variables").get(variable).get("name"):
                                        if "[" + input_var + "]" in condition:
                                            if isinstance(input_vars.get(input_var), list) or isinstance(input_vars.get(input_var), set):
                                                if len(input_vars.get(input_var)) > 0:
                                                    if query_template.get("variables").get(variable).get(
                                                            "allow_list").lower() == "true":
                                                        new_conditions_list = list()
                                                        var_value_metrics = list()
                                                        for var_value in input_vars.get(input_var):
                                                            if (isinstance(var_value, tuple) or
                                                                isinstance(var_value, list)):
                                                                if len(var_value) > 1:
                                                                    var_value_text = var_value[0]
                                                                    var_value_metric = var_value[1]
                                                                elif len(var_value) > 0:
                                                                    var_value_text = var_value[0]
                                                                    var_value_metric = -1.0
                                                                else:
                                                                    continue
                                                            else:
                                                                var_value_text = str(var_value)
                                                                var_value_metric = -1.0
                                                            var_value_metrics.append(var_value_metric)
                                                            new_conditions_list.append(new_condition_string.replace(
                                                                "[" + query_template.get(
                                                                    "variables").get(variable).get("name") + "]",
                                                                ":" + str(var_value_text)))
                                                        new_condition_string = " ".join(new_conditions_list)
                                                        try:
                                                            var_value_metric = statistics.mean([float(val) for val in var_value_metrics])
                                                        except Exception as e:
                                                            print(e)
                                                            var_value_metric = -1.0
                                                    else:
                                                        if (isinstance(input_vars.get(input_var)[0], tuple) or
                                                                isinstance(input_vars.get(input_var)[0], list)):
                                                            if len(input_vars.get(input_var)[0]) > 1:
                                                                var_value_text = input_vars.get(input_var)[0][0]
                                                                var_value_metric = input_vars.get(input_var)[0][1]
                                                            elif len(input_vars.get(input_var)[0]) > 0:
                                                                var_value_text = input_vars.get(input_var)[0][0]
                                                                var_value_metric = -1.0
                                                            else:
                                                                continue
                                                        else:
                                                            var_value_text = str(input_vars.get(input_var)[0])
                                                            var_value_metric = -1.0
                                                        new_condition_string = new_condition_string.replace(
                                                            "[" + query_template.get("variables").get(variable).get(
                                                                "name") + "]",
                                                             ":" + str(var_value_text))
                                            else:
                                                if (isinstance(input_vars.get(input_var), tuple)):
                                                    if len(input_vars.get(input_var)) > 1:
                                                        var_value_text = input_vars.get(input_var)[0]
                                                        var_value_metric = input_vars.get(input_var)[1]
                                                    elif len(input_vars.get(input_var)) > 0:
                                                        var_value_text = input_vars.get(input_var)[0]
                                                        var_value_metric = -1.0
                                                    else:
                                                        continue
                                                else:
                                                    var_value_text = str(input_vars.get(input_var))
                                                    var_value_metric = -1.0

                                                new_condition_string = new_condition_string.replace(
                                                    "[" + query_template.get("variables").get(variable).get(
                                                        "name") + "]",
                                                    ":" + str(var_value_text))
                                # print("new_condition_string ", new_condition_string)
                    template_text += " " + new_condition_string + " "
                template_text += "}"
            if 'ordering' in query_template and len(query_template.get('ordering')) > 0:
                template_text += " ORDER BY ?" + query_template.get('ordering').replace("[", "").replace("]", "").strip()
            # print("var_value_metric: ", var_value_metric)
            return template_text, var_value_metric
    return "", var_value_metric


def digit_symbol_replacer(input_digit_string="0"):
    if input_digit_string == "0":
        return "Null"
    elif input_digit_string == "1":
        return "En"
    elif input_digit_string == "2":
        return "To"
    elif input_digit_string == "3":
        return "Tre"
    elif input_digit_string == "4":
        return "Fire"
    elif input_digit_string == "5":
        return "Fem"
    elif input_digit_string == "6":
        return "Seks"
    elif input_digit_string == "7":
        return "Sju"
    elif input_digit_string == "8":
        return "Åtte"
    elif input_digit_string == "9":
        return "Ni"
    else:
        return input_digit_string


def digit_string_replacer(input_digit_string="0"):
    out_str = ""
    for symbol in input_digit_string:
        if symbol.isdigit():
            out_str += digit_symbol_replacer(symbol)
        else:
            out_str += symbol
    return out_str


class WordObj:
    def __init__(self, pos="", word=""):
        self.pos = pos
        self.word = word

    def __hash__(self):
        return int(hashlib.md5((self.pos + self.word).encode()).hexdigest(), 16)

    def serialize(self):
        return {self.word: self.pos}


class AnalyzerAPIWrapper:
    def get_allterms_xml(self, text=""):
        parser_obj = text_analysis_handlers.TermParser()
        return parser_obj.make_xml(document=text)

    def get_parce_xml(self, text=""):
        parser_obj = text_analysis_handlers.WordParser()
        return parser_obj.make_xml(document=text)


def form_set_of_special_queries(query_template=None, prefixes=None, entities_for_query=None, query_type=None):
    # print("burum-burum", entities_for_query, query_type, query_template)
    if prefixes is None:
        prefixes = Prefixes().get_instance()
    else:
        prefixes = prefixes.get_instance()

    if entities_for_query is not None and query_template is not None:
        if isinstance(query_template, str):
            current_query, metric_value = form_query(query_template=query_template, input_vars=entities_for_query)
            return [[{"ontology": "ontology", "query": current_query, "query_type": query_type,
                      "metric": metric_value}]]
        elif isinstance(query_template, list) or isinstance(query_template, set):
            result = list()
            for i, type in enumerate(query_type):
                if type.strip().lower() == "predicate_definition":
                    defined_by_predicates = query_template_qualifier_special.keywords["defined_classes"]
                    definition_exist = False
                    for entity in entities_for_query:
                        if isinstance(entities_for_query[entity], str):
                            compare_str = entities_for_query[entity].lower().strip()
                        elif isinstance(entities_for_query[entity], tuple) or isinstance(entities_for_query[entity], list):
                            if len(entities_for_query[entity]) > 0:
                                compare_str = entities_for_query[entity][0].lower().strip()
                            else:
                                continue
                        else:
                            continue
                        if compare_str in [pr.lower().strip() for pr in
                                                                          defined_by_predicates]:
                            definition_exist = True
                            break
                else:
                    definition_exist = True
                if definition_exist:
                    for template in query_template:
                        if template["type"].lower().strip() == type.strip().lower():
                            current_query, metric_value = form_query(query_template=template, prefixes=prefixes,
                                                                     input_vars=entities_for_query)
                            # print("current_query 11111111111111111", current_query)
                            result.append(
                                [{"ontology": "ontology", "query": current_query, "query_type": template["type"],
                                  "entities_for_query": entities_for_query, "metric": metric_value}])
                            break
            return result
        else:
            return [[{"ontology": "ontology", "query": "", "query_type": ""}]]
    elif entities_for_query is None and query_template is not None:
        if isinstance(query_template, str):
            current_query, metric_value = form_query(query_template=query_template, prefixes=prefixes, input_vars={})
            return [[{"ontology": "ontology", "query": current_query, "query_type": query_type,
                      "entities_for_query": {}, "metric": metric_value}]]
        elif isinstance(query_template, list) or isinstance(query_template, set):
            result = list()
            for i, template in enumerate(query_template):
                current_query, metric_value = form_query(query_template=template, prefixes=prefixes, input_vars={})
                # print("current_query 11111111111111111", current_query)
                result.append([{"ontology": "ontology", "query": current_query, "query_type": template["type"],
                                "entities_for_query": {}, "metric": metric_value}])
            return result
        else:
            return [[{"ontology": "ontology", "query": "", "query_type": "", "metric": -1.0}]]


def select_query_template(input_text="", templates=None, query_templates_file="query_template.xml"):
    start_time = time.time()
    if templates is None:
        templates = QueryTemplates().get_instance(config_file=query_templates_file)
    else:
        templates = templates.get_instance(config_file=query_templates_file)
    query_templates = None
    analysis_result = query_template_qualifier_special.fit_input_entities(
        query_template_qualifier_special.choise_query_template(
        input_str=input_text,
        qualifier_config=qualifier_config))
    # print(analysis_result)
    print("getting templates time ", (time.time() - start_time))
    start_time = time.time()
    query_type = analysis_result.get('query_type')
    input_entities = analysis_result.get('input_entity')
    # print("input_entities", input_entities)
    if input_entities is not None:
        if len(input_entities) < 2:
            if isinstance(input_entities, list):
                try:
                    input_entities = {"inputEntity": [i if not isinstance(i, list) else [j for j in i]
                                                      for i in input_entities][0]}
                    # print("sddfgdfdfbfv")
                except:
                    input_entities = {"inputEntity": []}
            else:
                input_entities = {"inputEntity": input_entities}

            # print(input_entities)
        else:
            input_entities_tmp = dict()
            for i, entity in enumerate(input_entities):
                if isinstance(entity, list):
                    input_entities_tmp["inputEntity_" + str(i+1)] = [j for j in entity if (len(j) > 0)]
                else:
                    if len(entity) > 0:
                        input_entities_tmp["inputEntity_" + str(i + 1)] = entity
            input_entities = input_entities_tmp
    print("getting entities ", (time.time() - start_time))
    start_time = time.time()

    for t in templates.templates:
        # print("type", t.get("type"))
        if t.get("type") is not None and t.get("type").strip() in query_type:
            if query_templates is None:
                query_templates = [t]
            elif isinstance(query_templates, list):
                query_templates.append(t)
            if len(query_templates) >= len(query_type):
                break
    print("form templates set time ", (time.time() - start_time))

    return query_templates, query_type, input_entities







