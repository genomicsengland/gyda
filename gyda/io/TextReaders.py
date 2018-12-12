import logging
from abc import abstractmethod

from DataProducers.PanelApp import PanelApp


class TextReader:

    _logger = logging.getLogger()

    def __init__(self):
        self._resource = None

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def pre(self):
        pass

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def post(self):
        pass

    @abstractmethod
    def close(self):
        pass


class PanelAppDiseasesReader(TextReader):
    PHENOTYPES_FIELD = "genes.phenotypes"
    RELEVANT_DISORDERS_FIELD = "relevant_disorders"
    NAME_FIELD = "name"
    CC_PANEL_TYPE = "cancer germline 100k"
    RD_PANEL_TYPE = "rare disease 100k"
    _HOST = "https://panelapp.genomicsengland.co.uk"
    _PANEL_TYPE_NAME_FIELD = "name"

    def __init__(self, allowed_panel_type_list=None, allowed_panel_field_list=None):
        TextReader.__init__(self)

        if allowed_panel_type_list:
            self._allowed_panel_type_set = set(allowed_panel_type_list)
        else:
            self._allowed_panel_type_set = None

        if allowed_panel_field_list:
            self._allowed_panel_field_set = set(allowed_panel_field_list)
        else:
            self._allowed_panel_field_set = None

    def pre(self):
        pass

    def open(self):
        self._resource = PanelApp(server=self._HOST)

    def read(self):
        i = 0
        for gene in self._resource.gene_list():
            if i % 100 == 0:
                self._logger.info("{i} gene (panel-specific) entities read".format(i=i))
                if i > 0:
                    break

            if self._allowed_panel_type_set is None \
                    or self._get_panel_type_set(gene).intersection(self._allowed_panel_type_set):
                if self._allowed_panel_field_set is None \
                        or self.PHENOTYPES_FIELD in self._allowed_panel_field_set \
                        and gene.phenotypes:
                    for phenotype_string in gene.phenotypes:
                        if phenotype_string:
                            yield phenotype_string

                if self._allowed_panel_field_set is None or self.NAME_FIELD in self._allowed_panel_field_set:
                    # Panel name is also a disease name
                    yield gene.panel.name

                if self._allowed_panel_field_set is None \
                        or self.RELEVANT_DISORDERS_FIELD in self._allowed_panel_field_set \
                        and gene.panel.relevant_disorders:
                    for relevant_disorder in gene.panel.relevant_disorders:
                        yield relevant_disorder
            i += 1

    def post(self):
        pass

    def close(self):
        pass

    def _get_panel_type_set(self, gene_entity):
        if gene_entity.panel is not None and gene_entity.panel.types:
            return set([panel_type_dict[self._PANEL_TYPE_NAME_FIELD].lower() for panel_type_dict
                        in gene_entity.panel.types
                        if self._PANEL_TYPE_NAME_FIELD in panel_type_dict
                        and panel_type_dict[self._PANEL_TYPE_NAME_FIELD]])

        return set()
