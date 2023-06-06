# -*- coding: utf8 -*-

import xml.etree.ElementTree as Et
import json


def execute(morph):
    with open("tree.xml", 'r', encoding='utf-8') as xml_file:
        tree = Et.fromstring((xml_file).read().encode('utf-8').decode('utf-8'))

    out_words = set()
    for i in tree:
        if i.tag.split("}")[-1].lower() == "tree":
            for level in i:
                for position in level:
                    for condition in position:
                        for section in condition:
                            if section.tag == "words_list":
                                for item in section:
                                    tmp_words_list = item.text.split()
                                    for word in tmp_words_list:
                                        out_words.add(word)
                                        p = morph.parse(word)
                                        for form in p:
                                            out_words.add(form.normal_form)
    f_1 = open('tree_entities.json', mode='w', encoding='utf-8')
    f_1.write(json.dumps(list(out_words), ensure_ascii=False, indent=2).encode('utf8').decode())
    f_1.close()
    f_2 = open('converter/tree_entities.json', mode='w', encoding='utf-8')
    f_2.write(json.dumps(list(out_words), ensure_ascii=False, indent=2).encode('utf8').decode())
    f_2.close()



