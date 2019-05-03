import sys
import Product as p
import Review as r
import re


def parse(file):
    reviews = []
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
                reviews.append(review)
                print(print_product(review))
    return reviews


def print_product(product):
    return "Product:\n" \
           "ID: {0}\n" \
           "helpfulness: {1}\n" \
           "score: {2}\n" \
           "text: {3}\n".format(product.product_id,
                                product.helpfulness,
                                product.score,
                                product.get_text())


if __name__ == '__main__':

    file = sys.argv[1]
    parse(file)
