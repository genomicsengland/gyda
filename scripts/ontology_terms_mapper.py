#!/usr/bin/env python
from gyda.phenotype_mapper import *
import argparse
import logging


def main():
    '''command line support for adding terms directly or from file'''
    logging.basicConfig(level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M')
    parser = argparse.ArgumentParser(description='Gyda phenotype mapper')
    parser.add_argument('-p', '--phenotype', help='a single phenotype', required=False)
    parser.add_argument('-i', '--infile', help='a file containing a list of phenotypes', required=False)
    parser.add_argument('-o', '--outfile', help='file name for csv containing mapped terms', required=True)
    parser.add_argument('--hpo', help='location of hpo obo file', required=False)
    parser.add_argument('--do', help='location of disease ontology obo file', required=False)
    parser.add_argument('--omim', help='location of OMIM file', required=False)
    parser.add_argument('--snomed', help='location of SNOMEDCT file', required=False)
    parser.add_argument('--panelapp', help='location of PanelApp file', required=False)
    args = parser.parse_args()

    # if --phenotype AND --file flags are included
    if args.phenotype is not None and args.infile is not None:
        with open(os.path.join('files',args.infile), 'r') as f:
            targets = [line.strip() for line in f if len(line.strip()) > 0]
        targets += [args.phenotype]
        targets_note = 'Terms to match: '+', '.join(targets)
        logging.info(targets_note)
    # if only --phenotype flag is used
    elif args.phenotype is not None:
        assert isinstance(args.phenotype, str), 'This is not a string'
        targets = [args.phenotype]
        targets_note = 'Terms to match: '+', '.join(targets)
        logging.info(targets_note)
    # if only --file flag is used
    elif args.infile is not None:
        # check file actually exists
        #assert os.path.isfile(os.path.join('files',args.file)), 'File not found'
        assert os.path.isfile(args.infile), 'File not found'
        targets = []
        #with open(os.path.join('files',args.file), 'r') as f:
        with open(args.infile, 'r') as f:
            targets = [line.strip() for line in f if len(line.strip()) > 0]
            targets_note = 'Terms to match: '+', '.join(targets)
            logging.info(targets_note)
    else:
        # no flags used
        logging.warning('No valid input provided')
        sys.exit()


    config = {}
    # ontology files
    config["hpo"] = args.hpo
    config["do"] = args.do
    config["omim"] = args.omim
    config["snomed"] = args.snomed
    config["panelapp"] = args.panelapp

    # jaccard threshold for fuzzy dearch
    config["threshold"] = 0.5

    #hpo_id_set = map_ontology(targets)
    if args.outfile is not None:
        mapper = PhenotypeMapper(config)
        df = mapper.map_phenotypes(targets)
        outfile = args.outfile
    df.to_csv(outfile, sep='\t', header=True, index=False)


if __name__ == '__main__':
    main()
