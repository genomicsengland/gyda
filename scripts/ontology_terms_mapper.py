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
    parser.add_argument('-f', '--file', help='a file containing a list of phenotypes', required=False)
    args = parser.parse_args()

    # if --phenotype AND --file flags are included
    if args.phenotype is not None and args.file is not None:
        with open(os.path.join('files',args.file), 'r') as f:
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
    elif args.file is not None:
        # check file actually exists
        #assert os.path.isfile(os.path.join('files',args.file)), 'File not found'
        print(args.file)
        assert os.path.isfile(args.file), 'File not found'
        targets = []
        #with open(os.path.join('files',args.file), 'r') as f:
        with open(args.file, 'r') as f:
            targets = [line.strip() for line in f if len(line.strip()) > 0]
            targets_note = 'Terms to match: '+', '.join(targets)
            logging.info(targets_note)
    else:
        # no flags used
        logging.warning('No valid input provided')
        sys.exit()

    map_ontology(targets)


if __name__ == '__main__':
    main()
