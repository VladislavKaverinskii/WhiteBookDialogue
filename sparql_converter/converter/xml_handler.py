# -*- coding: utf-8 -*-

import xml.etree.ElementTree as et
from xml.etree import ElementTree as etree

class XMLDictEditor:
    def __init__(self, input_file=""):
        self.file = input_file
        self.tree = et.parse(self.file)
        self.root = self.tree.getroot()


    def get_flections(self, lemma):
        for i in self.root:
            if i.tag == "lemmata":
                for j in i:
                    if j.tag == "lemma":
                        if j.find("l").get("t") == lemma:
                            flections = j.findall("f")
                            out = []
                            for f in flections:
                                out.append({"word_form": f.get("t"), "characteristics": [g.get("v") for g in f]})
                            return out
        return []

    def get_list_of_flections(self, lemma):
        return [flection['word_form'] for flection in self.get_flections(lemma) if 'word_form' in flection]


    def modify_lemma(self, old_lemma="", new_lemma="", out_file='output.xml'):
        for i in self.root:
            if i.tag == "lemmata":
                for j in i:
                    if j.tag == "lemma":
                        if j.find("l").get("t") == old_lemma:
                            j.attrib["t"] = new_lemma
                            j.set('updated', 'yes')
                            break
        self.tree.write(out_file, encoding='utf-8')


    def modify_lemma_characteristics(self, lemma="", out_file='output.xml', characteristics=[]):
        for i in self.root:
            if i.tag == "lemmata":
                for j in i:
                    if j.tag == "lemma":
                        if j.find("l").get("t") == lemma:
                            for k in j:
                                if k.tag == "l":
                                    to_remove = [n for n in k if n.tag == "g"]
                                    for item in to_remove:
                                        k.remove(item)
                                    for i in characteristics:
                                        k.append(etree.fromstring('<g v="' + str(i) + '" />'))
        self.tree.write(out_file, encoding='utf-8')


    def modify_flection(self, lemma="", old_flection="", new_flection="", out_file='output.xml'):
        for i in self.root:
            if i.tag == "lemmata":
                for j in i:
                    if j.tag == "lemma":
                        if j.find("l").get("t") == lemma:
                            for k in j:
                                if k.tag == "f" and k.attrib["t"] == old_flection:
                                    k.attrib["t"] = new_flection
                                    break
        self.tree.write(out_file, encoding='utf-8')


    def modify_flection_characteristics(self, lemma="", flection="", characteristics=[], out_file='output.xml'):
        for i in self.root:
            if i.tag == "lemmata":
                for j in i:
                    if j.tag == "lemma":
                        if j.find("l").get("t") == lemma:
                            for k in j:
                                if k.tag == "f" and k.attrib["t"] == flection:
                                    to_remove = [n for n in k if n.tag == "g"]
                                    for item in to_remove:
                                        k.remove(item)
                                    for i in characteristics:
                                        k.append(etree.fromstring('<g v="' + str(i) + '" />'))
                                    break
        self.tree.write(out_file, encoding='utf-8')


    def add_lemma(self, new_lemma="", characteristics=[], out_file='output.xml'):
        for i in self.root:
            if i.tag == "lemmata":
                new_id = max([int(j.get("id")) for j in i]) + 1
                new_lemma_xml = '<lemma id="' + str(new_id) + '" rev="' + str(new_id) + '">'
                new_lemma_xml += '<l t="' + new_lemma + '">'
                for k in characteristics:
                    new_lemma_xml += '<g v="' + str(k) + '" />'
                new_lemma_xml += '</l></lemma>'
                i.append(etree.fromstring(new_lemma_xml))
                break
        self.tree.write(out_file, encoding='utf-8')


    def add_flection(self, lemma="", flection="", characteristics=[], out_file='output.xml'):
        for i in self.root:
            if i.tag == "lemmata":
                for j in i:
                    if j.tag == "lemma":
                        if j.find("l").get("t") == lemma:
                            new_flection_xml = '<f t="' + flection + '">'
                            for k in characteristics:
                                new_flection_xml += '<g v="' + str(k) + '" />'
                            new_flection_xml += '</f>'
                            j.append(etree.fromstring(new_flection_xml))
        self.tree.write(out_file, encoding='utf-8')


my_xml_editor = XMLDictEditor('11_corpus.xml')

print(my_xml_editor.get_flections("шахтовий"))
print(my_xml_editor.get_list_of_flections("шахтовий"))

my_xml_editor.add_lemma(new_lemma="йфсмпнор", characteristics=["NOMN", "anim"], out_file='output.xml')
my_xml_editor.add_flection(lemma="йфсмпнор", flection="йфсмпнорfgавв", characteristics=["masc", "gent"], out_file='output.xml')
my_xml_editor.add_flection(lemma="йфсмпнор", flection="йфсмпнорfgааис", characteristics=["masc", "loct"], out_file='output.xml')


