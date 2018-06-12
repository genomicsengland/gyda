""" Takes a phenotype string and returns matching ontology terms - more exact"""
import pronto
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

from datetime import datetime
from sys import argv

#start = datetime.now()

# make sure nltk packages are installed
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

# ontology source files
hpo_file = '/Users/matthewwerlock/Documents/ontologies/hp.obo'
do_file = '/Users/matthewwerlock/Documents/ontologies/doid-merged.obo'
omim_file = '/Users/matthewwerlock/Documents/ontologies/mimTitles.txt'
#snomed_file = '/Users/matthewwerlock/Documents/ontologies/sct2_Description_Full-en_INT_20180131.txt' # international
snomed_file = '/Users/matthewwerlock/Documents/ontologies/sct2_Description_Full-en-GB_GB1000000_20180401.txt' # UK version

# for stemming and stopword exclusion
stemmer = SnowballStemmer("english", ignore_stopwords=True)
stop_words = set(stopwords.words('english'))
# to remove punctuation during tokenisation
tokenizer = RegexpTokenizer(r'\w+')

# load HPO and DO ontology files into Ontology objects
hpo = pronto.Ontology(hpo_file)
do = pronto.Ontology(do_file)


def tokenize_and_stem_str(target):
    """tokenize, filter, stem and back to string"""
    words = tokenizer.tokenize(target)
    filtered_target = [stemmer.stem(w) for w in words if w not in stop_words]
    stem_str_target = ' '.join(filtered_target)
    return stem_str_target


def tokenize_and_stem_list(target):
    """tokenize, filter and stem"""
    words = tokenizer.tokenize(target)
    filtered_target = [stemmer.stem(w) for w in words if w not in stop_words]
    return filtered_target


def tokenize_and_stem_set(target):
    """tokenize, filter and stem"""
    words = tokenizer.tokenize(target)
    filtered_target = set([stemmer.stem(w) for w in words if w not in stop_words])
    return filtered_target


def make_set(row):
    """add column of sets of stemmed terms to onto_df"""
    set_list= set(row)
    return set_list


def exact_search(target):
    """search with stemmed terms but requiring correct order"""
    stem_target_str = tokenize_and_stem_str(target)
    df = onto_df[onto_df.stem_str == stem_target_str]
    df['target'] = target
    df['score'] = 'exact'
    df = df[['target', 'name', 'id', 'score']]
    df.columns = ['phenotype', 'matched_term', 'id', 'score']
    return df


def jaccard_scores(row, target):
    """calculate jaccard distance over dataframe entries"""
    target_set = tokenize_and_stem_set(target)
    match_set = row
    score = jaccard_distance(target_set, match_set)
    return score


def fuzzy_search(target):
    """search with stemmed terms using jaccard scores for similarity and filter on threshold"""
    df = onto_df.copy()
    df['score'] = df.stem_set.apply(jaccard_scores, args=[target])
    df = df[df.score <= 0.5]
    df['target'] = target
    df = df[['target', 'name', 'id', 'score']]
    df.score = df.score.astype(str)
    df.columns = ['phenotype', 'matched_term', 'id', 'score']
    return df


def prepare_onto_df():
    """combine ontos into dataframe"""
    onto_dfs = []
    for entry in hpo:
        try:
            hpo_id = entry.id
            # gather main name and any synonyms
            names = [entry.name] + [str(x).split('"')[1] for x in entry.synonyms]
            # loop through names and synonym_ids for orderedmatches
            df = pd.DataFrame()
            df['name'] = names
            df['id'] = hpo_id
            df['primary_name'] = entry.name
            onto_dfs.append(df)
        except:
            pass
    for entry in do:
        try:
            do_id = entry.id
            # gather main name and any synonyms
            names = [entry.name] + [str(x).split('"')[1] for x in entry.synonyms]
            # loop through names and synonym_ids for orderedmatches
            df = pd.DataFrame()
            df['name'] = names
            df['id'] = do_id
            df['primary_name'] = entry.name
            onto_dfs.append(df)
        except:
            pass
    # OMIM - from .txt file (different structure to .obo)
    with open(omim_file, 'r') as f:
        # file has a header and a footer that needs to be excluded
        lines = f.readlines()[3:25809]
        for line in lines:
            try:
                names = []
                # skip removed or moved entries - if line.startswith('Caret'):
                if line.startswith('Caret'):
                    continue
                else:
                    line = line.strip().split('\t')
                    #main_title
                    names.append(line[2].split(';')[::2][0])
                    #alt_titles
                    if len(line) > 3:
                        names = names + [x.strip() for x in line[3].split(';') if len(x.strip()) > 0]
                df = pd.DataFrame()
                df['name'] = names
                df['id'] = 'OMIM:'+str(line[1])
                df['primary_name'] = names[0]
                onto_dfs.append(df)
            except:
                pass
    # SNOMED - from .txt file (different structure to .obo)
    try:
        df= pd.read_csv(snomed_file, sep='\t', header=0, usecols=['conceptId', 'term']).drop_duplicates()
        #rename and rearrange columns
        df['name'] = df.term
        df['id'] = 'SNOMEDCT:'+df['conceptId'].astype(str)
        df['primary_name'] = df.term
        df = df[['name', 'id', 'primary_name']]
        onto_dfs.append(df)
    except:
        pass
    # panelapp - from  dict
    try:
        url = 'https://panelapp.genomicsengland.co.uk/WebServices/list_panels/'
        response = urllib.request.urlopen(url)
        data = json.load(response)
        df = pd.DataFrame()
        # prepare add panelapp data
        panel_ids = []
        panel_names = []
        for panel in data['result']:
            panel_ids.append('PANELAPP:'+panel['Panel_Id'])
            panel_names.append(panel['Name'])
        df['name'] = panel_names
        df['id'] = panel_ids
        df['primary_name'] = panel_names
        onto_dfs.append(df)
    except:
        pass
    onto_df = pd.concat(onto_dfs)
    onto_df = onto_df.drop_duplicates()
    return onto_df


if sys.version_info[0] == 3:
    #onto_df = prepare_onto_df()
    #onto_df['stem_str'] = onto_df.name.apply(tokenize_and_stem_str)
    #onto_df['stem_set'] = onto_df.name.apply(tokenize_and_stem_set)
    #pickle.dump(onto_df, open('/Users/matthewwerlock/Documents/ontologies/df3.p', 'wb'))
    onto_df = pickle.load(open('/Users/matthewwerlock/Documents/ontologies/df3.p', 'rb'))
elif sys.version_info[0] == 2:
    #onto_df = prepare_onto_df()
    #onto_df['stem_str'] = onto_df.name.apply(tokenize_and_stem_str)
    #onto_df['stem_set'] = onto_df.name.apply(tokenize_and_stem_set)
    #pickle.dump(onto_df, open('/Users/matthewwerlock/Documents/ontologies/df2.p', 'wb'))
    onto_df = pickle.load(open('/Users/matthewwerlock/Documents/ontologies/df2.p', 'rb'))
else:
    print('Check python version')


def reduce_terms(df):
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
                df1 = subdf[subdf.matched_term.str.lower() == term.lower()]
                # break phenotype term away from number suffix
                x = subdf.matched_term.str.split(' ')
                prefix = x.str[:-1].tolist()
                try:
                    prefix = [' '.join(item) for item in prefix]
                except:
                    print(df1)
                suffix = x.str[-1].tolist()
                subdf['term_prefix'] = prefix
                subdf['term_suffix'] = suffix
                # add all non-numbered (generic) entries
                df2 = subdf[~subdf.term_suffix.str.isnumeric()][['phenotype', 'matched_term', 'id', 'score']]
                # join these two elements together
                df_part = pd.concat([df1,df2])
                if df_part.shape[0] > 0:
                    reduced.append(df_part)
                else:
                    # if no entries match this way, add everything that is available
                    subdf = subdf[['phenotype', 'matched_term', 'id', 'score']]
                    reduced.append(subdf)
            else:
                # if the pheno is not gene-specific, add everything that is available
                df_part = subdf
                reduced.append(df_part)
        # combine df parts into one df of reduced terms
        dfred = pd.concat(reduced)
        # sort elements by jaccard score
        dfred = dfred.sort_values(by='score')
        return dfred
    else:
        return


def map_ontology(targets):
    logging.basicConfig(level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M')
    #dfs = []
    outfiles = []
    for target in targets:
        outfile = '_'.join(target.split(' '))+'_ontologies.csv'
        dfs = []
        dfs.append(exact_search(target))
        dfs.append(fuzzy_search(target))
        df = pd.concat(dfs).sort_values(by='phenotype')
        cleaned_df = reduce_terms(df)
        cleaned_df.to_csv(outfile, sep='\t', header=True, index=False)
        outfiles.append(outfile)
    logging.info('Files created:')
    for outfile in outfiles:
        logging.info(outfile)
    #cleaned_df.to_csv('more_exact_test_pd_minitest.csv', sep='\t', header=True, index=False)

    #end = datetime.now()

    #print(end-start)


if __name__ == '__main__':
    infile = argv[1]
    targets = pd.read_csv(infile, header=None).iloc[:,0].tolist()
    map_ontology(targets)
