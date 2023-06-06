
import pymorphy2 # отвесает за разбор и генерацию словоформ (падежи, число, род и т. п.)

try:
    from converter.ukr_stemmer3 import UkrainianStemmer  # Для выделения основ
except:
    from ukr_stemmer3 import UkrainianStemmer

from nltk.stem.snowball import SnowballStemmer  # Для выделения основ

class UniStemmer:

    def __init__(self, lang):

        if lang == "russian" or lang == "ru":
            self.stemmer_obj = SnowballStemmer("russian")
            self.lang = "ru"
        elif lang == "ukrainian" or lang == "uk":
            self.stemmer_obj = UkrainianStemmer
            self.lang = "uk"
        else:
            self.stemmer_obj = UkrainianStemmer
            self.lang = lang

    def stem(self, word):
        if self.lang == "ru":
            if isinstance(self.stemmer_obj, SnowballStemmer):
                return self.stemmer_obj.stem(word)
            return ""
        elif self.lang == "uk":
            stemmer_tmp = UkrainianStemmer(word)
            return stemmer_tmp.stem_word()
        return ""


stemmer_obj = UniStemmer("uk")
language = 'uk'


morph = pymorphy2.MorphAnalyzer(lang='uk') # Объект морфологического анализатора весит много, поэтому рекомендуют создать его в программе один раз
                                           # Язык украинский.
                                           # Чтобы украинский язый работал нужно устанавливать пакеты следующим образом:
                                           # pip install -U https://github.com/kmike/pymorphy2/archive/master.zip#egg=pymorphy2
                                           # pip install -U pymorphy2-dicts-uk



def set_language(lang='uk'):
    global morph, stemmer_obj, language
    morph = pymorphy2.MorphAnalyzer(lang=lang)
    if lang == "uk":
        stemmer_obj = UniStemmer(lang)
    language = lang


