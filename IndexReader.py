import json
import traceback
import csv
from struct import *
import Constants as c
import os


class IndexReader:

    def __init__(self, dir):
        """Creates an IndexReader which will read from the given directory"""
        self.metadata_path = dir+"reviews_metadata.csv"
        self.binary_path = dir+"binary.dat"
        self.vocabulary_path = dir+"vocabulary.dat"
        self.prod = 1
        self.helpfulness = 2
        self.score = 3
        self.curr_pos_in_binary = 0

        try:
            with open(self.vocabulary_path, "r") as voc:
                jsondata = voc.read()
                data = json.loads(jsondata)
                self.vocabulary = data["words"]
                self.word_indexes = data["indexes"]
        except Exception:
            print("Cant load vocabulary from: " + self.vocabulary_path)
            traceback.print_exc()
            exit(1)

    def getProductId(self, reviewId):
        """Returns the product identifier for the given review
        Returns null if there is no review with the given identifier"""
        res = self.get_metadata_item(reviewId, self.prod)
        if res is None:
            return -1
        return res

    def getReviewScore(self, reviewId):
        """Returns the score for a given review
        Returns -1 if there is no review with the given identifier"""
        res = self.get_metadata_item(reviewId, self.score)
        if res is None:
            return -1
        return res

    def getReviewHelpfulnessNumerator(self, reviewId):
        """Returns the numerator for the helpfulness of a given review
        Returns -1 if there is no review with the given identifier"""
        res = self.get_metadata_item(reviewId, self.helpfulness)
        if res is None:
            return -1
        return res.split('/')[0]

    def getReviewHelpfulnessDenominator(self, reviewId):
        """Returns the denominator for the helpfulness of a given review
        Returns -1 if there is no review with the given identifier"""
        res = self.get_metadata_item(reviewId, self.helpfulness)
        if res is None:
            return -1
        return res.split('/')[1]

    def getReviewLength(self, reviewId):
        """Returns the number of tokens in a given review
        Returns -1 if there is no review with the given identifier"""

    def getTokenFrequency(self, token):
        """Return the number of reviews containing a given token (i.e., word)
        Returns 0 if there are no reviews containing this token"""
    def getTokenCollectionFrequency(self, token):
        """Return the number of times that a given token (i.e., word) appears in
        the reviews indexed
        Returns 0 if there are no reviews containing this token"""

        wordid = self.find_word_in_dictionary(token)
        # word is not in the dictionary
        if wordid == -1:
            return 0

        with open(self.binary_path, 'rb') as bin:

            def next_number():
                currbyte = bin.read(2)
                if currbyte == b'':
                    return -2
                cb = self.check_byte(currbyte)
                if cb != 0:
                    bytes = bin.read((cb-1)*2)
                    currbyte = currbyte+bytes
                fnum = self.unpack_number(currbyte, cb)
                res = 0
                for num in fnum:
                    res += num
                return res

            # iterate the word ids:
            while bin.tell() != os.fstat(bin.fileno()).st_size:

                # get wordid:
                wordid_in_file = next_number()
                if wordid_in_file == -2:
                    return 0

                # get frequency:
                frequency = next_number()
                if wordid_in_file == -2:
                    return 0

                print("wordid in file:", wordid_in_file, "frequency:", frequency)
                # print("word in file: ", wordid_in_file, "wordid: ", wordid)
                if wordid_in_file == wordid:
                    return frequency

                #go to next wordid:
                for i in range(frequency):
                    next_number()

            return 0

    def getReviewsWithToken(self, token):
        """Returns a series of integers of the form id-1, freq-1, id-2, freq-2, ... such
        that id-n is the n-th review containing the given token and freq-n is the
        number of times that the token appears in review id-n
        Note that the integers should be sorted by id
        Returns an empty Tuple if there are no reviews containing this token"""
    def getNumberOfReviews(self):
        """Return the number of product reviews available in the system"""
    def getTokenSizeOfReviews(self):
        """Return the number of tokens in the system
        (Tokens should be counted as many times as they appear)"""
    def getProductReviews(self, productId):
        """Return the ids of the reviews for a given product identifier
        Note that the integers returned should be sorted by id
        Returns an empty Tuple if there are no reviews for this product"""

    def get_metadata_item(self, reviewId, index):
        try:
            with open(self.metadata_path, "r", newline='') as metadata:
                mdata = csv.reader(metadata, delimiter=' ', quotechar='|')
                for review_data in mdata:
                    if review_data[0] == str(reviewId):
                        return review_data[index]

        except Exception:
            print("Cant load metadata file")
            traceback.print_exc()

    def unpack_number(self, bytes, num_of_bytes):
        if num_of_bytes == 1:
            return unpack('h', bytes)
        elif num_of_bytes == 2:
            return unpack('hh', bytes)
        elif num_of_bytes == 3:
            return unpack('hhh', bytes)
        elif num_of_bytes == 4:
            return unpack('hhhh', bytes)

    def num_of_bytes_left_to_read(self, number):
        if number < c.sixbits:
            return 0
        elif c.sixbits <= number < c.sixbitsonebyte:
            return 1
        elif c.sixbitsonebyte <= number < c.sixbits2bytes:
            return 2
        elif c.sixbits2bytes <= number < c.sixbits3bytes:
            return 3

    def check_byte(self, byte):
        if byte[0] & 128 == 0 and byte[0] & 64 == 0:
            return 1
        if byte[0] & 128 == 0 and byte[0] & 64 == 64:
            return 2
        if byte[0] & 128 == 128 and byte[0] & 64 == 0:
            return 3
        if byte[0] & 128 == 128 and byte[0] & 64 == 64:
            return 4


    def find_word_in_dictionary(self, word):
        for i in range(len(self.word_indexes)-2):
            currIndex = self.word_indexes[i]
            nextIndex = self.word_indexes[i+1]
            if word == self.vocabulary[currIndex:nextIndex]:
                return currIndex
        return -1




if __name__ == '__main__':

    i = IndexReader('./results/')
    print(i.getProductId(23))
    print(i.getReviewScore(23))
    print(i.getReviewHelpfulnessNumerator(50))
    print(i.getReviewHelpfulnessDenominator(50))
    print("num of tokens:", str(i.getTokenCollectionFrequency('i')))
