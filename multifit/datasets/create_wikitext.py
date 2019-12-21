"""
Script to create small and large WikiText datasets from Wikipedia articles in
any language that were downloaded with `prepare_wiki.sh`.
Articles are tokenized using the Moses tokenizer. Articles with least than
100 tokens are removed.
"""
import argparse
from pathlib import Path
import json
import csv
import os
from shutil import copyfile
from collections import Counter
from sacremoses import MosesTokenizer
import pandas as pd

def get_texts(root):
    for dir_ in root.iterdir():
        for wiki_file in dir_.iterdir():
            with open(wiki_file, encoding='utf-8') as f_in:
                for line in f_in:
                    article = json.loads(line)
                    text = article['text']
                    title = article['title']
                    if text.strip() == title:
                        # print('No content continuing...')
                        continue
                    yield {'title':title,'text':text}


def countUnique(filePath):
    cnt = Counter()
    with open(filePath, 'r', encoding='utf-8') as reader:
        for line in reader:
            cnt.update(str(line).strip().split())
    return len(cnt)


def findTotalTokens(root, mt):
    total = 0
    for dir_ in root.iterdir():
        for wiki_file in dir_.iterdir():
            with open(wiki_file, encoding='utf-8') as f_in:
                for line in f_in:
                    article = json.loads(line)
                    text = article['text']
                    title = article['title']
                    if text.strip() == title:
                        continue
                    paragraphs = text.split('\n')
                    for paragraph in paragraphs:
                        tokenized = mt.tokenize(paragraph.strip())
                        token_count = len(tokenized) + 1
                        if token_count>=100:
                            total+=len(tokenized)
    return total


def write_wikitext(file_path, text_iter, mt, num_tokens, mode='w',all_tokens=False):
    total_num_tokens = 0
    i = 0
    count = 0
    ids, titles, texts = [],[],[]
    with open(file_path, mode, encoding='utf-8') as f_out:
        for i, article in enumerate(text_iter):
            text = article['text']
            title = article['title']
            num_tokens_article = 0  # count the number of tokens in an article
            tokenized_paragraphs = []
            paragraphs = text.split('\n')

            for paragraph in paragraphs:
                tokenized = mt.tokenize(paragraph.strip(), return_str=True)
                tokenized_paragraphs.append(tokenized)

                tokens = tokenized.split(' ')  # split on whitespace to keep newlines
                # don't count empty lines
                tokens = [token for token in tokens if token]
                # calculate length based on tokens; add 1 for newline
                num_tokens_article += len(tokens) + 1

            if num_tokens_article < 100:
                # only use articles that have at least 100 tokens
                continue

            f_out.write(f'= {title.strip()} =')
            f_out.write('\n')
            for tokenized in tokenized_paragraphs:
                f_out.write(tokenized + '\n')
            count+=1
            total_num_tokens += num_tokens_article + 1
            if num_tokens is not None and total_num_tokens > num_tokens:
                break
    print('{}. # documents: {:,}. # tokens: {:,}.'.format(file_path, count, total_num_tokens))


def wiki2csv(file_path, text_iter, num_tokens):
    total_num_tokens = 0
    print(f'Writing to {file_path}...')
    i = 0
    with open(file_path, 'w', encoding='utf-8') as csvfile:
        f_out = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for i, text in enumerate(text_iter):
            num_tokens_article = 0  # count the number of tokens in an article
            tokenized_paragraphs = []
            paragraphs = text.split('\n')

            for paragraph in paragraphs:
                tokenized = paragraph.strip()
                tokenized_paragraphs.append(tokenized)

                tokens = tokenized.split(' ')  # split on whitespace to keep newlines
                # don't count empty lines
                tokens = [token for token in tokens if token]

                # calculate length based on tokens; add 1 for newline
                num_tokens_article += len(tokens) + 1

            if num_tokens_article < 100:
                # only use articles that have at least 100 tokens
                continue

            f_out.writerow(['\n'.join(tokenized_paragraphs)])

            total_num_tokens += num_tokens_article + 1
            if num_tokens is not None and total_num_tokens > num_tokens:
                break
            if i % 100000 == 0 and i > 0:
                print('Processed {:,} documents. Total # tokens: {:,}.'.format(i, total_num_tokens))


def get_splits(tokens_size, split):
    split = int(tokens_size*split)
    tokens_size = tokens_size - (2*split)
    return [tokens_size, split, split]


def main(args):
    input_path = Path(args.input)
    output = Path(args.output)
    assert input_path.exists(), f'Error: {input_path} does not exist.'
    output.mkdir(exist_ok=True)

    mt = MosesTokenizer(args.lang)

    tokens_size = args.tokens
    if tokens_size is None:
        tokens_size = findTotalTokens(input_path,mt)
    else:
        tokens_size = int(tokens_size)

    token_nums = get_splits(tokens_size, 0.1)
    text_iter = get_texts(input_path)
    
    wiki_out = output / f'{args.lang}'
    wiki_out.mkdir(exist_ok=True)

    splits = ['train', 'valid', 'test']
    
    print(f"Using Splits - Train: {token_nums[0]}, Valid: {token_nums[1]}, Test: {token_nums[2]}")

    for split, token_num in zip(splits, token_nums):
        wiki_path = wiki_out / f'{args.lang}.wiki.{split}.tokens'
        write_wikitext(wiki_path, text_iter, mt, token_num)
        print()

    for split in splits:
        current_path = wiki_out / f'{args.lang}.wiki.{split}.tokens'
        total = countUnique(current_path)
        print(f"Unique tokens {current_path} - {total}")



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True,
                        help='the directory where the Wikipedia data extracted '
                             'with WikiExtractor.py is located. Consists of '
                             'directories AA, AB, AC, etc.')
    parser.add_argument('-o', '--output', required=True,
                        help='the output directory where the merged Wikipedia '
                             'documents should be saved')
    parser.add_argument('-l', '--lang', required=True,
                        help='the iso code of the language of the Wikipedia '
                             'documents, e.g. en, fr, de, etc.')
    parser.add_argument('-t', '--tokens', required=False, default=None,
                        help='total tokens to be considered while building train,test,valid'
                             '80% will be train, 10% will be test, 10% will be valid of the input')
    args = parser.parse_args()
    main(args)
