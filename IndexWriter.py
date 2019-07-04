import shutil
import os
import Review as r
import Product as p
import csv
import json
import itertools
import re

buffer_size = 1024

class IndexWriter:

    def write(self, inputFile, dir):
        """Given product review data, creates an on disk index
            inputFile is the path to the file containing the review data
            dir is the directory in which all index files will be created
            if the directory does not exist, it should be created"""
        if not os.path.exists(dir):
            os.makedirs(dir)

        self.output_dir = dir
        tmp_path = './tmp/'
        buffer_name = 'buffer{0}'
        buffer_wordid_name = '%s%s' % (tmp_path, buffer_name)

        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)

        self.parse_metadata_and_vocabulary(inputFile, dir)
        self.parse_for_binary_files(inputFile, buffer_wordid_name)
        self.sort_and_merge_binaries(dir, tmp_path, buffer_name, buffer_wordid_name)

        # delete tmp files and folder:
        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)

    def removeIndex(self, dir):
        """Delete all index files by removing the given directory"""
        if os.path.exists(dir):
            shutil.rmtree(dir)

    # ===================== first parse for the vocabulary ========================

    def parse_metadata_and_vocabulary(self, file, dir):

        words_list = list()
        words_indexes_list = list()

        metadata = open(dir + 'reviews_metadata.csv', 'w', newline='')
        writer = csv.writer(metadata, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        with open(file, 'r', encoding='ISO-8859-1') as data:
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

                    # write review to the metadata file
                    writer.writerow([review.id,
                                     review.product_id,
                                     review.helpfulness,
                                     review.score,
                                     review.num_of_words])

                    words_list.extend(review.get_text_without_doubles())

        # close metadata file
        metadata.close()
        print('Created Metadata file')

        words_list = self.remove_duplicates(words_list)
        # append words and indexes to the lists
        wordlist_asa_string = self.append_to_wordlonglist(words_list, words_indexes_list)
        # write data to vocabulary
        self.write_to_vocabulary(wordlist_asa_string, words_indexes_list, dir)

    # ================== second parse for binary files ===================

    """
    1. while there is still data in input file: read from the input file to a buffer file.
    2. when finished: merge sort each the files.
    3. when there is only one file - stop. 
    """
    def parse_for_binary_files(self, file, buffer_wordid_name):

        curr_docid = itertools.count()
        output_buffer = list()

        i = 0
        self.added_padding = False

        with open(file, 'r', encoding='ISO-8859-1') as data:
            for line in data.readlines():

                if re.match('^review/text', line):
                    text = line.split(': ')[1].strip('\n')
                    text = text.lower()
                    text = re.compile(r'[\W]').split(text)
                    text = list(filter(None, text))

                elif re.match('^\s*$', line):

                    docid = next(curr_docid)

                    # write review to binary:
                    curr_review_tuples = self.make_word_docid_tuples(text, docid)

                    # add <word_id, docid> tuples to the buffer
                    output_buffer.extend(curr_review_tuples)
                    if len(output_buffer) >= buffer_size:
                        self.write_to_tmp_file(output_buffer, buffer_wordid_name.format(i))
                        output_buffer.clear()
                        i += 1

        # write the rest of the buffer:
        if len(output_buffer) > 0:
            self.write_to_tmp_file(output_buffer, buffer_wordid_name.format(i))
        print("Finished to write tmp files")

    def sort_and_merge_binaries(self, dir, tmp_path, buffer_name, buffer_wordid_name):

        tmp_dir_size = len(os.listdir(tmp_path))
        print('dir size:', tmp_dir_size)

        i = 0
        dirnum = 0
        self.last_file = buffer_wordid_name.format(dirnum)
        print(self.last_file)
        while tmp_dir_size > 1:

            if i >= tmp_dir_size:
                print('Finished iteration %d' % tmp_dir_size)
                i = 0
                dirnum = 0
                tmp_dir_size /= 2
                continue

            buffer1int = []
            buffer2int = []

            # read from first file:
            print('file:', buffer_wordid_name.format(i))
            with open(buffer_wordid_name.format(i), 'rb') as bin1:
                while bin1.tell() != os.fstat(bin1.fileno()).st_size:
                    wordid = int.from_bytes(bin1.read(4), 'big')
                    docid = int.from_bytes(bin1.read(4), 'big')
                    buffer1int.append((wordid, docid))

            # get next file:
            next_file = self.nextFile(buffer_name.format(i), './tmp')
            # read from second file:
            if not isinstance(next_file, list):
                next_file = '%s%s' % (tmp_path, next_file)
                with open(next_file, 'rb') as bin2:
                    while bin2.tell() != os.fstat(bin2.fileno()).st_size:
                        wordid = int.from_bytes(bin2.read(4), 'big')
                        docid = int.from_bytes(bin2.read(4), 'big')
                        buffer2int.append((wordid, docid))

            merged_list = self.merge(buffer1int, buffer2int)
            if os.path.isfile(buffer_wordid_name.format(i)):
                os.remove(buffer_wordid_name.format(i))
            if os.path.isfile(buffer_wordid_name.format(i + 1)):
                os.remove(buffer_wordid_name.format(i + 1))
            self.last_file = buffer_wordid_name.format(dirnum)
            self.write_to_tmp_file(merged_list, self.last_file)

            i += 2
            dirnum += 1

        # copy file to the result dir:
        shutil.copyfile(self.last_file, dir + "words_to_file.bin")

        # self.create_word_to_docs_binary_file(bin, self.last_file, self.added_padding)
        print("Finished writing the word to docs file")

    # =========================== Finished Parsing ===============================

    def nextFile(self, filename, directory):
        fileList = os.listdir(directory)
        nextIndex = fileList.index(filename) + 1
        if nextIndex == 0 or nextIndex == len(fileList):
            self.added_padding = True
            return [(0, 0)]
        return fileList[nextIndex]

    # ================= Make tuples and write them to buffer file ================

    def write_to_tmp_file(self, buffer, buffer_wordid_name):
        """ write the <wordid, docid> tuples to a buffer file """

        with open(buffer_wordid_name, 'ab') as bwn:
            wordid_docid = sorted(buffer, key=self.get_wordid)
            for item in wordid_docid:
                bwn.write(item[0].to_bytes(4, 'big'))
                bwn.write(item[1].to_bytes(4, 'big'))
                # bwn.write("%d,%d\n" % (item[0], item[1]))

    def make_word_docid_tuples(self, words, docid):
        """make tuples of <wordid, docid>"""

        wordid_docid = []
        for word in words:
            wordid = self.find_word_in_dictionary(word)
            if wordid != -1:
                wordid_docid.append((wordid, docid))
        return wordid_docid

    def find_word_in_dictionary(self, word):
        """ returns the word id from the dictionary"""

        voc = self.read_vocabulary()
        vocabulary = voc[0]
        word_indexes = voc[1]

        for i in range(len(word_indexes)-2):
            currIndex = word_indexes[i]
            nextIndex = word_indexes[i+1]
            if word == vocabulary[currIndex:nextIndex]:
                return currIndex
        return -1

    # =================== Read vocabulary =================

    def read_vocabulary(self):
        try:
            with open(self.output_dir+'vocabulary.dat', "r") as voc:
                jsondata = voc.read()
                data = json.loads(jsondata)
                return [data["words"], data["indexes"]]

        except Exception:
            print("Cant load vocabulary from: " + self.output_dir+'vocabulary.dat')
            exit(1)

    # ================== Vocabulary File ===================

    def remove_duplicates(self, wordlist):
        tmp = set(wordlist)
        return list(tmp)

    def append_to_wordlonglist(self, text_list, indexes_list):
        """make the long word list and sets the indexes to each word in the indexes list"""
        text_list.sort()

        wordlonglist = ""
        for word in text_list:
            indexes_list.append(len(wordlonglist))
            wordlonglist += word
        return wordlonglist

    def write_to_vocabulary(self, wordlonglist, words_indexes_list, dir):
        with open(dir + 'vocabulary.dat', 'w') as indexfile:
            json_to_file = {
                'words': wordlonglist,
                'indexes': words_indexes_list
            }
            data = json.dumps(json_to_file)
            indexfile.write(data)
            print('Created Index file')

    # ================== Merge Sort ======================

    # Merge the sorted halves
    def merge(self, left_half, right_half):
        res = []
        while len(left_half) != 0 and len(right_half) != 0:
            if left_half[0] < right_half[0]:
                res.append(left_half[0])
                left_half.remove(left_half[0])
            else:
                res.append(right_half[0])
                right_half.remove(right_half[0])
        if len(left_half) == 0:
            res = res + right_half
        else:
            res = res + left_half
        return res

    # ==================== Tuple sort ===================

    def get_wordid(self, tuple):
        return tuple[0]

    def get_docid(self, tuple):
        return tuple[1]

    # ================ Word to docs binary ==================

    def create_word_to_docs_binary_file(self, file_to_write, file_to_read, added_padding):

        with open(file_to_read, 'rb') as fn:

            if added_padding:
                int.from_bytes(fn.read(4), 'big')
                int.from_bytes(fn.read(4), 'big')

            res = []
            curr_wordid = -1
            last_wordid = curr_wordid
            while fn.tell() != os.fstat(fn.fileno()).st_size:

                wordid = int.from_bytes(fn.read(4), 'big')
                docid = int.from_bytes(fn.read(4), 'big')

                if wordid != curr_wordid and curr_wordid != last_wordid:
                    self.add_to_word_to_docs_binary(file_to_write, res)
                    res = []
                    last_wordid = curr_wordid

                curr_wordid = wordid
                res.append((wordid, docid))

    def add_to_word_to_docs_binary(self, bin, wordid_docid):

        curr_wordid = wordid_docid[0][0]
        last_wordid = curr_wordid
        line = []

        # --- inside function ---:
        def write_to_file():
            bin.write(line[0].to_bytes(4, 'big'))
            bin.write(line[1].to_bytes(4, 'big'))
            for i in range(len(line) - 2):
                bin.write(line[i + 2].to_bytes(4, 'big'))
        # -----------------------#

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

