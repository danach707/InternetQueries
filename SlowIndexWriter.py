import shutil
import os
import Parser as p


class SlowIndexWriter:

    def slowWrite(self, inputFile, dir):
        """Given product review data, creates an on disk index
                inputFile is the path to the file containing the review data
                dir is the directory in which all index files will be created
                if the directory does not exist, it should be created"""

        if not os.path.exists(dir):
            os.makedirs(dir)
        p.parse(inputFile, dir)

    def removeIndex(self, dir):
        """Delete all index files by removing the given directory"""
        shutil.rmtree(dir)


if __name__ == '__main__':
    s = SlowIndexWriter()
    s.slowWrite('100utf8.txt', './results/')
    # with open('./results/binary.dat') as f:
    #     print(f.read())
