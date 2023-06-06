# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.response import SimpleTemplateResponse
from django.views.generic import View
from django.forms import Form
from django.db.models import Q
import json
import copy
import statistics
import pika
import redis

import datetime
import xml.etree.ElementTree as Et
import string
import random
import json
import traceback
import time
from datetime import datetime, timedelta, timezone
from threading import Thread, Lock

from foreign_libraries import morph
from .models import *

import locale
try:
    locale.setlocale(locale.LC_ALL, 'uk_UA')
except:
    pass



r_cursor = redis.Redis(host="localhost", port=6379, db=1)


class ChatbotConstants:
    __instance = None

    def __init__(self):
        if not ChatbotConstants.__instance:
            self.name = ""
            self.conversation_limitation = 1000
            self.garbage_deleting = 100
            self.wait_time = 20.0
            self.answer_comments = {}
            self.greeting_phrases = {}
            self.standard_answers = {}
            self.explanations = {}
            self.dialog_answers = {}
            self.goodbye_phrases = []
            self.db_clean_time = 1000000.0
            self.cache_clean_time = 1000000.0
            self.history_api_password = ""
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="agent_config.xml"):
        if not cls.__instance:
            cls.__instance = ChatbotConstants()
            cls.__instance.config_file = config_file
            with open(config_file, 'r', encoding='utf-8') as xml_file:
                xml_file_data = xml_file.read()
                tree = Et.ElementTree(Et.fromstring(xml_file_data.encode('utf-8').decode('utf-8')))

            root = tree.getroot()
            for i in root:
                if i.tag == "name":
                    cls.__instance.name = i.text.strip()
                elif i.tag == "conversation_limitation":
                    cls.__instance.conversation_limitation = int(i.text.strip())
                elif i.tag == "garbage_deleting":
                    cls.__instance.garbage_deleting = int(i.text.strip())
                elif i.tag == "wait_time":
                    cls.__instance.wait_time = float(i.text.strip())
                elif i.tag == "answers_comments":
                    for comment_type in i:
                        cls.__instance.answer_comments[comment_type.attrib["number"]] = comment_type.text.strip()
                elif i.tag == "greeting_phrases":
                    for phrase in i:
                        cls.__instance.greeting_phrases[phrase.find("case").text.strip()] = phrase.find(
                            "text").text.strip()
                elif i.tag == "standard_answers":
                    for phrase in i:
                        cls.__instance.standard_answers[phrase.find("case").text.strip()] = phrase.find(
                            "text").text.strip()
                elif i.tag == "explanations":
                    for phrase in i:
                        cls.__instance.explanations[phrase.find("case").text.strip()] = phrase.find("text").text.strip()
                elif i.tag == "dialog_answers":
                    for phrase in i:
                        new_answer = {
                                      "answer": phrase.find("answer").text.strip(),
                                      "markers": [marker.text.strip().lower() for marker in phrase.find("markers")
                                                  if phrase.find("markers")]
                                    }
                        cls.__instance.dialog_answers[phrase.find("type").text.strip()] = new_answer
                elif i.tag == "goodbye_phrases":
                    for phrase in i:
                        cls.__instance.goodbye_phrases.append(phrase.text.strip().lower())
                elif i.tag == "db_clean_time":
                    cls.__instance.db_clean_time = float(i.text.strip())
                elif i.tag == "cache_clean_time":
                    cls.__instance.cache_clean_time = float(i.text.strip())
        return cls.__instance


chatbot_config = ChatbotConstants().get_instance(config_file="chatbot_config.xml")
j_text = open('links_dict.json', encoding='utf-8').read()
links_dict = json.loads(j_text, strict=False)


class GetDialogHistory(View):

    def __get_diaog_history__(self, conversation_id=""):
        all_dialog = UserDialogPosition.objects.filter(conversation_id=conversation_id).order_by('date_time')
        full_context = []
        for position in all_dialog:
            current_context = {}
            if position.type == "answer":
                current_context = json.loads(position.content)
                current_context["type"] = "answer"
            elif position.type == "question":
                current_context = {"question": position.content, "type": "question"}
            elif position.type == "additional_answer":
                current_context = json.loads(position.content)
                current_context["type"] = "additional_answer"
            # current_context['date_time'] = position.date_time
            full_context.append(current_context)
        if len(full_context) > 0:
            full_context[-1]["local_link"] = "last_message"
        return full_context

    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")
        if convresation_id is not None:
            context = self.__get_diaog_history__(conversation_id=convresation_id)
        else:
            context = []
        return HttpResponse(json.dumps(context), content_type="application/json")

    def post(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")
        print("convresation_id", convresation_id)
        if convresation_id is not None:
            context = self.__get_diaog_history__(conversation_id=convresation_id)
        else:
            context = []
        return HttpResponse(json.dumps(context), content_type="application/json")


class StartConversation(View):

    def get(self, request, *args, **kwargs):
        # Отобразить стартовую страницу
        return render(request, template_name="index.html")

    def post(self, request, *args, **kwargs):
        # Генерируем ID для нового диалога и сохраняем его в сессии
        convresation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=100))
        request.session["convresation_id"] = convresation_id
        try:
            post_body = json.loads(request.body.decode())
            if "is_webhook" not in post_body:
                request.session.set_expiry(chatbot_config.conversation_limitation)
            elif post_body.get("is_webhook") is not None and not post_body.get("is_webhook"):
                request.session.set_expiry(chatbot_config.conversation_limitation)
            else:
                request.session.set_expiry(10000000) # Практически бесконечная сессия
        except Exception as e:
            request.session.set_expiry(chatbot_config.conversation_limitation)
            print(e)
        context = {"greeting_phrase": chatbot_config.greeting_phrases.get("question"),
                   'convresation_id': convresation_id,
                   "status": True
                   }
        return HttpResponse(json.dumps(context), content_type="application/json")

class ProcessQuestion(View):

    def __clean_text__(self, question_data):
        question_data_cleaned = question_data.strip().strip(".").strip("!").strip("?").strip("-").strip("_").strip("*")
        question_data_cleaned = question_data_cleaned.strip("(").strip(")").strip("[").strip("]").strip(",").strip("#")
        question_data_cleaned = question_data_cleaned.strip("$").strip("%").strip(":").strip(";").strip("\"").strip("'")
        question_data_cleaned = question_data_cleaned.strip("~").strip("`").strip("+").strip("=").strip("\\").strip("/")
        question_data_cleaned = question_data_cleaned.strip(">").strip("<").strip("^").strip("&").strip("@")
        question_data_cleaned = question_data_cleaned.lower()
        return question_data_cleaned

    def __check_standard_answers__(self, question_data):
        question_data_cleaned = self.__clean_text__(question_data)
        for case in chatbot_config.dialog_answers:
            for item in chatbot_config.dialog_answers.get(case).get("markers"):
                if item == question_data_cleaned:
                    return chatbot_config.dialog_answers.get(case).get("answer")
        return None

    def __check_goodbye__(self, question_data):
        question_data_cleaned = self.__clean_text__(question_data)
        for item in chatbot_config.goodbye_phrases:
            if item == question_data_cleaned:
                return True
        return False

    def __get_diaog_history__(self, conversation_id=""):
        all_dialog = UserDialogPosition.objects.filter(conversation_id=conversation_id).order_by('date_time')
        full_context = []
        for position in all_dialog:
            current_context = {}
            if position.type == "answer":
                current_context = json.loads(position.content)
                current_context["type"] = "answer"
            elif position.type == "question":
                current_context = {"question": position.content, "type": "question"}
            elif position.type == "additional_answer":
                current_context = json.loads(position.content)
                current_context["type"] = "additional_answer"
            current_context['date_time'] = position.date_time
            full_context.append(current_context)
        if len(full_context) > 0:
            full_context[-1]["local_link"] = "last_message"
        return full_context

    def __render_additional__(self, form=None, convresation_id=""):
        if form.is_valid():
            try:
                question_key = form.data["question"]
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                db_url_answers = mongo_config.url_base + '://' + mongo_config.admin + ':'
                db_url_answers += mongo_config.password + '@' + mongo_config.db_url

                new_client_answers = motor.motor_asyncio.AsyncIOMotorClient(db_url_answers,
                                                                            io_loop=loop, tls=True,
                                                                            tlsAllowInvalidCertificates=True)
                db_answers = eval('new_client_answers.' + mongo_config.db_name)
                new_collection_answers = eval('db_answers.' + mongo_config.collection_name)
                data = loop.run_until_complete(get_data_from_db(dict_item={"onto_link": question_key},
                                                                mongo_data_base=new_collection_answers))

                context = dict()
                context["primary_answers"] = [{"name": data.get("name"), "content": data.get("content"),
                                               "key": question_key}]
                context["greeting_phrase"] = "Hallo! Hva er du interessert i?"

                UserDialogPosition.objects.create(conversation_id=convresation_id, type="additional_answer",
                                                  content=json.dumps(context, ensure_ascii=False),
                                                  additional_info=json.dumps([])).save()

                formated_time_string = form.data.get("time").replace(",", "").replace(
                    " p.m.", "PM").replace(" a.m.", "AM").replace(" р.", "").strip()

                print(formated_time_string)
                print(datetime.now().__format__('%d %B %Y %H:%M'))
                datetime_object = datetime.strptime(formated_time_string, '%d %B %Y %H:%M')

                datetime_object = datetime_object + timedelta(milliseconds=1000)

                t_object = UserDialogPosition.objects.filter(conversation_id=convresation_id, type="additional_answer",
                                                             content=json.dumps(context, ensure_ascii=False))
                if t_object is None:
                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="additional_answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([]),
                                                      date_time=datetime_object).save()

                all_dialog = UserDialogPosition.objects.filter(conversation_id=convresation_id)

                for position in all_dialog:
                    if position.type == "answer":
                        current_context = json.loads(position.content)
                        if "additional_answers" in current_context:
                            new_additional_answers = []
                            for a_answ in current_context["additional_answers"]:
                                if "key" in a_answ and a_answ.get("key") != question_key:
                                    new_additional_answers.append(a_answ)
                            current_context["additional_answers"] = new_additional_answers
                        position.content = json.dumps(current_context, ensure_ascii=False)
                        position.save(update_fields=['content'])

                context = dict()
                context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")
                context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                return context

            except Exception as e:
                print(e)
                print(traceback.format_exc())

        context = dict()
        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("question")
        context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
        return context

    def get(self, request, *args, **kwargs):
        return redirect("../")

    def post(self, request, *args, **kwargs):
        request.session["quertion_processing"] = True
        convresation_id = request.session.get("convresation_id")
        print(convresation_id)
        if convresation_id is not None:
            print("is_webhook", request.COOKIES.get("is_webhook"))
            if request.COOKIES.get("is_webhook") is None:
                request.session.set_expiry(chatbot_config.conversation_limitation)
            elif request.COOKIES.get("is_webhook"):
                request.session.set_expiry(10000000)
        else:
            print("convresation_id", convresation_id)
            context = {"convresation_id": convresation_id}
            context["status"] = True
            return HttpResponse(json.dumps(context), content_type="application/json")

        form = Form(request.POST or None)
        if not form.is_valid():
            form = Form(json.loads(request.body.decode()) or None)
        print(form.is_valid())
        if form.is_valid():
            try:
                if form.data.get("is_additional") is not None and form.data.get("is_additional") == "True":
                    context = self.__render_additional__(form=form, convresation_id=convresation_id)
                    context["status"] = True
                    context['convresation_id'] = convresation_id
                    return HttpResponse(json.dumps(context), content_type="application/json")

                question_data = form.data.get("question")

                question_data_work = question_data
                if question_data is None or not isinstance(question_data, str) or len(question_data.strip()) == 0:
                    context = dict()
                    context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("wrong_input"),
                                                   "content": "", "comment": ""}]
                    context["additional_answers"] = []
                    context["additional_info_message"] = ""
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("wrong_input")
                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    context = dict()
                    # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("wrong_input")
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    elif request.COOKIES.get("is_webhook"):
                        request.session.set_expiry(10000000)
                    context["status"] = True
                    print("context", context)
                    return HttpResponse(json.dumps(context), content_type="application/json")
                UserDialogPosition.objects.create(conversation_id=convresation_id, type="question",
                                                  content=question_data, additional_info=None).save()
                standard_answer = self.__check_standard_answers__(question_data)
                if standard_answer is None:
                    standard_answer = self.__check_standard_answers__(question_data_work)

                if standard_answer is not None:
                    context = dict()
                    context["primary_answers"] = [
                        {"name": "", "content":standard_answer, "comment": ""}]
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")

                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    # context = dict()
                    # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    elif request.COOKIES.get("is_webhook"):
                        request.session.set_expiry(10000000)
                    context["tech_response"] = "is_standard"
                    context["status"] = True
                    return HttpResponse(json.dumps(context), content_type="application/json")

                if self.__check_goodbye__(question_data):
                    return redirect("../ask_unsubscribe/")

                is_too_long = False
                if len(question_data) > 120:
                    is_too_long = True
                    question_data_tmp = question_data.split()
                    new_question_data = ""
                    counter = 0
                    while len(new_question_data) < 120:
                        if counter < len(question_data_tmp):
                            new_question_data += question_data_tmp[counter]
                        else:
                            break

                print("Setting the task to the converter queue")
                task_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=100))
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host='localhost'))
                channel = connection.channel()
                channel.queue_declare(queue='convert_queue')
                message = {
                    "convresation_id": convresation_id,
                    "task_id": task_id,
                    "question_data": question_data
                }
                channel.basic_publish(exchange='', routing_key='convert_queue', body=json.dumps(message))
                connection.close()

                context = dict()
                context["tech_response"] = "set_into_processing"
                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                elif request.COOKIES.get("is_webhook"):
                    request.session.set_expiry(10000000)
                context["status"] = True
                context["task_id"] = task_id
                context["is_too_long"] = is_too_long
                context["question_data"] = question_data.strip().strip(".").strip("?").strip("!").lower()
                return HttpResponse(json.dumps(context), content_type="application/json")
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                elif request.COOKIES.get("is_webhook"):
                    request.session.set_expiry(10000000)
                context = {"explanation": chatbot_config.explanations.get("error")}
                UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                  content=json.dumps(context, ensure_ascii=False),
                                                  additional_info=json.dumps([])).save()
                return HttpResponse(json.dumps(context), content_type="application/json")


        context = {"explanation": chatbot_config.explanations.get("validation_failure")}
        UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                          content=json.dumps(context, ensure_ascii=False),
                                          additional_info=json.dumps([])).save()
        if request.COOKIES.get("is_webhook") is None:
            request.session.set_expiry(chatbot_config.conversation_limitation)
        elif request.COOKIES.get("is_webhook"):
            request.session.set_expiry(10000000)
        return HttpResponse(json.dumps(context), content_type="application/json")


class GetFinalAnswer(View):

    def recover_digits(self, input_text):
        return input_text.replace("_one_", "1").replace("_two_", "2").replace("_thre_", "3").replace(
            "_four_", "4").replace("_five_", "5").replace("_six_", "6").replace("_seven_", "7").replace(
            "_eight_", "8").replace("_nine_", "9").replace("_zero_", "0")

    def __get_form_answer_context__(self, answer_obj, is_webhook):
        answers_by_level = []
        for level in answer_obj:
            answers_by_sent = []
            for link_obj in level:
                answers = []
                for answer_link in link_obj:
                    images = list()
                    links = list()
                    answer_content = answer_link.get("content")
                    if answer_content is None:
                        answer_content = self.recover_digits(answer_link.get("key")).replace("_comma_", ",").replace(
                            "_apostrof_", "`").replace("_squote_", "'").replace("_dquote_", '"').replace(
                            "_dot_", '.').replace("_lquote_", '«').replace("_rquote_", '»').replace(
                            "_colon_", ':').replace("_dash_", '–').replace("_lbraket_", '(').replace(
                            "_rbraket_", ')').replace("_slash_", '/').replace("__", "-").replace("_", " ")
                    current_name = self.recover_digits(answer_link.get("name")).replace("_comma_", ",").replace(
                        "_apostrof_", "`").replace("_squote_", "'").replace("_dquote_", '"').replace(
                        "_dot_", '.').replace("_lquote_", '«').replace("_rquote_", '»').replace(
                        "_colon_", ':').replace("_dash_", '–').replace("_lbraket_", '(').replace(
                        "_rbraket_", ')').replace("_slash_", '/').replace("__", "-").replace("_", " ")
                    current_additional = answer_link.get("additional")
                    semantic_type = answer_link.get("semantic_type")
                    entities_for_query_tmp = answer_link.get("entities_for_query")
                    metric = answer_link.get("metric")
                    print(metric)
                    # print(111111)
                    is_self_defined = False
                    if current_name.strip().lower() == answer_content.strip().lower():
                        is_self_defined = True
                    # print(2222)
                    entities_for_query = dict()
                    metric_list = list()
                    for i_en in entities_for_query_tmp:
                        if isinstance(entities_for_query_tmp[i_en], tuple) or isinstance(entities_for_query_tmp[i_en],
                                                                                         list):
                            if len(entities_for_query_tmp[i_en]) > 1:
                                metric_list.append(entities_for_query_tmp[i_en][1])
                                entities_for_query_tmp[i_en] = entities_for_query_tmp[i_en][0]
                            elif len(entities_for_query_tmp[i_en]) > 0:
                                entities_for_query_tmp[i_en] = entities_for_query_tmp[i_en][0]
                                metric_list.append(-1.0)
                            else:
                                entities_for_query_tmp[i_en] = ""
                                metric_list.append(-1.0)
                        print()
                        entities_for_query_tmp[i_en] = self.recover_digits(entities_for_query_tmp[i_en])
                        entities_for_query[i_en] = entities_for_query_tmp[i_en].replace(
                            "_comma_", ",").replace("_apostrof_", "`").replace("_squote_", "'").replace(
                            "_dquote_", '"').replace("_dot_", '.').replace("_lquote_", '«').replace(
                            "_rquote_", '»').replace("_colon_", ':').replace("_dash_", '–').replace(
                            "_lbraket_", '(').replace("_rbraket_", ')').replace("_slash_", '/').replace("__",
                                                                                                        "-").replace(
                            "_", " ")
                        if (entities_for_query_tmp[i_en].replace("_comma_", ",").replace("_apostrof_", "`").replace(
                                "_squote_", "'").replace("_dquote_", '"').replace("_dot_", '.').replace(
                            "_lquote_", '«').replace("_rquote_", '»').replace("_colon_", ':').replace("_dash_",
                                                                                                      '–').replace(
                            "_lbraket_", '(').replace("_rbraket_", ')').replace("_slash_", '/').replace("__",
                                                                                                        "-").replace(
                            "_", " ").strip().lower() == answer_content.strip().lower()):
                            is_self_defined = True
                    if is_self_defined:
                        continue

                    if metric is None:
                        try:
                            metric = statistics.mean([float(val) for val in metric_list])
                        except Exception as e:
                            metric = -1.0
                            print(e)

                            # print(33333)
                    used_keyword = list()
                    work_keywords = list()

                    normalized_text = " ".join([morph.parse(word)[0].normal_form
                                                for word in answer_content.strip().lower().split()])
                    for keyword in links_dict:
                        # Строка со словами в начальной форме. Для случаев, если ключ в тексте находится не в начальной форме
                        to_select = False
                        if ((keyword.strip().lower() in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("а") in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("б") in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("в") in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("a") in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("b") in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("c") in answer_content.strip().lower())
                                or (keyword.strip().lower() in current_name.strip().lower())):
                            to_select = True
                        else:
                            if ((keyword.strip().lower() in normalized_text)
                                    or (keyword.strip().lower().rstrip("а") in normalized_text)
                                    or (keyword.strip().lower().rstrip("б") in normalized_text)
                                    or (keyword.strip().lower().rstrip("в") in normalized_text)
                                    or (keyword.strip().lower().rstrip("a") in normalized_text)
                                    or (keyword.strip().lower().rstrip("b") in normalized_text)
                                    or (keyword.strip().lower().rstrip("c") in normalized_text)):
                                to_select = True
                        if to_select:
                            # Отсеивание частичных совпадений
                            key_found = True
                            for keyword_2 in links_dict:
                                if (keyword in keyword_2 and (
                                        len(keyword) < len(keyword_2.rstrip("А").rstrip("Б").rstrip(
                                        "В").rstrip("A").rstrip("B").rstrip("C"))) and
                                        ((answer_content.strip().lower().count(keyword) ==
                                          answer_content.strip().lower().count(keyword_2.rstrip("А").rstrip("Б").rstrip(
                                              "В").rstrip("A").rstrip("B").rstrip("C"))) or
                                         (normalized_text.count(keyword) ==
                                          normalized_text.count(keyword_2.rstrip("А").rstrip("Б").rstrip(
                                              "В").rstrip("A").rstrip("B").rstrip("C"))))):
                                    # print(keyword, keyword_2)
                                    key_found = False
                                    break
                            if key_found:
                                work_keywords.append(keyword)

                    for keyword in work_keywords:
                        print(len(links_dict[keyword]))
                        if len(links_dict[
                                   keyword]) == 1:  # Если ключ однозначный (проверка вхождения в класс не требуется)
                            current_content = links_dict[keyword][0]
                            # print("current_content", current_content)
                            # print(len(current_content) > 1 and current_content[1].strip().lower() not in used_keyword)
                            # print(used_keyword)
                            if len(current_content) > 1 and current_content[1].strip().lower() not in used_keyword:
                                used_keyword.append(keyword.strip().lower())
                                alter_conternt = links_dict.get(current_content[1])
                                # print("current_content[1]", current_content[1])
                                if alter_conternt is None:
                                    used_keyword.append(keyword.strip().lower())
                                    if is_webhook:
                                        link_exists = False
                                        for link in links:
                                            if link["link"].strip() == current_content[0].strip():
                                                link_exists = True
                                                break
                                        if not link_exists:
                                            links.append({
                                                "title": current_content[1],
                                                "link": current_content[0]
                                            })
                                    else:
                                        answer_content += "<br /><br /><a target='_blank' href='" + current_content[
                                            0] + "' >"
                                        answer_content += current_content[1] + "</a>"
                                else:
                                    # print("alter_conternt", alter_conternt)
                                    if len(alter_conternt) == 1:
                                        if is_webhook:
                                            if (current_content[0].split('.')[-1] == "jpg" or
                                                    current_content[0].split('.')[-1] == "png" or
                                                    current_content[0].split('.')[-1] == "bmp"):
                                                image_exists = False
                                                for img in images:
                                                    if img["link"] == current_content[0]:
                                                        image_exists = True
                                                        break
                                                if not image_exists:
                                                    images.append({
                                                        "title": current_content[1],
                                                        "link": current_content[0]
                                                    })
                                            else:
                                                link_exists = False
                                                for link in links:
                                                    if link["link"].strip() == current_content[0].strip():
                                                        link_exists = True
                                                        break
                                                if not link_exists:
                                                    links.append({
                                                        "title": alter_conternt[0][1],
                                                        "link": current_content[0]
                                                    })

                                        else:
                                            answer_content += "<br /><br />" + current_content[1] + " - " + \
                                                              alter_conternt[0][1] + ":<br />"
                                            answer_content += "<a target='_blank' href='" + current_content[0] + "' >"
                                            if current_content[0].split('.')[-1] == "jpg" or \
                                                    current_content[0].split('.')[-1] == "png" or \
                                                    current_content[0].split('.')[-1] == "bmp":
                                                answer_content += "<img src='" + current_content[0] + "' title='" + \
                                                                  current_content[1] + "' /></a>"
                                            else:
                                                answer_content += current_content[1] + "</a>"
                            elif len(links_dict[keyword]) == 1 and keyword not in used_keyword:
                                used_keyword.append(keyword.strip().lower())
                                if is_webhook:
                                    link_exists = False
                                    for link in links:
                                        if link["link"].strip() == current_content[0].strip():
                                            link_exists = True
                                            break
                                    if not link_exists:
                                        links.append({
                                            "title": "Докладна інформація",
                                            "link": current_content[0]
                                        })
                                else:
                                    answer_content += "<br /><br /><a target='_blank' href='" + current_content[
                                        0] + "' >"
                                    answer_content += "Докладна інформація</a>"
                        elif len(links_dict[keyword]) > 1:  # Имеется несколько значений для ключа
                            current_content = []
                            for option in links_dict[keyword]:
                                print(option)
                                option_fit = False
                                if len(option) > 2:
                                    for entity in entities_for_query_tmp:
                                        print("entity", entities_for_query_tmp[entity].lower().strip())
                                        if entities_for_query_tmp[entity].lower().strip() == option[2].lower().strip():
                                            current_content = option
                                            option_fit = True
                                            break
                                print("current_content 2", current_content)
                                if option_fit and len(current_content) > 1 and current_content[
                                    1].strip().lower() not in used_keyword:
                                    used_keyword.append(keyword.strip().lower())
                                    alter_conternt = links_dict.get(current_content[1])
                                    # print("current_content[1]", current_content[1])
                                    if alter_conternt is None:
                                        used_keyword.append(keyword.strip().lower())
                                        if is_webhook:
                                            link_exists = False
                                            for link in links:
                                                if link["link"].strip() == current_content[0].strip():
                                                    link_exists = True
                                                    break
                                            if not link_exists:
                                                links.append({
                                                    "title": current_content[1],
                                                    "link": current_content[0]
                                                })
                                        else:
                                            answer_content += "<br /><br /><a target='_blank' href='" + current_content[
                                                0] + "' >"
                                            answer_content += current_content[1] + "</a>"
                                    else:
                                        # print("alter_conternt", alter_conternt)
                                        if len(alter_conternt) == 1:
                                            if is_webhook:
                                                if current_content[0].split('.')[-1] == "jpg" or \
                                                        current_content[0].split('.')[-1] == "png" or \
                                                        current_content[0].split('.')[-1] == "bmp":
                                                    image_exists = False
                                                    for img in images:
                                                        if img["link"] == current_content[0]:
                                                            image_exists = True
                                                            break
                                                    if not image_exists:
                                                        images.append({
                                                            "title": current_content[1],
                                                            "link": current_content[0]
                                                        })
                                                else:
                                                    link_exists = False
                                                    for link in links:
                                                        if link["link"].strip() == current_content[0].strip():
                                                            link_exists = True
                                                            break
                                                    if not link_exists:
                                                        links.append({
                                                            "title": alter_conternt[0][1],
                                                            "link": current_content[0]
                                                        })

                                            else:
                                                answer_content += "<br /><br />" + current_content[1] + " - " + \
                                                                  alter_conternt[0][1] + ":<br />"
                                                answer_content += "<a target='_blank' href='" + current_content[
                                                    0] + "' >"
                                                if current_content[0].split('.')[-1] == "jpg" or \
                                                        current_content[0].split('.')[-1] == "png" or \
                                                        current_content[0].split('.')[-1] == "bmp":
                                                    answer_content += "<img src='" + current_content[0] + "' title='" + \
                                                                      current_content[1] + "' /></a>"
                                                else:
                                                    answer_content += current_content[1] + "</a>"
                                        elif len(alter_conternt) > 1:
                                            alter_conternt_work = []
                                            for alter_option in alter_conternt:
                                                alter_option_fit = False
                                                if len(alter_option) > 2:
                                                    for entity in entities_for_query_tmp:
                                                        print("entity", entities_for_query_tmp[entity].lower().strip())
                                                        if entities_for_query_tmp[entity].lower().strip() == \
                                                                alter_option[
                                                                    2].lower().strip():
                                                            alter_conternt_work = option
                                                            alter_option_fit = True
                                                            break
                                                if alter_option_fit and len(alter_conternt_work) > 1:
                                                    if is_webhook:
                                                        if current_content[0].split('.')[-1] == "jpg" or \
                                                                current_content[0].split('.')[-1] == "png" or \
                                                                current_content[0].split('.')[-1] == "bmp":
                                                            image_exists = False
                                                            for img in images:
                                                                if img["link"] == current_content[0]:
                                                                    image_exists = True
                                                                    break
                                                            if not image_exists:
                                                                images.append({
                                                                    "title": current_content[1],
                                                                    "link": current_content[0]
                                                                })
                                                        else:
                                                            link_exists = False
                                                            for link in links:
                                                                if link["link"].strip() == current_content[0].strip():
                                                                    link_exists = True
                                                                    break
                                                            if not link_exists:
                                                                links.append({
                                                                    "title": alter_conternt_work[1],
                                                                    "link": current_content[0]
                                                                })

                                                    else:
                                                        answer_content += "<br /><br />" + current_content[1] + " - " + \
                                                                          alter_conternt_work[1] + ":<br />"
                                                        answer_content += "<a target='_blank' href='" + current_content[
                                                            0] + "' >"
                                                        if current_content[0].split('.')[-1] == "jpg" or \
                                                                current_content[0].split('.')[-1] == "png" or \
                                                                current_content[0].split('.')[-1] == "bmp":
                                                            answer_content += "<img src='" + current_content[
                                                                0] + "' title='" + \
                                                                              current_content[1] + "' /></a>"
                                                        else:
                                                            answer_content += current_content[1] + "</a>"

                    if is_webhook:
                        answer = {"name": current_name, "content": answer_content, "semantic_type": semantic_type,
                                  "entities_for_query": entities_for_query, "additional": current_additional,
                                  "links": links, "images": images, "metrica": metric}
                    else:
                        answer = {"name": current_name, "content": answer_content, "semantic_type": semantic_type,
                                  "entities_for_query": entities_for_query, "additional": current_additional,
                                  "metrica": metric}
                    answers.append(answer)

                print("answers: ", answers)
                answers_by_sent.append(answers)
            answers_by_level.append(answers_by_sent)

        primary_answers = []
        additional_answers = []

        '''
        for level_num, level in enumerate(answers_by_level):
            if level_num == 0:
                for st in level:
                    for j in st:
                        primary_answers.append(j)
            else:
                for i in level:
                    additional_answers.append(i)
        '''
        for level_num, level in enumerate(answers_by_level):
            if level_num == 0:
                primary_answers, additional_answers = self.form_answers_set(level=level,
                                                                            comment_level=0)
            else:
                if len(primary_answers) < 1:
                    primary_answers, additional_answers = self.form_answers_set(level=level,

                                                                                comment_level=level_num)
                else:
                    new_additional_answers_1, new_additional_answers_2 = \
                        self.form_answers_set(level=level, comment_level=level_num)
                    additional_answers += new_additional_answers_1 + new_additional_answers_2

        context = dict()
        context["primary_answers"] = primary_answers
        for ans in additional_answers:
            if "metrica" not in ans:
                ans["metrica"] = 0.0
        if len(additional_answers) > 10:
            sorted_additional = sorted(additional_answers, key=lambda answ: answ.get("metrica"), reverse=True)
            context["additional_answers"] = sorted_additional[:5]
            context["additional_answers"] += random.sample(sorted_additional[5:], 5)
        else:
            context["additional_answers"] = additional_answers
        context["additional_info_message"] = chatbot_config.answer_comments["additional_info"]
        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")
        print(context)
        return context, True

    def form_answers_set(self, level=None, comment_level=0):
        main_answers_set = []
        additional_answers_set = []
        print("level ", level)
        if level is not None and len(level) > 0:
            for sent_answer in level:
                if len(sent_answer) == 1:
                    metric = sent_answer[0].get('metrica')
                    if metric is None:
                        metric = -1.0
                    # print ("burum-burum 111", metric, self.__metric_to_level__(float(metric)), comment_level)
                    current_level = 0.4 * self.__metric_to_level__(float(metric)) + 0.6 * comment_level
                    comment = chatbot_config.answer_comments.get(str(int(round(current_level))))
                    if comment is not None:
                        sent_answer[0]["comment"] = comment
                    else:
                        sent_answer[0]["comment"] = ""
                    self.__put_vorbose_comment__(sent_answer[0])
                    main_answers_set.append(sent_answer[0])
                else:
                    for answer in sent_answer:
                        metric = answer.get('metrica')
                        # print ("burum-burum 222", metric, self.__metric_to_level__(float(metric)), comment_level)
                        # print("semantic_type ", answer.get("semantic_type"))
                        if metric is None:
                            metric = -1.0
                        current_level = 0.4 * self.__metric_to_level__(float(metric)) + 0.6 * comment_level
                        comment = chatbot_config.answer_comments.get(str(int(round(current_level))))
                        answer["comment"] = comment
                        self.__put_vorbose_comment__(answer)
                        main_answers_set.append(answer)
                        print("answer ", answer)
                        print("comment ", comment)
        for ans in additional_answers_set:
            if "metrica" not in ans:
                ans["metrica"] = 0.0
        return main_answers_set, additional_answers_set

    def __put_vorbose_comment__(self, answer_object):
        current_semantic_type = answer_object.get("semantic_type")
        if isinstance(current_semantic_type, str):
            if current_semantic_type.strip() == "count_derivatives":
                if isinstance(answer_object.get("content"), str) and answer_object.get("content").isdigit():
                    main_entity = "названих Вами об'єктів "
                    if ('entities_for_query' in answer_object and
                            isinstance(answer_object.get('entities_for_query'), dict)):
                        if "inputEntity" in answer_object['entities_for_query']:
                            input_entity_list = answer_object['entities_for_query']["inputEntity"].split()
                            new_input_entity_list = list()
                            for word in input_entity_list:
                                p = morph.parse(word)
                                poossible_pos = dict()
                                for frm in p:
                                    poossible_pos[frm.tag.POS] = frm
                                if "NOUN" in poossible_pos and "ADJF" in poossible_pos:
                                    selected_option = poossible_pos["ADJF"]
                                elif "NOUN" in poossible_pos and "VERB" in poossible_pos:
                                    selected_option = poossible_pos["VERB"]
                                else:
                                    selected_option = max(p, key=lambda i: i.score)
                                if (selected_option.tag.POS == "NOUN" or selected_option.tag.POS == "NPRO"
                                        or selected_option.tag.POS == "ADJF"):
                                    if selected_option.tag.case == "nomn" or selected_option.tag.case == "accs":
                                        if selected_option.tag.number == "plur":
                                            new_input_entity_list.append(
                                                selected_option.inflect({'gent', "plur"}).word)
                                        else:
                                            print(selected_option.inflect({'gent'}).word)
                                            new_input_entity_list.append(selected_option.inflect({'gent'}).word)
                                    else:
                                        new_input_entity_list.append(selected_option.word)
                                else:
                                    new_input_entity_list.append(selected_option.word)
                            if len(new_input_entity_list) > 0:
                                main_entity = " ".join(new_input_entity_list)
                            else:
                                main_entity = " ".join([wd.lower() for wd in input_entity_list])

                    if answer_object.get("content").strip() == "0":
                        answer_object["comment"] = "Затруднююсь відповісти..."
                        answer_object["content"] = "Нажаль мені достеменно невідомо про кількість " \
                                                   + main_entity + "."
                    else:
                        answer_object["content"] = "Кількість різновидів " + main_entity + " ствновить: " \
                                                   + answer_object["content"]
            elif current_semantic_type.strip() == "count_chapters":
                answer_object["content"] = "Біла Книга з Фізичної та Реабілітаційної Медицини" \
                                           " (ФРM) в Європі містить " \
                                           + answer_object["content"] + " розділів."

            elif (current_semantic_type.strip().lower() == "linked_classes_down" or
                  current_semantic_type.strip().lower() == "linked_classes_up"):
                main_entity = ""
                if ('entities_for_query' in answer_object and
                        isinstance(answer_object.get('entities_for_query'), dict)):
                    if "inputEntity" in answer_object['entities_for_query'] and answer_object['entities_for_query'][
                        "inputEntity"].strip() != "":
                        main_entity = answer_object['entities_for_query']["inputEntity"].strip()
                if main_entity != "":
                    answer_object["comment"] = 'На жаль, у наявній онтології відсутнє безпсереднє визначення поняття "'
                    answer_object["comment"] += main_entity + '". '
                else:
                    answer_object[
                        "comment"] = 'Нажаль, у наявній онтології відсутнє безпсереднє визначення запитуваного поняття.'
                answer_object["comment"] += "Тим не менш, ми можемо навести ряд пов'язаних з ним сутностей. "
                answer_object["comment"] += "Сподіваємося, що ця інформація буде для Вас корисною."

    def __metric_to_level__(self, metric):
        if metric > 0.75:
            return 0
        if metric > 0.5:
            return 1
        if metric > 0.25:
            return 2
        if metric > 0.0:
            return 3
        if metric > -0.25:
            return 4
        if metric > -0.5:
            return 5
        if metric > -0.75:
            return 6
        return 7

    def post(self, request, *args, **kwargs):
        global r_cursor
        request.session["quertion_processing"] = True
        convresation_id = request.session.get("convresation_id")
        if convresation_id is not None and request.COOKIES.get("is_webhook") is None:
            request.session.set_expiry(chatbot_config.conversation_limitation)
        elif request.COOKIES.get("is_webhook") is not None and request.COOKIES.get("is_webhook"):
            request.session.set_expiry(10000000)

        form = Form(request.POST or None)
        if not form.is_valid():
            try:
                form = Form(json.loads(request.body.decode()) or None)
            except Exception as e:
                print(e)
        # print(form.is_valid())
        if form.is_valid():
            try:
                task_id = form.data.get("task_id")
                is_too_long = form.data.get("is_too_long")
                # print("is_too_long", is_too_long)
                if isinstance(is_too_long, str):
                    if is_too_long.lower().strip() == "false":
                        is_too_long = False
                    else:
                        is_too_long = True

                print("task_id - ", task_id)
                answer_obj = r_cursor.get(task_id)

                print("answer_obj ", answer_obj)

                if answer_obj is None:
                    context = dict()
                    context["tech_response"] = "in_process"
                    context["status"] = True
                    # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    elif request.COOKIES.get("is_webhook"):
                        request.session.set_expiry(10000000)
                    return HttpResponse(json.dumps(context), content_type="application/json")

                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                elif request.COOKIES.get("is_webhook"):
                    request.session.set_expiry(10000000)

                if form.data.get("is_webhook") is not None and form.data.get("is_webhook"):
                    is_webhook = True
                else:
                    is_webhook = False

                answer_obj = r_cursor.get(task_id)
                if answer_obj is not None:
                    answer_obj = json.loads(r_cursor.get(task_id).decode())
                else:
                    answer_obj = list()

                print("answer_obj ", answer_obj)
                try:
                    r_cursor.delete(task_id)
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())

                context, status = self.__get_form_answer_context__(answer_obj.get("result"), is_webhook)

                if (context is not None and len(context) > 0 and "primary_answers" in context
                        and len(context.get("primary_answers")) > 0):
                    if is_too_long:
                        if context.get("primary_answers") is not None and len(context.get("primary_answers")) > 0:
                            if "comment" in context.get("primary_answers")[0]:
                                context["primary_answers"][0][
                                    "comment"] += " Ваше запитання занадто довге. Система призначена для відповіді на прості, зрозумілі запитання. Питання не повинно перевищувати 120 символів. Ваш текст зменшено до зазначеної межі. "
                            else:
                                context["primary_answers"][0][
                                    "comment"] = " Ваше запитання занадто довге. Система призначена для відповіді на прості, зрозумілі запитання. Питання не повинно перевищувати 120 символів. Ваш текст зменшено до зазначеної межі. "

                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    if status and len(context) > 0 and "primary_answers" in context and len(context.get(
                            "primary_answers")) > 0:
                        # context = dict()
                        # context["history"] = full_context - исключили истрию диалогоа из ответа API в данном случае
                        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success").strip()
                        if context["greeting_phrase"] == "":
                            current_greeting_phrase = context.get("primary_answers")[0].get("comment")
                            if isinstance(current_greeting_phrase, str) is not None and current_greeting_phrase.strip() != "":
                                context["greeting_phrase"] = context.get("primary_answers")[0].get("comment")
                                for answ in context["primary_answers"]:
                                    answ["comment"] = ""
                        print("is_too_long", is_too_long)
                        if is_too_long:
                            if "primary_answers" in context:
                                if len(context.get("primary_answers")) > 0 and "comment" in context.get("primary_answers")[0]:
                                    context["primary_answers"][0][
                                        "comment"] += " Ваше запитання занадто довге. Система призначена для відповіді на прості, зрозумілі запитання. Питання не повинно перевищувати 120 символів. Ваш текст зменшено до зазначеної межі. "
                                else:
                                    context["primary_answers"][0][
                                        "comment"] = " Ваше запитання занадто довге. Система призначена для відповіді на прості, зрозумілі запитання. Питання не повинно перевищувати 120 символів. Ваш текст зменшено до зазначеної межі. "
                            elif context.get("primary_answers") is not None and len(context.get("primary_answers")) > 0:
                                context["primary_answers"] = [{
                                                                  "comment": " Ваше запитання занадто довге. Система призначена для відповіді на прості, зрозумілі запитання. Питання не повинно перевищувати 120 символів. Ваш текст зменшено до зазначеної межі. "}]
                        if request.COOKIES.get("is_webhook") is None:
                            request.session.set_expiry(chatbot_config.conversation_limitation)
                        elif request.COOKIES.get("is_webhook"):
                            request.session.set_expiry(10000000)
                        context["status"] = True

                        return HttpResponse(json.dumps(context), content_type="application/json")
                    else:
                        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("no_answer")
                        context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("no_answer"),
                                                       "content": "", "comment": ""}]

                        if is_too_long:
                            if "comment" in context.get("primary_answers")[0]:
                                context["primary_answers"][0][
                                    "comment"] = " Ваше запитання занадто довге. Система призначена для відповіді на прості, зрозумілі запитання. Питання не повинно перевищувати 120 символів. Ваш текст зменшено до зазначеної межі."

                        UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                          content=json.dumps(context, ensure_ascii=False),
                                                          additional_info=json.dumps([])).save()
                        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("no_answer")
                        # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                        if request.COOKIES.get("is_webhook") is None:
                            request.session.set_expiry(chatbot_config.conversation_limitation)
                        elif request.COOKIES.get("is_webhook"):
                            request.session.set_expiry(10000000)
                        context["status"] = True

                        return HttpResponse(json.dumps(context), content_type="application/json")
                else:
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("no_answer")
                    context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("no_answer"),
                                                   "content": "", "comment": ""}]
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    elif request.COOKIES.get("is_webhook"):
                        request.session.set_expiry(10000000)
                    context["status"] = True
                    return HttpResponse(json.dumps(context), content_type="application/json")
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                context = dict()
                context["greeting_phrase"] = chatbot_config.greeting_phrases.get("no_answer")
                context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("no_answer"),
                                               "content": "", "comment": ""}]
                # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                elif request.COOKIES.get("is_webhook"):
                    request.session.set_expiry(10000000)
                context["status"] = True
                return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            context = dict()
            context["greeting_phrase"] = chatbot_config.greeting_phrases.get("no_answer")
            context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("no_answer"),
                                           "content": "", "comment": ""}]
            # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
            if request.COOKIES.get("is_webhook") is None:
                request.session.set_expiry(chatbot_config.conversation_limitation)
            elif request.COOKIES.get("is_webhook"):
                request.session.set_expiry(10000000)
            context["status"] = True
            return HttpResponse(json.dumps(context), content_type="application/json")



class Unsubsrcibe(View):

    def post(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")
        if convresation_id is None:
            return redirect('/')
        if request.COOKIES.get("is_webhook") is None:
            request.session.set_expiry(2)
        elif request.COOKIES.get("is_webhook"):
            request.session.set_expiry(10000000)
        form = Form(request.POST or None)
        if form.is_valid():
            result = form.data.get("result")
            if result is not None:
                try:
                    if result == "False":
                        context = dict()
                        context["primary_answers"] = [{"name": "result evaluation",
                                                       "content": "negative", "comment": ""}]
                        UserDialogPosition.objects.create(conversation_id=convresation_id, type="result_evaluation",
                                                          content=json.dumps(context, ensure_ascii=False),
                                                          additional_info=json.dumps([])).save()
                    else:
                        context = dict()
                        context["primary_answers"] = [{"name": "result evaluation",
                                                       "content": "positive", "comment": ""}]
                        UserDialogPosition.objects.create(conversation_id=convresation_id, type="result_evaluation",
                                                          content=json.dumps(context, ensure_ascii=False),
                                                          additional_info=json.dumps([])).save()
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())
        context = {"status": True}
        return HttpResponse(json.dumps(context), content_type="application/json")

