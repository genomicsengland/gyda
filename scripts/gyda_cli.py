#!/usr/bin/env python
import argparse
import logging
import os
import sys
from gyda.phenotype_mapper import PhenotypeMapper


def main():
    """
    command line support for adding terms directly or from file
    :return:
    """
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    parser = argparse.ArgumentParser(description='Gyda phenotype mapper')
    parser.add_argument('-p', '--phenotype', help='a single input phenotype', required=False)
    parser.add_argument('-i', '--infile', help='a file containing a list of input phenotypes (one phenotype per row)',
                        required=False)
    parser.add_argument('-o', '--outfile', help='file name for csv with results (if not provided results are printed '
                                                'to the standard output)', required=False)
    parser.add_argument('--hpo', help='location of hpo obo file', required=False)
    parser.add_argument('--do', help='location of disease ontology obo file', required=False)
    parser.add_argument('--omim', help='location of OMIM file', required=False)
    parser.add_argument('--snomed', help='location of SNOMEDCT file', required=False)
    parser.add_argument('--panelapp', help='location of PanelApp file', required=False)
    parser.add_argument('--threshold', help='set the threshold for jaccard distance', default=0.5)
    args = parser.parse_args()

    # if --phenotype AND --file flags are included
    if args.phenotype is not None and args.infile is not None:
        with open(os.path.join('files', args.infile), 'r') as f:
            targets = [line.strip() for line in f if len(line.strip()) > 0]
        targets += [args.phenotype]
        logging.info("{} terms to match".format(len(targets)))
    # if only --phenotype flag is used
    elif args.phenotype is not None:
        assert isinstance(args.phenotype, str), 'This is not a string'
        targets = [args.phenotype]
        targets_note = 'Terms to match: '+', '.join(targets)
        logging.info(targets_note)
    # if only --file flag is used
    elif args.infile is not None:
        # check file actually exists
        assert os.path.isfile(args.infile), 'File not found'
        targets = []
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
    config["threshold"] = args.threshold

    mapper = PhenotypeMapper(config)
    df = mapper.map_phenotypes(targets)
    if args.outfile is not None:
        outfile = args.outfile
        df.to_csv(outfile, sep='\t', header=True, index=False)
    else:
        if df.empty:
            print "No results"
        else:
            print(df.to_string())


if __name__ == '__main__':
    main()
