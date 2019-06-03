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

    # create the binary files:
    create_word_to_docs_binary_file(wordid_docid, dir)
    create_doc_to_words_binary_file(wordid_docid, dir)


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


def create_word_to_docs_binary_file(wordid_docid, dir):

    wordid_docid = sorted(wordid_docid, key=get_wordid)

    curr_wordid = wordid_docid[0][0]
    last_wordid = curr_wordid
    line = []
    with open(dir+"words_to_file.bin", 'wb') as bin:

        def write_to_file():
            bin.write(line[0].to_bytes(4, 'big'))
            bin.write(line[1].to_bytes(4, 'big'))
            for i in range(len(line) - 2):
                bin.write(line[i + 2].to_bytes(4, 'big'))

        for item in wordid_docid:
            if not isinstance(item, tuple):
                continue
            wordid, docid = item[0], item[1]

            curr_wordid = wordid
            if curr_wordid != last_wordid and len(line) > 0:
                write_to_file()
                line.clear()
                last_wordid = curr_wordid

            if len(line) == 0:
                line.append(wordid)
                line.append(1)
                line.append(docid)
            else:
                line[1] = line[1] + 1
                line.append(docid)
        write_to_file()
    print("Finished writing the word to docs file")

def create_doc_to_words_binary_file(wordid_docid, dir):

    wordid_docid = sorted(wordid_docid, key=get_docid)

    curr_docid = wordid_docid[0][0]
    last_docid = curr_docid
    line = []
    with open(dir + "file_to_words.bin", 'wb') as bin:

        def write_to_file():
            bin.write(line[0].to_bytes(4, 'big'))
            bin.write(line[1].to_bytes(4, 'big'))
            for i in range(len(line) - 2):
                bin.write(line[i + 2].to_bytes(4, 'big'))

        for item in wordid_docid:
            if not isinstance(item, tuple):
                continue
            wordid, docid = item[0], item[1]

            curr_docid = docid
            if curr_docid != last_docid and len(line) > 0:
                write_to_file()
                line.clear()
                last_docid = curr_docid

            if len(line) == 0:
                line.append(docid)
                line.append(1)
                line.append(wordid)
            else:
                # number of words in file:
                line[1] = line[1] + 1
                line.append(wordid)
        write_to_file()

    print("Finished writing the doc to words file")
