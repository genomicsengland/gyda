from abc import abstractmethod

from DataProducers.PanelApp import PanelApp


class TextReader:

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
    _HOST = "https://panelapp.genomicsengland.co.uk"

    def pre(self):
        pass

    def open(self):
        self._resource = PanelApp(server=self._HOST)

    def read(self):
        for panel in self._resource.panel_list():
            # Panel name is also a disease name
            yield panel.name

            for relevant_disorder in panel.relevant_disorders:
                yield relevant_disorder

    def post(self):
        pass

    def close(self):
        pass
