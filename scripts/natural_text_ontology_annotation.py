#!/usr/bin/env python
import argparse
import logging
import os
import sys

from pkg_resources import get_distribution

from gyda.PhenotypeMappers import ZoomaMapper
from gyda.io.TermMappingResultWriters import TermMappingResultTsvWriter
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
_AVAILABLE_PANEL_TYPES = {PanelAppDiseasesReader.RD_PANEL_TYPE, PanelAppDiseasesReader.CC_PANEL_TYPE}
_AVAILABLE_PANEL_FIELDS = {PanelAppDiseasesReader.NAME_FIELD, PanelAppDiseasesReader.RELEVANT_DISORDERS_FIELD,
                           PanelAppDiseasesReader.PHENOTYPES_FIELD}

# Zooma offers more than these vocabularies. I just set these here since are the ones I am familiar with but this list
# can be extended. Note HPO written explicitly since Zooma API asks for "HP" rather than "HPO" which in my opinion is
# counterintuitive
_AVAILABLE_ZOOMA_VOCABULARIES = {ZoomaMapper.CMPO_NAME.lower(), ZoomaMapper.ORPHANET_NAME.lower(),
                                 ZoomaMapper.EFO_NAME.lower(), ZoomaMapper.CHEBI_NAME.lower(),
                                 ZoomaMapper.DOID_NAME.lower(), ZoomaMapper.NCIT_NAME.lower(), "hpo"}

_CLI_MULTIPLE_FIELD_SEPARATOR = ","

allowed_panel_type_list = []
allowed_panel_field_list = []
allowed_vocabulary_list = []


def _log_software_version():
    logger.info("Running {software_details}".format(software_details=get_distribution("gyda")))


def _parse_params(args):
    logger.info("Parameters {cli_parameters}".format(cli_parameters=str(args)))
    global outfile
    if os.path.exists(os.path.dirname(args.outfile)):
        outfile = args.outfile
    else:
        raise IOError("Please provide valid output path")

    global allowed_panel_type_list
    if args.panel_types is None:
        allowed_panel_type_list = list(_AVAILABLE_PANEL_TYPES)
    else:
        allowed_panel_type_list = [panel_type.lower() for panel_type
                                   in args.panel_types.split(_CLI_MULTIPLE_FIELD_SEPARATOR)]
        if set(allowed_panel_type_list) - _AVAILABLE_PANEL_TYPES:
            raise ValueError("One or more panel types specified is not valid. Please, provide a comma separated list"
                             "of panel types from avavilable types {available_panel_types}"
                             .format(available_panel_types=str(_AVAILABLE_PANEL_TYPES)))

    global allowed_panel_field_list
    if args.panel_fields is None:
        allowed_panel_field_list = list(_AVAILABLE_PANEL_FIELDS)
    else:
        allowed_panel_field_list = [panel_field.lower() for panel_field
                                    in args.panel_fields.split(_CLI_MULTIPLE_FIELD_SEPARATOR)]
        if set(allowed_panel_field_list) - _AVAILABLE_PANEL_FIELDS:
            raise ValueError("One or more panel fields specified is not valid. Please, provide a comma separated list"
                             "of panel fields from avavilable fields {available_panel_fields}"
                             .format(available_panel_fields=str(_AVAILABLE_PANEL_FIELDS)))

    global allowed_vocabulary_list
    if args.vocabularies is None:
        allowed_vocabulary_list = None
    else:
        allowed_vocabulary_list = [vocabulary.lower() for vocabulary
                                    in args.vocabularies.split(_CLI_MULTIPLE_FIELD_SEPARATOR)]
        if set(allowed_vocabulary_list) - _AVAILABLE_ZOOMA_VOCABULARIES:
            raise ValueError("One or more vocabularies specified is not valid. Please, provide a comma separated list"
                             "of vocabularies from available options {available_zooma_vocabularies}"
                             .format(available_zooma_vocabularies=str(_AVAILABLE_ZOOMA_VOCABULARIES)))

        # Zooma API uses "hp" rather than "hpo". I changed it for the CLI since seems counterintuitive. Needs
        # translation before passing it over to the ZoomaMapper
        if "hpo" in allowed_vocabulary_list:
            allowed_vocabulary_list.remove("hpo")
            allowed_vocabulary_list.append(ZoomaMapper.HPO_NAME)


def _get_trait_reader():
    return PanelAppDiseasesReader(allowed_panel_type_list, allowed_panel_field_list)


def _get_phenotype_mapper():
    global allowed_vocabulary_list
    return ZoomaMapper(allowed_vocabulary_list=allowed_vocabulary_list)


def _get_mapping_writer():
    global outfile
    return TermMappingResultTsvWriter(outfile)


def _natural_text_ontology_annotation():
    logger.info("Reading traits...")
    trait_reader = _get_trait_reader()
    trait_reader.open()
    str_set = set([text for text in trait_reader.read() if text])
    trait_reader.close()

    logger.info("Annotating...")
    ontology_annotator = _get_phenotype_mapper()
    mapping_result_list = ontology_annotator.run(list(str_set))

    logger.info("Writing results...")
    mapping_writer = _get_mapping_writer()
    mapping_writer.open()
    mapping_writer.pre()
    mapping_writer.write(mapping_result_list)
    mapping_writer.close()


def main():
    """
    command line support for annotating ClinVar phenotypes with ontology terms
    :return:
    """
    parser = argparse.ArgumentParser(description='Text to ontology mapper')
    parser.add_argument('-o', '--outfile', help='file name for csv with results', required=True)
    parser.add_argument('-p', '--panel-types', help='Comma separated list of panel types to consider. Available '
                                                    'options {available_panel_types}'
                        .format(available_panel_types=str(_AVAILABLE_PANEL_TYPES)),
                        required=False,
                        default=None,
                        dest="panel_types")
    parser.add_argument('-f', '--panel-fields', help='Comma separated list of panel fields to read from. Available '
                                                     'options {available_panel_fields}'
                        .format(available_panel_fields=_AVAILABLE_PANEL_FIELDS),
                        required=False,
                        default=None,
                        dest="panel_fields")
    parser.add_argument('-v', '--vocabularies', help='Comma separated list of vocabularies to use. Available '
                                                     'vocabularies for ZOOMA:'
                                                     ' {available_zooma_vocabularies}'
                        .format(available_zooma_vocabularies=_AVAILABLE_ZOOMA_VOCABULARIES),
                        required=False,
                        default=None,
                        dest="vocabularies")
    _log_software_version()
    args = parser.parse_args()
    _parse_params(args)
    _natural_text_ontology_annotation()
    logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Finished <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")


if __name__ == '__main__':
    main()
