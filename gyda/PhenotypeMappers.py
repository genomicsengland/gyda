import json
from abc import abstractmethod
from time import sleep

import requests

from gyda.TermMappingResult import TermMappingResult
from gyda.TermResult import TermResult
from protocols.reports_6_0_0 import StandardPhenotype, Ontology
import logging

logger = logging.getLogger("PhenotypeMappers")


class PhenotypeMapper:

    def __init__(self):
        pass

    @abstractmethod
    def run(self, str_list):
        pass


class ZoomaMapper(PhenotypeMapper):
    _HOST = "https://www.ebi.ac.uk"
    _ONTOLOGIES_QUERY_PARAM = "ontologies"
    _BATCH_SIZE = 200
    _PROPERTY_VALUE_FIELD = "propertyValue"
    _PROPERTY_VALUE_POSITION = 1
    _LABEL_POSITION = 2
    _TERM_ID_POSITION = 5
    _CONFIDENCE_POSITION = 4
    _DATA_FIELD = "data"
    _RESPONSE_FIELD = 'response'
    _NONE = "none"
    _SEPARATOR = ", "
    _READY = "1.0"
    _MISSING_VALUES = {"[UNKNOWN EXPERIMENTS]", "[NO TYPE]", "na", "NA", "N/A", "null", "none", "Did not map"}
    _EMPTY_STRING = ""
    _QUOTES = "\'"
    _SPACE = " "

    _CMPO_PREFIX = "cmpo"
    CMPO_NAME = "CMPO"
    _ORPHANET_PREFIX = "orphanet"
    ORPHANET_NAME = "Orphanet"
    _EFO_PREFIX = "efo"
    EFO_NAME = "EFO"
    _CHEBI_PREFIX = "chebi"
    CHEBI_NAME = "CHEBI"
    _HPO_PREFIX = "hp"
    HPO_NAME = "HPO"
    _DOID_PREFIX = "doid"
    DOID_NAME = "DOID"
    _NCIT_PREFIX = "ncit"
    NCIT_NAME = "NCIT"
    _DID_NOT_MAP = "Did not map"

    def __init__(self, allowed_vocabulary_list=None):
        PhenotypeMapper.__init__(self)
        self._allowed_vocabulary_list = allowed_vocabulary_list
        self._session = requests.Session()
        self._session.headers.update({"Accept-Encoding": "gzip"})
        self._session.headers.update({"Content-type": "application/json"})

    def run(self, str_list):
        mapping_result_list = []
        ndone = 0
        for batch in self._next_batch(str_list):
            request_payload = self._create_request_payload(batch)
            response = self._session.post(url=self._create_submission_url(), data=request_payload)
            self._wait_ready(response)
            response = self._session.get(self._get_result_request_url())

            json_result = self._parse_response(response)
            if response.status_code == 504:  # Gateway timeout
                raise requests.ConnectionError("Timeout querying Zooma server")

            mapping_result_list.extend(self._create_mapping_result_list(json_result))

            ndone += len(batch)
            logger.info("{ndone}/{ntotal} text strings annotated".format(ndone=ndone, ntotal=len(str_list)))
            self._session.cookies.clear()

        return mapping_result_list

    def _next_batch(self, str_list):
        for i in range(0, len(str_list), self._BATCH_SIZE):
            yield str_list[i:i + self._BATCH_SIZE]

    def _create_submission_url(self):
        return "{host}/spot/zooma/v2/api/services/map?json{query_param}" \
            .format(host=self._HOST,
                    query_param=self._get_query_param_string())

    def _get_query_param_string(self):
        query_param_string = self._EMPTY_STRING
        filter_param_dict = {}
        if self._allowed_vocabulary_list:
            filter_param_dict[self._ONTOLOGIES_QUERY_PARAM] = self._allowed_vocabulary_list

        if filter_param_dict:
            query_param_string = "&filter="
            i = 0
            for filter_param, value in filter_param_dict.iteritems():
                if i > 0:
                    query_param_string += ","

                # For lists, python str method will include quotes for string values and will leave an space in between
                # elements of the string - remove these
                query_param_string += "{query_param}:{value}" \
                    .format(query_param=filter_param,
                            value=str(value).replace(self._QUOTES, self._EMPTY_STRING)
                            .replace(self._SPACE, self._EMPTY_STRING))

        return query_param_string

    def _create_request_payload(self, str_list):
        return json.dumps([self._create_payload_dict(string) for string in str_list])

    def _create_payload_dict(self, string):
        return {self._PROPERTY_VALUE_FIELD: string}

    def _create_mapping_result_list(self, json_result):
        term_mapping_result_list = []
        query2term_result_dict = {}
        if json_result and self._DATA_FIELD in json_result:
            for result_dict in json_result[self._DATA_FIELD]:
                term_result = self._parse_term_result(result_dict)
                query = self._get_if_present(result_dict[self._PROPERTY_VALUE_POSITION])
                if term_result is not None and query is not None:
                    if query in query2term_result_dict:
                        query2term_result_dict[query].append(term_result)
                    else:
                        query2term_result_dict[query] = [term_result]

            for query, term_result_list in query2term_result_dict.iteritems():
                term_mapping_result_list \
                    .append(TermMappingResult(query, term_result_list))

        return term_mapping_result_list

    def _get_if_present(self, string):
        if self._is_missing(string):
            return None
        else:
            return string

    def _is_missing(self, string):
        return not string or string in self._MISSING_VALUES

    def _parse_term_result(self, mapping_result_list):

        confidence = self._get_if_present(mapping_result_list[self._CONFIDENCE_POSITION])
        label = self._get_if_present(mapping_result_list[self._LABEL_POSITION])
        term_id = self._get_if_present(mapping_result_list[self._TERM_ID_POSITION])

        if confidence is None or label is None or term_id is None:
            return None

        return TermResult(StandardPhenotype(id=term_id,
                                            name=label,
                                            ontology=self._get_ontology(term_id)), confidence)

        # term_result_list = []
        #
        # label_list_string = self._get_if_present(mapping_result_list[self._LABEL_POSITION])
        # label_list = []
        # if label_list_string is not None:
        #     label_list = label_list_string.split(self._SEPARATOR)
        #
        # confidence = self._get_if_present(mapping_result_list[self._CONFIDENCE_POSITION])
        #
        # term_id_list_string = self._get_if_present(mapping_result_list[self._TERM_ID_POSITION])
        # if term_id_list_string is not None:
        #     term_id_list = term_id_list_string.split(self._SEPARATOR)
        #     if len(term_id_list) != len(label_list):
        #         raise RuntimeError("List of returned labels and list of returned term ids do not have same length. "
        #                            "Please, check. Mapping result: {mapping_result}"
        #                            .format(mapping_result=str(mapping_result_list)))
        #
        #     # Assuming term labels and term ids are in correlative positions
        #     for i, term_id in enumerate(term_id_list):
        #         term_result_list.append(TermResult(StandardPhenotype(id=term_id,
        #                                                              name=label_list[i],
        #                                                              ontology=self._get_ontology(term_id)), confidence))

    def _get_ontology(self, term_id):
        if term_id:
            if term_id.lower().startswith(self._CMPO_PREFIX):
                return Ontology(name=self.CMPO_NAME)
            elif term_id.lower().startswith(self._ORPHANET_PREFIX):
                return Ontology(name=self.ORPHANET_NAME)
            elif term_id.lower().startswith(self._EFO_PREFIX):
                return Ontology(name=self.EFO_NAME)
            elif term_id.lower().startswith(self._CHEBI_PREFIX):
                return Ontology(name=self.CHEBI_NAME)
            elif term_id.lower().startswith(self._HPO_PREFIX):
                return Ontology(name=self.HPO_NAME)
            elif term_id.lower().startswith(self._DOID_PREFIX):
                return Ontology(name=self.DOID_NAME)
            elif term_id.lower().startswith(self._NCIT_PREFIX):
                return Ontology(name=self.NCIT_NAME)

        return None

    def _parse_response(self, response):
        try:
            json_obj = response.json()
            if self._RESPONSE_FIELD in json_obj:
                return json_obj[self._RESPONSE_FIELD]
            else:
                return json_obj
        except ValueError:
            msg = 'Bad JSON format retrieved from server'
            raise ValueError(msg)

    def _wait_ready(self, submission_response):
        self._session.headers.cookies = submission_response.cookies

        response = self._session.get(self._get_status_url())
        while response.content != self._READY:
            logger.info("Batch progress: {batch_progress}".format(batch_progress=response.content))
            sleep(1)
            response = self._session.get(self._get_status_url())

        logger.info("Batch progress: {batch_progress}".format(batch_progress=response.content))

    def _get_status_url(self):
        return "{host}/spot/zooma/v2/api/services/map/status".format(host=self._HOST)

    def _get_result_request_url(self):
        return "{host}/spot/zooma/v2/api/services/map?json".format(host=self._HOST)

# https://www.ebi.ac.uk/spot/zooma/v2/api/services/map?json POST
# Request payload
# [{"propertyValue": "Bright nuclei"}, {"propertyValue": "Agammaglobulinemia 2", "propertyType": "phenotype"},
#  {"propertyValue": "Reduction in IR-induced 53BP1 foci in HeLa cell"},
#  {"propertyValue": "Impaired cell migration with increased protrusive activity", "propertyType": "phenotype"},
#  {"propertyValue": "C57Black/6", "propertyType": "strain"}, {"propertyValue": "nuclei stay close together"},
#  {"propertyValue": "Retinal cone dystrophy 3B", "propertyType": "disease"},
#  {"propertyValue": "segregation problems/chromatin bridges/lagging chromosomes/multiple DNA masses"},
#  {"propertyValue": "Segawa syndrome autosomal recessive", "propertyType": "phenotype"},
#  {"propertyValue": "BRCA1", "propertyType": "gene"},
#  {"propertyValue": "Deafness, autosomal dominant 17", "propertyType": "phenotype"},
#  {"propertyValue": "cooked broccoli", "propertyType": "compound"},
#  {"propertyValue": "Amyloidosis, familial visceral", "propertyType": "phenotype"},
#  {"propertyValue": "Spastic paraplegia 10", "propertyType": "phenotype"},
#  {"propertyValue": "Epilepsy, progressive myoclonic 1B", "propertyType": "phenotype"},
#  {"propertyValue": "Big cells"}, {"propertyValue": "Cardiomyopathy, dilated, 1S", "propertyType": "phenotype"},
#  {"propertyValue": "Long QT syndrome 3/6, digenic", "propertyType": "disease"},
#  {"propertyValue": "Lung adenocarcinoma", "propertyType": "disease state"},
#  {"propertyValue": "doxycycline 130 nanomolar", "propertyType": "compound"},
#  {"propertyValue": "left tibia", "propertyType": "organism part"}, {"propertyValue": "CD4-positive"},
#  {"propertyValue": "cerebellum", "propertyType": "organism part"},
#  {"propertyValue": "hematology traits", "propertyType": "gwas trait"},
#  {"propertyValue": "nifedipine 0.025 micromolar", "propertyType": "compound"},
#  {"propertyValue": "Microtubule clumps"}]

# Alternatively this get call can be used (allows just one text per call) LET'S USE THE POST CALL ABOVE
# https://www.ebi.ac.uk/spot/zooma/v2/api//services/annotate?propertyValue=Bright+nuclei
