import json
import traceback
import csv
import os


class IndexReader:

    def __init__(self, dir):
        """Creates an IndexReader which will read from the given directory"""

        self.metadata_path = dir+"reviews_metadata.csv"
        self.word_to_docs_path = dir + "words_to_file.bin"
        self.vocabulary_path = dir+"vocabulary.dat"

        self.review_id_index = 0
        self.prod_index = 1
        self.helpfulness_index = 2
        self.score_index = 3
        self.num_of_tokens = 4


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
        res = self.get_metadata_item_by_review_id(reviewId, self.prod_index)
        if res is None:
            return -1
        return res

    def getReviewScore(self, reviewId):
        """Returns the score for a given review
        Returns -1 if there is no review with the given identifier"""
        res = self.get_metadata_item_by_review_id(reviewId, self.score_index)
        if res is None:
            return -1
        return res

    def getReviewHelpfulnessNumerator(self, reviewId):
        """Returns the numerator for the helpfulness of a given review
        Returns -1 if there is no review with the given identifier"""
        res = self.get_metadata_item_by_review_id(reviewId, self.helpfulness_index)
        if res is None:
            return -1
        return res.split('/')[0]

    def getReviewHelpfulnessDenominator(self, reviewId):
        """Returns the denominator for the helpfulness of a given review
        Returns -1 if there is no review with the given identifier"""
        res = self.get_metadata_item_by_review_id(reviewId, self.helpfulness_index)
        if res is None:
            return -1
        return res.split('/')[1]

    def getReviewLength(self, reviewId):
        """Returns the number of tokens in a given review
        Returns -1 if there is no review with the given identifier"""
        res = self.get_metadata_item_by_review_id(reviewId, self.num_of_tokens)
        if res is None:
            return -1
        return res

    def getTokenFrequency(self, token):
        """Return the number of reviews containing a given token (i.e., word)
        Returns 0 if there are no reviews containing this token"""

        wordid = self.find_word_in_dictionary(token)
        # word is not in the dictionary
        if wordid == -1:
            print("Token is not in the dictionary")
            return 0

        found, num = 0, 0
        docs = set()
        with open(self.word_to_docs_path, 'rb') as bin:
            while bin.tell() != os.fstat(bin.fileno()).st_size:
                # get wordid:
                wordid_in_file = int.from_bytes(bin.read(4), 'big')
                # get docid:
                docid = int.from_bytes(bin.read(4), 'big')

                if wordid == wordid_in_file:
                    docs.add(docid)
                    found = 1
                if wordid != wordid_in_file and found == 1:
                    break
        return len(docs)

    def getTokenCollectionFrequency(self, token):
        """Return the number of times that a given token (i.e., word) appears in
        the reviews indexed
        Returns 0 if there are no reviews containing this token"""

        wordid = self.find_word_in_dictionary(token)
        # word is not in the dictionary
        if wordid == -1:
            print("Token is not in the dictionary")
            return 0

        found, num = 0, 0
        with open(self.word_to_docs_path, 'rb') as bin:
            while bin.tell() != os.fstat(bin.fileno()).st_size:
                # get wordid:
                wordid_in_file = int.from_bytes(bin.read(4), 'big')
                # get docid:
                int.from_bytes(bin.read(4), 'big')

                if wordid == wordid_in_file:
                    num += 1
                    found = 1
                if wordid != wordid_in_file and found == 1:
                    break
        return num

    def getReviewsWithToken(self, token):
        """Returns a series of integers of the form id-1, freq-1, id-2, freq-2, ... such
        that id-n is the n-th review containing the given token and freq-n is the
        number of times that the token appears in review id-n
        Note that the integers should be sorted by id
        Returns an empty Tuple if there are no reviews containing this token"""

        wordid = self.find_word_in_dictionary(token)
        # word is not in the dictionary
        if wordid == -1:
            print("Token is not in the dictionary")
            return 0

        with open(self.word_to_docs_path, 'rb') as bin:
            tup = dict()
            while bin.tell() != os.fstat(bin.fileno()).st_size:
                # get wordid:
                wordid_in_file = int.from_bytes(bin.read(4), 'big')
                # get docid:
                docid = int.from_bytes(bin.read(4), 'big')

                if wordid_in_file == wordid:
                    if docid in tup:
                        tup[docid] += 1
                    else:
                        tup[docid] = 1

            tup = sorted(list(tup.items()))
            res = [e for tupl in tup for e in tupl]
            return tuple(res)

    def getNumberOfReviews(self):
        """Return the number of product reviews available in the system"""
        try:
            count = 0
            with open(self.metadata_path, "r", newline='') as metadata:
                mdata = csv.reader(metadata, delimiter=' ', quotechar='|')
                for review_data in mdata:
                    count += 1
                return count
        except Exception:
            print("Cant load metadata file")
            traceback.print_exc()

    def getTokenSizeOfReviews(self):
        """Return the number of tokens in the system
        (Tokens should be counted as many times as they appear)"""
        return os.stat(self.word_to_docs_path).st_size/8

    def getProductReviews(self, productId):
        """Return the ids of the reviews for a given product identifier
        Note that the integers returned should be sorted by id
        Returns an empty Tuple if there are no reviews for this product"""

        res = self.get_metadata_item_by_product_id(productId, self.review_id_index)
        if res is None:
            return ()
        return tuple(sorted(res))

    def get_metadata_item_by_review_id(self, reviewId, index):
        try:
            with open(self.metadata_path, "r", newline='') as metadata:
                mdata = csv.reader(metadata, delimiter=' ', quotechar='|')
                for review_data in mdata:
                    if review_data[0] == str(reviewId):
                        return review_data[index]
        except Exception:
            print("Cant load metadata file")
            traceback.print_exc()

    def get_metadata_item_by_product_id(self, prodId, index):
        try:
            with open(self.metadata_path, "r", newline='') as metadata:
                mdata = csv.reader(metadata, delimiter=' ', quotechar='|')
                res = ()
                for review_data in mdata:
                    if review_data[self.prod_index] == prodId:
                        res = res + (review_data[index],)
                return res
        except Exception:
            print("Cant load metadata file")
            traceback.print_exc()

    def find_word_in_dictionary(self, word):
        for i in range(len(self.word_indexes)-2):
            currIndex = self.word_indexes[i]
            nextIndex = self.word_indexes[i+1]
            if word == self.vocabulary[currIndex:nextIndex]:
                return currIndex
        return -1

