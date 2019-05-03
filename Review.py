import re


class Review:

    def __init__(self, product_id, helpfulness, score, text):
        self.product_id = product_id
        self.helpfulness = helpfulness
        self.score = score
        self.__text = text

    def set_text(self, text):
        text = text.lower()
        text = re.compile(r'[\W]').split(text)
        self.__text = list(filter(None, text))
        # print(self.__text)

    def get_text(self):
        return self.__text


if __name__ == '__main__':
    r = Review(1, 'ffff', 33, '')
    r.set_text('I have bought several of the Vitality canned dog food products and have found them all to be of good quality. The product looks more like a stew than a processed meat and it smells better. My Labrador is finicky and she appreciates this product better than most. ')
