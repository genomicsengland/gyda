#!/usr/bin/env python
import argparse
import logging
import os
import sys

from pkg_resources import get_distribution

from gyda.PhenotypeMappers import ZoomaMapper
from gyda.io.TextReaders import PanelAppDiseasesReader

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(threadName)s] %(levelname)s %(module)s:%(lineno)d - %(message)s",
                    datefmt="%Y-%M-%d %H:%M:%S",
                    stream=sys.stderr)
logger = logging.getLogger("gyda")
outfile = None

_SPECIES = 'hsapiens'
_CELLBASE_VERSION = 'v4'
_HOST = 'https://bio-test-cellbase.gel.zone/cellbase'
_CELLBASE_CONFIG = {
    "species": _SPECIES,
    "version": _CELLBASE_VERSION,
    "rest": {
        "hosts": [
            _HOST
        ]
    }
}
_RESULT_FIELD = "result"
_ANNOTATION_FIELD = "annotation"
_TRAIT_ASSOCIATION_FIELD = "traitAssociation"
_HERITABLE_TRAITS_FIELD = "heritableTraits"


def _log_software_version():
    logger.info("Running {software_details}".format(software_details=get_distribution("gyda")))


def _parse_params(args):
    global outfile
    if os.path.exists(os.path.dirname(args.outfile)):
        outfile = args.outfile
    else:
        raise IOError("Please provide valid output path")


def _get_trait_reader():
    return PanelAppDiseasesReader()


def _get_phenotype_mapper():
    return ZoomaMapper()


def _natural_text_ontology_annotation():

    logger.info("Reading traits...")
    trait_reader = _get_trait_reader()
    trait_reader.open()
    str_set = set([text for text in trait_reader.read()])
    trait_reader.close()

    logger.info("Annotating...")
    ontology_annotator = _get_phenotype_mapper()
    mapping_result_list = ontology_annotator.run(list(str_set))

    logger.info("Writing results...")
    mapping_writer = _get_mapping_writer()
    mapping_writer.open()
    mapping_writer.write(mapping_result_list)
    mapping_writer.close()

        if mapping_result_list:
            fdw.write("{text}".format(text=text))
            for annotation_result in mapping_result_list:
                fdw.write("\t{name}\t{id}\n".format(name=annotation_result.term.name, id=annotation_result.term.id))
    fdw.close()



def main():
    """
    command line support for annotating ClinVar phenotypes with ontology terms
    :return:
    """
    parser = argparse.ArgumentParser(description='ClinVar phenotype mapper')
    parser.add_argument('-o', '--outfile', help='file name for csv with results', required=True)
    _log_software_version()
    args = parser.parse_args()
    _parse_params(args)
    _natural_text_ontology_annotation()
    logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Finished <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")


if __name__ == '__main__':
    main()
