#!/env/python
import argparse
import logging

from gyda.phenotype_mapper import PhenotypeMapper


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Gyda phenotype mapper')
    # parser.add_argument('--cipapi-url', help='The URL for the CIPAPI', required=True)
    # parser.add_argument('--cva-url', help='The URL for CVA', required=True)
    parser.add_argument('--gel-user', help='The user for GEL', required=True)
    # parser.add_argument('--gel-password', help='The password for GEL', required=True)
    # parser.add_argument('--decipher-system-key', help="Decipher's system key", required=True)
    # parser.add_argument('--decipher-user-key', help="Decipher's user key", required=True)
    # parser.add_argument('--decipher-url', help="Decipher's URL", required=True)
    # parser.add_argument('--send-absent-phenotypes', help="Flag to send absent phenotypes", action='store_true')
    args = parser.parse_args()

    config = {
        "gel_user": args.gel_user
    }
    mapper = PhenotypeMapper(config)
    result = mapper.map(["Something"])
    logging.warning(result)


if __name__ == '__main__':
    main()
