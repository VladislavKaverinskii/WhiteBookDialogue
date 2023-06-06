# -*- coding: utf-8 -*-

import sys
import argparse
import os
import json
import time
import threading
import random
import string
import traceback
import signal
import xml.etree.ElementTree as Et

import pika

import converter.sparql_converter

entities_names_description = converter.sparql_converter.InputVarsNames()
analyzer = converter.sparql_converter.AnalyzerAPIWrapper()
marker_words = converter.sparql_converter.MarkerWords()

query_templates = converter.sparql_converter.QueryTemplates()
prefixes_obj = converter.sparql_converter.Prefixes()


def make_conversion(input_text="",  templates=None, prefixes=None):
    s_time = time.time()

    query_template, query_type, entities_for_query = converter.sparql_converter.select_query_template(
        input_text=input_text, templates=templates)
    print("select template time ", (time.time() - s_time))
    print("query_template", query_template)
    print("entities_for_query", entities_for_query)
    print("query_type", query_type)
    query_set = converter.sparql_converter.form_set_of_special_queries(query_template=query_template,
                                                                       prefixes=prefixes,
                                                                       entities_for_query=entities_for_query,
                                                                       query_type=query_type)
    print("query formation", (time.time() - s_time))

    return query_set


def send_for_exeqution(message):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='ontology_queue')
    channel.basic_publish(exchange='', routing_key='ontology_queue', body=json.dumps(message))
    connection.close()


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='convert_queue')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body.decode("utf-8"))
        message = json.loads(body.decode("utf-8"))
        question_data = message.get("question_data")

        if isinstance(question_data, str):
            question_data = question_data.strip()
        else:
            question_data = ""
        result = make_conversion(input_text=question_data, templates=query_templates, prefixes=prefixes_obj)
        print(result)
        send_for_exeqution({"query_set": result, "convresation_id": message.get("convresation_id"),
                            "task_id": message.get("task_id")})

    channel.basic_consume(queue='convert_queue', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == "__main__":
    print("Sratring")
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

