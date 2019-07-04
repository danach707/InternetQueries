import IndexWriter as iw
import IndexReader as i
import traceback
import csv


if __name__ == '__main__':
    dir = './results/'
    s = iw.IndexWriter()

    s.removeIndex(dir)
    s.removeIndex('./tmp/')

    s.write('1000.txt', dir)

    i = i.IndexReader(dir)
    prod = i.getProductId(4)
    print(prod)
    print('1:', i.getReviewScore(0))
    print('2:', i.getReviewHelpfulnessNumerator(0))
    print('3:', i.getReviewHelpfulnessDenominator(0))
    print("get token frequency:", i.getTokenFrequency('have'))
    print("num of tokens:", str(i.getTokenCollectionFrequency('have')))
    print("token size:", str(i.getTokenSizeOfReviews()))
    print("reviews for tokenid:", i.getProductReviews(prod))
    print("get review length:", i.getReviewLength(0))
    print("get number overviews:", i.getNumberOfReviews())
    print("tuple of files:", i.getReviewsWithToken('100'))
