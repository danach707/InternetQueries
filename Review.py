import re
import itertools


def set_id_to_0():
    count_id = itertools.count()
    return count_id

class Review:

    id = itertools.count()

    def __init__(self, product_id, helpfulness, score, text):
        self.id = next(Review.id)
        self.product_id = product_id
        self.helpfulness = helpfulness
        self.score = score
        self.__text = ""
        self.set_text(text)

    def set_text(self, text):
        text = text.lower()
        text = re.compile(r'[\W]').split(text)
        self.__text = list(filter(None, text))

    def get_text(self):
        return self.__text

    def delete_text_doubles(self):
        text_no_doubles = set(self.__text)
        text_no_doubles = list(text_no_doubles)
        return text_no_doubles

