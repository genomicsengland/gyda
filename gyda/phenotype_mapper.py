""" Takes a phenotype string and returns matching ontology terms """
import pronto
import nltk
from nltk.corpus import wordnet, stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize
from nltk.metrics import jaccard_distance
import pickle
import pandas as pd
import sys
import os
import argparse
import logging


# fix for string encoding in python2
#reload(sys)
#sys.setdefaultencoding('utf-8')

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
# improves the specificty of matches by excluding common words
blacklist = ['syndrome', 'syndromic', 'abnormal', 'abnormality', 'familial', 'phenotype', 'phenotypic']

# load HPO and DO ontology files into Ontology objects
hpo = pronto.Ontology(hpo_file)
do = pronto.Ontology(do_file)

def parse_omim_file():
    """Process OMIM flat file into dictionary"""
    d_omim = {}
    with open(omim_file, 'r') as f:
        # file has a header and a footer that needs to be excluded
        lines = f.readlines()[3:25809]
        for line in lines:
            titles = []
            # skip removed or moved entries - if line.startswith('Caret'):
            if line.startswith('Caret'):
                continue
            else:
                line = line.strip().split('\t')
                #main_title
                titles.append(line[2].split(';')[::2][0])
                #alt_titles
                if len(line) > 3:
                    titles = titles + [x.strip() for x in line[3].split(';') if len(x.strip()) > 0]
                d_omim['OMIM:'+str(line[1])] = titles
    return d_omim

# prepare to combine OMIM data with HPO and DO data
d_omim = parse_omim_file()

#d_snomed = pd.read_csv(snomed_file, sep='\t', header=0, usecols=['conceptId', 'term']).drop_duplicates().groupby('conceptId').term.apply(list).to_dict()
df_snomed = pd.read_csv(snomed_file, sep='\t', header=0, usecols=['conceptId', 'term']).drop_duplicates()
df_snomed['conceptId'] = 'SNOMEDCT:'+df_snomed['conceptId'].astype(str)
d_snomed = df_snomed.groupby('conceptId').term.apply(list).to_dict()


def prepare_onto_dict():
    """Prepare dictionary of combined ontologies."""
    d = {}
    # HPO - from .obo file
    for entry in hpo:
        try:
            hpo_id = entry.id
            # gather main name and any synonyms
            names = [entry.name] + [str(x).split('"')[1] for x in entry.synonyms]
            # loop through names and synonym_ids
            snowballed_names = []
            for name in names:
                words = word_tokenize(name)
                # exclude stop words and blacklisted words
                filtered_name = [stemmer.stem(w) for w in words if w not in stop_words and w not in blacklist]
                snowballed_names.append(filtered_name)
            d[hpo_id] = snowballed_names
        except:
            pass
    # DO - from .obo file
    for entry in do:
        try:
            do_id = entry.id
            # gather main name and any synonyms
            names = [entry.name] + [str(x).split('"')[1] for x in entry.synonyms]
            # loop through names and synonym_ids
            snowballed_names = []
            for name in names:
                words = word_tokenize(name)
                # exclude stop words and blacklisted words
                filtered_name = [stemmer.stem(w) for w in words if w not in stop_words and w not in blacklist]
                snowballed_names.append(filtered_name)
            d[do_id] = snowballed_names
        except:
            pass
    # OMIM - from .txt file (different structure to .obo)
    d_omim = parse_omim_file()
    for key in d_omim:
        try:
            snowballed_names = []
            names = d_omim[key]
            for name in names:
                words = word_tokenize(name)
                # exclude stop words and blacklisted words
                filtered_name = [stemmer.stem(w) for w in words if w not in stop_words and w not in blacklist]
                snowballed_names.append(filtered_name)
            d[key] = snowballed_names
        except:
            pass
    # SNOMED - from .txt file (different structure to .obo)
    for key in d_snomed:
        try:
            snowballed_names = []
            names = d_snomed[key]
            for name in names:
                words = word_tokenize(name)
                # exclude stop words and blacklisted words
                filtered_name = [stemmer.stem(w) for w in words if w not in stop_words and w not in blacklist]
                snowballed_names.append(filtered_name)
            d[key] = snowballed_names
        except:
            pass
    return d


# dictionaries for translating hpo names and ids
hpo_id_to_name = {}
for x in hpo:
    hpo_id_to_name[x.id] = x.name

# dictionaries for translating do names and ids
do_id_to_name = {}
for x in do:
    do_id_to_name[x.id] = x.name

# dictionaries for translating omim names and ids
omim_id_to_name = {}
for key in d_omim:
    omim_id_to_name[key] = d_omim[key][0]

# dictionaries for translating snomed names and ids
snomed_id_to_name = {}
for key in d_snomed:
    snomed_id_to_name[key] = d_snomed[key][0]


def get_name_from_id(id):
    """Translate onto id to name."""
    try:
        name = hpo_id_to_name[id]
        return name
    except Exception:
        pass
    try:
        name = do_id_to_name[id]
        return name
    except Exception:
        pass
    try:
        name = omim_id_to_name[id]
        return name
    except Exception:
        pass
    try:
        name = snomed_id_to_name[id]
        return name
    except:
        pass


# ***** replace with pickle for testing to get speedup *****
#d = prepare_onto_dict()
#pickle.dump(d, open('/Users/matthewwerlock/Documents/ontologies/ont_d.p', 'wb'))
if sys.version_info[0] == 3:
    #d = prepare_onto_dict()
    #pickle.dump(d, open('/Users/matthewwerlock/Documents/ontologies/ont_d_3.p', 'wb'))
    d = pickle.load(open('/Users/matthewwerlock/Documents/ontologies/ont_d_3.p', 'rb'))
#pickle.dump(d, open('/Users/matthewwerlock/Documents/ontologies/ont_d.p', 'wb'))
elif sys.version_info[0] == 2:
    #d = prepare_onto_dict()
    #pickle.dump(d, open('/Users/matthewwerlock/Documents/ontologies/ont_d_2.p', 'wb'))
    d = pickle.load(open('/Users/matthewwerlock/Documents/ontologies/ont_d_2.p', 'rb'))
else:
    print('Check python version')


def get_matched_terms(target):
    """Return a dataframe of matched ontology terms using Jaccard to score."""
    jaccard_scores = []
    # process search term for matching
    words = word_tokenize(target)
    filtered_target = [stemmer.stem(w) for w in words if w not in stop_words and w not in blacklist]
    target_set = set(filtered_target)
    # search ontology dictionary for matches using Jaccard distance
    for key in d.keys():
        for item in d[key]:
            match_set = set(item)
            score = jaccard_distance(target_set, match_set)
            if score <= 0.5:
                matched = [target.strip('\n'), ', '.join(filtered_target),
                ', '.join(list(match_set)), get_name_from_id(key), key, score]
                jaccard_scores.append(matched)
    if len(jaccard_scores) == 0:
        logging.warning('No terms found matching: {}'.format(target))
    else:
        # output to dataframe
        df = pd.DataFrame(jaccard_scores)
        df.columns = ['phenotype', 'phenotype search', 'matched search', 'term', 'id', 'score']
        #df = df[['phenotype','term','id']]
        df = df[['phenotype','term','id', 'score']]
        df = df.drop_duplicates()
        return df


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
                df1 = subdf[subdf.term.str.lower() == term.lower()]
                # break phenotype term away from number suffix
                x = subdf.term.str.split(' ')
                prefix = x.str[:-1].tolist()
                try:
                    prefix = [' '.join(item) for item in prefix]
                except:
                    print(df1)
                suffix = x.str[-1].tolist()
                subdf['term_prefix'] = prefix
                subdf['term_suffix'] = suffix
                # add all non-numbered (generic) entries
                df2 = subdf[~subdf.term_suffix.str.isnumeric()][['phenotype', 'term', 'id', 'score']]
                # join these two elements together
                df_part = pd.concat([df1,df2])
                if df_part.shape[0] > 0:
                    reduced.append(df_part)
                else:
                    # if no entries match this way, add everything that is available
                    subdf = subdf[['phenotype', 'term', 'id', 'score']]
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
    '''match provided terms to ontologies and term files'''
    logging.basicConfig(level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M')
    outfiles = []
    for target_term in targets:
        df = get_matched_terms(target_term)
        cleaned_df = reduce_terms(df)
        if cleaned_df is not None:
            # set outfile name based on search term
            outfile = '_'.join(target_term.split(' '))+'_ontologies.csv'
            outfiles.append(outfile)
            # write to file
            cleaned_df.to_csv(outfile, sep='\t', header=True, index=False)
    logging.info('Files created:')
    for outfile in outfiles:
        logging.info(outfile)
    return


if __name__ == '__main__':
    # for debugging only:
    targets = ['retinitis pigmentosa 5', 'beals syndrome', 'bohring-opitz syndrome']
    targets_note = 'Terms to match: '+', '.join(targets)
    map_ontology(targets)
