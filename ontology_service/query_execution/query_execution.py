# -*- coding: utf8 -*-

import json
import xml.etree.ElementTree as Et
from argparse import ArgumentParser
import random
import time
import traceback

from SPARQLWrapper import SPARQLWrapper, JSON

class Ontologies:
    __instance = None
    def __init__(self):
        if not Ontologies.__instance:
            self.ontology_object = None
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, ontology_endpoint="http://localhost:3030/WhiteBook"):
        if not cls.__instance:
            cls.__instance = Ontologies()
            cls.__instance.ontology_object = SPARQLWrapper(ontology_endpoint)
            cls.__instance.ontology_object.setReturnFormat(JSON)
        return cls.__instance


def execute_sparql_query(query="", graph=None):
    if graph is not None and query is not None and "select" in query.lower():
        graph.setQuery(query)
        return graph.query().convert()
    else:
        return None


def get_ontilogy_answers_from_qurey_set(query_set=None, ontology_object=None,
                                        ontology_endpoint="http://localhost:3030/WhiteBook"):
    s_time = time.time()
    random.seed()
    is_any_answer = False
    if query_set is not None:
        if ontology_object is None:
            ontology_object = Ontologies().get_instance(ontology_endpoint=ontology_endpoint)
        else:
            ontology_object = ontology_object.get_instance(ontology_endpoint=ontology_endpoint)
        results = []
        found_answers = []
        if isinstance(query_set, str):
            try:
                query_set = json.loads(query_set)
            except:
                return []
        total_keys_n = 0
        for counter, query_list in enumerate(query_set):
            if total_keys_n > 10:
                break
            results_level = []
            for j, query_point in enumerate(query_list):
                if total_keys_n > 10:
                    break
                query = query_point.get("query")
                semantic_type = query_point["query_type"]
                entities_for_query = query_point["entities_for_query"]
                metric = query_point.get("metric")

                if is_any_answer and (semantic_type == "linked_classes_down" or semantic_type == "linked_classes_up"):
                    continue

                print("query ", query)
                if query is not None and query != "":
                    result = execute_sparql_query(query=query, graph=ontology_object.ontology_object)
                    print("current_answer", result)
                    if result is not None and len(result) > 1 and semantic_type != "linked_classes_down"\
                            and semantic_type != "linked_classes_up":
                        is_any_answer = True
                    if result is not None:
                        answer_keys = []
                        print("result", result, len(result))

                        current_answer_list = list()

                        if 'head' in result and 'results' in result:
                            if 'vars' in result['head']:
                                if len(result['head']['vars']) > 1:
                                    for res in result['results']:
                                        for res_2 in result['results'][res]:
                                            if 'title' in res_2 and 'result' in res_2:
                                                if 'value' in res_2['title'] and 'value' in res_2['result']:
                                                    if '#' in res_2['title']['value']:
                                                        res_2['title']['value'] = res_2['title']['value'].split('#')[1]
                                                    elif "http://www.semanticweb.org/" in res_2['title']['value']:
                                                        res_2['title']['value'] = res_2['title']['value'].strip("http://www.semanticweb.org/")
                                                    if '#' in res_2['result']['value']:
                                                        res_2['result']['value'] = res_2['result']['value'].split('#')[1]
                                                    elif "http://www.semanticweb.org/" in res_2['result']['value']:
                                                        res_2['result']['value'] = res_2['result']['value'].strip(
                                                            "http://www.semanticweb.org/")
                                                    current_answer_list.append([res_2['title']['value'], res_2['result']['value']])
                                elif (len(result['head']['vars']) == 1 and 'result' in result['head']['vars']
                                      or 'title' in result['head']['vars']):
                                    for res in result['results']:
                                        for res_2 in result['results'][res]:
                                            if 'title' in res_2 and 'value' in res_2['title']:
                                                if '#' in res_2['title']['value']:
                                                    res_2['title']['value'] = res_2['title']['value'].split('#')[1]
                                                elif "http://www.semanticweb.org/" in res_2['title']['value']:
                                                    res_2['title']['value'] = res_2['title']['value'].strip(
                                                        "http://www.semanticweb.org/")
                                                current_answer_list.append([res_2['title']['value']])
                                            elif 'result' in res_2 and 'value' in res_2['result']:
                                                if '#' in res_2['result']['value']:
                                                    res_2['result']['value'] = res_2['result']['value'].split('#')[1]
                                                elif "http://www.semanticweb.org/" in res_2['result']['value']:
                                                    res_2['result']['value'] = res_2['result']['value'].strip(
                                                        "http://www.semanticweb.org/")
                                                current_answer_list.append([res_2['result']['value']])

                        print("query counter", counter, j)
                        for answer in current_answer_list:
                            if answer not in found_answers:
                                if len(answer) > 1:
                                    answer_keys.append({"name": answer[0], "key": answer[1], "type": "letters",
                                                        "is_link": False, "semantic_type": semantic_type,
                                                        "entities_for_query": entities_for_query,
                                                        "metric": metric})
                                else:
                                    answer_keys.append({"name": "", "key": answer[0], "type": "letters",
                                                        "is_link": False, "semantic_type": semantic_type,
                                                        "entities_for_query": entities_for_query,
                                                        "metric": metric})
                                found_answers.append(answer)
                                total_keys_n += 1
                        result_tmp = dict()
                        for ky in answer_keys:
                            if ky.get('key') in result_tmp:
                                ky["additional"] = result_tmp[ky.get('key')]
                            else:
                                ky["additional"] = dict()
                        results_level.append(answer_keys)
            results.append(results_level)
        return results
    return []



