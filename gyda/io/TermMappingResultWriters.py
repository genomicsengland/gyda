import gzip
from abc import abstractmethod


class TermMappingResultWriter(object):
    def __init__(self, filename):
        self._filename = filename

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def pre(self):
        pass

    @abstractmethod
    def write(self, term_mapping_result_list):
        pass

    @abstractmethod
    def post(self):
        pass

    @abstractmethod
    def close(self):
        pass


class TermMappingResultTsvWriter(TermMappingResultWriter):
    _TSV_GZ_SUFFIX = "tsv.gz"
    _TSV_SUFFIX = "tsv"
    _EMPTY_STRING = ""
    _NA = "na"
    _NULL = "null"
    _NONE = "none"

    def __init__(self, filename):
        super(TermMappingResultTsvWriter, self).__init__(filename)
        self._fd = None

    def open(self):
        if self._filename.endswith(self._TSV_GZ_SUFFIX):
            self._fd = gzip.open(self._filename, 'wb')
        elif self._filename.endswith(self._TSV_SUFFIX):
            self._fd = open(self._filename, "w")

    def pre(self):
        self._fd.write("Queried text\tTerm name\tTerm id\tMapping confidence\tOntology\n")

    def write(self, term_mapping_result_list):
        for term_mapping_result in term_mapping_result_list:
            for term_result in term_mapping_result.result:
                self._fd.write("{query}\t{term_name}\t{term_id}\t{confidence}\t{ontology}\n"
                               .format(query=term_mapping_result.query.encode('utf-8', errors="ignore"),
                                       term_name=self._get_if_not_missing(term_result.standard_phenotype.name)
                                       .encode('utf-8', errors="ignore"),
                                       term_id=self._get_if_not_missing(term_result.standard_phenotype.id)
                                       .encode('utf-8', errors="ignore"),
                                       confidence=self._get_if_not_missing(term_result.confidence)
                                       .encode('utf-8', errors="ignore"),
                                       ontology=self._get_ontology_name(term_result.standard_phenotype.ontology)))

    def post(self):
        pass

    def close(self):
        self._fd.close()

    def _get_ontology_name(self, ontology):
        if ontology is None:
            return self._EMPTY_STRING
        else:
            return self._get_if_not_missing(ontology.name)

    def _get_if_not_missing(self, string):
        if self._is_missing(string):
            return self._EMPTY_STRING
        else:
            return string

    def _is_missing(self, string):
        if not string \
                or string.lower() == self._NA \
                or string.lower() == self._NULL \
                or string.lower() == self._NONE:
            return True
        else:
            return False

