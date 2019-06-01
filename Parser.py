import Product as p
import Review as r
import re
import json
import csv
from struct import *
import Constants as c


def parse(file, dir):

    words_list = list()
    words_indexes_list = list()
    wordid_docid = list()

    with open(file, 'r') as data:
        for line in data.readlines():
            if re.match('^product', line):
                prod = line.split(': ')[1].strip('\n')
            elif re.match('^review/helpfulness', line):
                helpfulness = line.split(': ')[1].strip('\n')
            elif re.match('^review/score', line):
                score = line.split(': ')[1].strip('\n')
            elif re.match('^review/text', line):
                text = line.split(': ')[1].strip('\n')

            elif re.match('^\s*$', line):
                product = p.Product(prod)
                review = r.Review(product.get_product_id(), helpfulness, score, text)

                # delete doubles and add to wordlist.
                words_list.extend(review.get_text())

                # write review to the metadata file
                write_to_metadata(review, dir)

                # set tuples with the words and their docids
                wordid_docid.extend(make_word_docid_tuples(review))

    print('Created Metadata file')
    words_list = remove_duplicates(words_list)
    # append words and indexes to the lists
    wordlist_asa_string = append_to_wordlonglist(words_list, words_indexes_list)
    # write words and indexes to the index file
    write_to_index_file(wordlist_asa_string, words_indexes_list, dir)
    # replace the words with word ids
    wordid_docid = make_wordid_docid_tuples(wordlist_asa_string, words_indexes_list, wordid_docid)

    # create the binary file
    create_binary_file(wordid_docid, dir)


def remove_duplicates(wordlist):
    tmp = set(wordlist)
    return list(tmp)


def print_product(product):
    return "Product:\n" \
           "ID: {0}\n" \
           "helpfulness: {1}\n" \
           "score: {2}\n" \
           "text: {3}\n".format(product.product_id,
                                product.helpfulness,
                                product.score,
                                product.get_text())


def append_to_wordlonglist(text_list, indexes_list):
    """make the long word list and sets the indexes to each word in the indexes list"""
    text_list.sort()

    wordlonglist = ""
    for word in text_list:
        indexes_list.append(len(wordlonglist))
        wordlonglist += word
    return wordlonglist


def write_to_metadata(r, dir):
    """ metadata file """
    with open(dir+'reviews_metadata.csv', 'a', newline='') as metadata:
        writer = csv.writer(metadata, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([r.id, r.product_id, r.helpfulness, r.score])


def write_to_index_file(wordlonglist, words_indexes_list, dir):
    with open(dir+'vocabulary.dat', 'w') as indexfile:
        json_to_file = {
            'words': wordlonglist,
            'indexes': words_indexes_list
        }
        data = json.dumps(json_to_file)
        indexfile.write(data)
        print('Created Index file')


def make_word_docid_tuples(review):
    word_docid = []
    """make tuples of <word, docid>"""
    for word in review.get_text():
        word_docid.append((word, review.id))
    return word_docid


def make_wordid_docid_tuples(words_string, indexes_list, word_docid_tuples):
    wordid_docid = []
    """make tuples of <wordid, docid>"""

    for tup in word_docid_tuples:
        for i in range(len(indexes_list)-2):
            currIndex = indexes_list[i]
            nextIndex = indexes_list[i+1]
            if tup[0] == words_string[currIndex:nextIndex]:
                wordid_docid.append((currIndex, tup[1]))
    return wordid_docid


def get_wordid(tuple):
    return tuple[0]


def get_docid(tuple):
    return tuple[1]


def create_binary_file(wordid_docid, dir):

    wordid_docid = sorted(wordid_docid, key=get_wordid)

    global curr_id, frequency, index_before
    curr_id = 0
    frequency = 0
    index_before = 0
    word_documents = b''

    with open(dir + 'binary.dat', 'ab') as bin:
        # all indexes - all the words
        for item in wordid_docid:
            if not isinstance(item, tuple):
                continue
            wordid, docid = item[0], item[1]

            # set current word
            if wordid != curr_id:
                # make it all one big list:
                to_the_bin = divide_number_to_byets(curr_id)
                to_the_bin += divide_number_to_byets(frequency)
                # write it to the file:
                to_the_bin += word_documents

                bin.write(to_the_bin)
                # reset:
                curr_id = wordid
                frequency = 0
                word_documents = b''
            else:
                frequency += 1
                wordid_docid += divide_number_to_byets(docid)
            # set the id of the last to document to subtract
            index_before = docid
        print("Created binary file")


def divide_number_to_byets(num):
    global res
    # if the docid needs 1 byte 00 in the beginning:
    if num < c.sixbits:
        res = pack('h', num)
    # if the docid needs 2 bytes (more than 6 bits, 01 in the beginning):
    elif c.sixbits <= num < c.sixbitsonebyte:
        byte1 = int(64 + num / c.bytesize)
        byte2 = num % c.bytesize
        res = pack('hh', byte1, byte2)
    # if the docid needs 3 bytes (more than 14 bits, 10 in the beginning):
    elif c.sixbitsonebyte <= num < c.sixbits2bytes:
        byte1 = int.from_bytes(b'\x80', 'big') + int(num / c.bytesize ** 2)
        byte2 = int((num % c.bytesize) / c.bytesize)
        byte3 = num % c.bytesize
        res = pack('hhh', byte1, byte2, byte3)
    # if the docid needs 4 bytes (more than 22 bits, 11 in the beginning):
    elif c.sixbits2bytes <= num < c.sixbits3bytes:
        byte1 = int.from_bytes(b'y\xc0', 'big') + int(num / (c.bytesize ** 3))
        byte2 = int((num % (c.bytesize ** 3)) / (c.bytesize ** 2))
        byte3 = int((num % (c.bytesize ** 2)) / c.bytesize)
        byte4 = num % c.bytesize
        res = pack('hhhh', byte1, byte2, byte3, byte4)
    return res


# def divide_number_to_byets(num):
#     numlist = []
#     # if the docid needs 1 byte 00 in the beginning:
#     if num < onebyte:
#         numlist.append(num)
#     # if the docid needs 2 bytes (more than 6 bits, 01 in the beginning):
#     elif onebyte <= num < twobytes:
#         numlist.append(int.from_bytes(b'\x40', 'big') + int(num / byte))
#         numlist.append(num % byte)
#     # if the docid needs 3 bytes (more than 14 bits, 10 in the beginning):
#     elif twobytes <= num < threebytes:
#         numlist.append(int.from_bytes(b'\x80', 'big') + int(num / byte ** 2))
#         numlist.append(int((num % byte) / byte))
#         numlist.append(num % byte)
#     # if the docid needs 4 bytes (more than 22 bits, 11 in the beginning):
#     elif threebytes <= num < fourbytes:
#         numlist.append(int.from_bytes(b'y\xc0', 'big') + int(num / (byte ** 3)))
#         numlist.append(int((num % (byte ** 3)) / (byte ** 2)))
#         numlist.append(int((num % (byte ** 2)) / byte))
#         numlist.append(num % byte)
#     return numlist