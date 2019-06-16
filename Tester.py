import IndexWriter as iw
import IndexReader as i


if __name__ == '__main__':
    dir = './results/'
    s = iw.IndexWriter()
    s.removeIndex(dir)
    s.write('1000.txt', dir)
    i = i.IndexReader(dir)
    prod = i.getProductId(23)
    print(prod)
    print(i.getReviewScore(23))
    print(i.getReviewHelpfulnessNumerator(50))
    print(i.getReviewHelpfulnessDenominator(50))
    print("get token frequency:", i.getTokenFrequency('this'))
    print("num of tokens:", str(i.getTokenCollectionFrequency('this')))
    print("token size:", str(i.getTokenSizeOfReviews()))
    print("reviews for tokenid:", i.getProductReviews(prod))
    print("get review length:", i.getReviewLength(23))
    print("get number ofreviews:", i.getNumberOfReviews())
    print("tuple of files:", i.getReviewsWithToken('this'))
