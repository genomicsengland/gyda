from abc import abstractmethod

import requests


class PhenotypeMapper:

    def __init__(self):
        pass

    @abstractmethod
    def run(self, str_list):
        pass


class TermMappingResult(object):
    def __init__(self, query=None, result=None):
        if result is None:
            result = []

        # String containing the original query
        self.query = query

        # Expected to contain a list of PhenotypeMapping objects
        self.result = result


class ZoomaMapper(PhenotypeMapper):
    _HOST = "https://www.ebi.ac.uk/"
    _BATCH_SIZE = 200
    _PROPERTY_VALUE_FIELD = "propertyValue"
    _PROPERTY_VALUE_POSITION = 1
    _LABEL_POSITION = 2
    _TERM_ID_POSITION = 5
    _CONFIDENCE_POSITION = 4
    _DATA_FIELD = "data"
    _UNKNOWN_EXPERIMENTS = "[UNKNOWN EXPERIMENTS]"
    _NO_TYPE = "[NO TYPE]"
    _NA = "na"
    _NULL = "null"
    _NONE = "none"
    _SEPARATOR = ", "

    def __init__(self):
        PhenotypeMapper.__init__(self)
        self._session = requests.Session()

    def run(self, str_list):
        mapping_result_list = []
        for batch in self._next_batch(str_list):
            url = self._create_url()
            request_payload = self._create_request_payload(batch)
            response = self._session.post(url, data=request_payload)

            if response.status_code == 504:  # Gateway timeout
                raise requests.ConnectionError("Timeout querying Zooma server")

            mapping_result_list.extend(self._create_mapping_result_list(response))

        return mapping_result_list

    def _next_batch(self, str_list):
        for i in range(0, len(str_list), self._BATCH_SIZE):
            yield str_list[i:self._BATCH_SIZE]

    def _create_url(self):
        return "{host}/spot/zooma/v2/api/services/map?json".format(host=self._HOST)

    def _create_request_payload(self, str_list):
        return [self._create_payload_dict(string) for string in str_list]

    def _create_payload_dict(self, string):
        return {self._PROPERTY_VALUE_FIELD: string}

    def _create_mapping_result_list(self, response):
        mapping_result_list = []
        if response and self._DATA_FIELD in response:
            for mapping_result_list in response[self._DATA_FIELD]:
                mapping_result_list \
                    .append(TermMappingResult(self
                                              ._get_if_present(mapping_result_list[self._PROPERTY_VALUE_POSITION]),
                                              self._parse_term_mapping(mapping_result_list)))

        return mapping_result_list

    def _get_if_present(self, string):
        if self._is_missing(string):
            return None
        else:
            return string

    def _is_missing(self, string):
        if not string \
                or string == self._UNKNOWN_EXPERIMENTS \
                or string == self._NO_TYPE \
                or string.lower() == self._NA \
                or string.lower() == self._NULL \
                or string.lower() == self._NONE:
            return True
        else:
            return False

    def _parse_term_mapping(self, mapping_result_list):

        label_list_string = self._get_if_present(mapping_result_list[self._LABEL_POSITION])
        label_list = []
        if label_list_string is not None:
            label_list = label_list_string.split(self._SEPARATOR)

        term_id_list_string = self._get_if_present(mapping_result_list[self._TERM_ID_POSITION])
        term_id_list = []
        if term_id_list_string is not None:
            term_id_list = term_id_list_string.split(self._SEPARATOR)

        confidence = self._get_if_present(mapping_result_list[self._CONFIDENCE_POSITION])


        pass

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
