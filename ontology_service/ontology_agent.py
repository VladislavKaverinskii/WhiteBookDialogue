# -*- coding: utf-8 -*-

import argparse
import os
import sys
import json
import time
import threading
import random
import string
import traceback
import xml.etree.ElementTree as Et

import pika
import redis

from query_execution import query_execution



def main():
    r_cursor = redis.Redis(host="localhost", port=6379, db=1)
    ontology_object = query_execution.Ontologies()
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='ontology_queue')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body.decode("utf-8"))
        message = json.loads(body.decode("utf-8"))
        query_set = message.get("query_set")
        if query_set is None:
            query_set = []
        result = query_execution.get_ontilogy_answers_from_qurey_set(query_set=query_set,
                                                                     ontology_object=ontology_object,
                                                                     ontology_endpoint="http://localhost:3030/WhiteBook")
        print(result)
        response = {"convresation_id": message.get("convresation_id"), "task_id": message.get("task_id"),
                    "result": result}
        print(message.get("task_id"))
        if message.get("task_id") is not None:

            r_cursor.set(message.get("task_id"), json.dumps(response, ensure_ascii=False))

    channel.basic_consume(queue='ontology_queue', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == "__main__":
    print("Starting ontology service")
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
