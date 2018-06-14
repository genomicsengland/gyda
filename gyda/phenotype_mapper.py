""" Takes a phenotype string and returns matching ontology terms - more exact"""
import nltk
from nltk.corpus import wordnet, stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.metrics import jaccard_distance
import pickle
import pandas as pd
import sys
import os
import argparse
import logging
import urllib
import json
import unicodedata
import time

from datetime import datetime
from sys import argv

from gyda.ontologies_dictionary import OntologiesDictionary


class PhenotypeMapper(object):

    def __init__(self, config):
        start = time.time()
        logging.info("Parsing ontologies...")
        ontologies_dict = OntologiesDictionary(config)
        self.ontologies_dataframe = ontologies_dict.ontology_terms
        step1 = time.time()
        logging.info("Ontologies parsed in {}!".format(str(step1-start)))

        logging.info("Initialising natural language toolkit...")
        # make sure nltk packages are installed
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)
        self.stemmer = SnowballStemmer("english", ignore_stopwords=True)    # stemming based in English
        self.stop_words = set(stopwords.words('english'))                   # stop word exclusion from English
        # TODO: use this regex to tokenise also hyphens
        self.tokenizer = RegexpTokenizer(r'\w+')                            # to remove punctuation during tokenisation
        step2 = time.time()
        logging.info("Natural language toolkit initialised in {}!".format(str(step2 - step1)))

        logging.info("Tokenising every ontology term...")
        self.ontologies_dataframe['stem_set'] = self.ontologies_dataframe.name.apply(self.tokenize_and_stem)
        self.ontologies_dataframe['stem_str'] = self.ontologies_dataframe.stem_set.apply(PhenotypeMapper.merge_stem_set)
        step3 = time.time()
        logging.info("Every ontology term tokenised in {}!".format(str(step3 - step2)))

        self.threshold = config.get('threshold', 0.5)


    @staticmethod
    def merge_stem_set(x):
        return " ".join(x)

    @staticmethod
    def normalise_text(text):
        if isinstance(text, unicode):
            unicode_text = text
        else:
            try:
                unicode_text = unicode(text)
            except UnicodeDecodeError:
                unicode_text = unicode(text, 'utf-8')
        return unicodedata.normalize('NFKD', unicode_text).encode('ASCII', 'ignore')

    def tokenize_and_stem(self, text):
        """transform to normal form, tokenize, filter out stop words and stem"""
        try:
            words = self.tokenizer.tokenize(PhenotypeMapper.normalise_text(text))
            stems = set([self.stemmer.stem(w) for w in words if w not in self.stop_words])
        except Exception as ex:
            logging.error("Error tokenising '{}'".format(text))
            raise ex
        return stems

    @staticmethod
    def jaccard_score(stemmed_match, stemmed_target):
        """calculate jaccard distance over dataframe entries"""
        intersection_len = len(stemmed_target.intersection(stemmed_match))
        if intersection_len == 0:
            return 1
        union_len = len(stemmed_target.union(stemmed_match))
        return float(union_len - intersection_len) / union_len

    def fuzzy_search(self, target, stemmed_target):
        """search with stemmed terms using jaccard scores for similarity and filter on threshold"""
        matched_terms = self.ontologies_dataframe.copy()
        matched_terms['score'] = matched_terms.stem_set.apply(PhenotypeMapper.jaccard_score, args=[stemmed_target])
        matched_terms = matched_terms[matched_terms.score <= self.threshold]
        matched_terms['target'] = target
        matched_terms = matched_terms[['target', 'name', 'id', 'primary_name', 'score']]
        matched_terms.score = matched_terms.score.astype(str)
        matched_terms.columns = ['phenotype', 'matched_term_name', 'matched_term_id', 'matched_primary_name', 'score']
        return matched_terms

    def exact_search(self, target, stemmed_target):
        """search with stemmed terms but requiring correct order"""
        stemmed_str = PhenotypeMapper.merge_stem_set(stemmed_target)
        matched_terms = self.ontologies_dataframe[self.ontologies_dataframe.stem_str == stemmed_str]
        matched_terms['target'] = target
        matched_terms['score'] = 'exact'
        matched_terms = matched_terms[['target', 'name', 'id', 'primary_name', 'score']]
        matched_terms.columns = ['phenotype', 'matched_term_name', 'matched_term_id', 'matched_primary_name', 'score']
        return matched_terms

    def reduce_terms(self, df):
        """Eliminate non-specific OMIM/DO terms (ie, for other genes)."""
        # extract phenotype terms as a list
        if df is not None:
            terms = df['phenotype'].unique()
            # set a placeholder for term-specific dataframes ready for concatenation
            reduced = []
            # loop through phenotypes (if more than one)
            for term in terms:
                subdf = df[df['phenotype'] == term]
                # check to see if the pheno is a gene-specific omim/doid-type term
                if term.split(' ')[-1].isdigit():
                    # match the gene-specific entry
                    df1 = subdf[subdf.matched_term_name.str.lower() == term.lower()]
                    # break phenotype term away from number suffix
                    x = subdf.matched_term_name.str.split(' ')
                    prefix = x.str[:-1].tolist()
                    try:
                        prefix = [' '.join(item) for item in prefix]
                    except:
                        print(df1)
                    suffix = x.str[-1].tolist()
                    subdf['term_prefix'] = prefix
                    subdf['term_suffix'] = suffix
                    # add all non-numbered (generic) entries
                    df2 = subdf[~subdf.term_suffix.str.isnumeric()][['phenotype', 'matched_term_name',
                                                                     'matched_term_id', 'matched_primary_name',
                                                                     'score']]
                    # join these two elements together
                    df_part = pd.concat([df1,df2])
                    if df_part.shape[0] > 0:
                        reduced.append(df_part)
                    else:
                        # if no entries match this way, add everything that is available
                        subdf = subdf[['phenotype', 'matched_term_name', 'matched_term_id', 'score']]
                        reduced.append(subdf)
                else:
                    # if the pheno is not gene-specific, add everything that is available
                    df_part = subdf
                    reduced.append(df_part)
            # combine df parts into one df of reduced terms
            if reduced:
                dfred = pd.concat(reduced)
                # sort elements by jaccard score
                dfred = dfred.sort_values(by='score')
            else:
                dfred = pd.DataFrame()
            return dfred
        else:
            return

    def map_phenotypes(self, targets):
        entries = []
        for target in targets:
            # outfile = '_'.join(target.split(' '))+'_ontologies.csv'
            stemmed = self.tokenize_and_stem(target)
            entries.append(self.exact_search(target, stemmed))
            entries.append(self.fuzzy_search(target, stemmed))
            # cleaned_df.to_csv(outfile, sep='\t', header=True, index=False)
            # outfiles.append(outfile)
        mapped_phenotypes = self.reduce_terms(pd.concat(entries).sort_values(by='phenotype'))
        return mapped_phenotypes
