import pronto
import pandas as pd
import json
import logging
import os


class OntologiesDictionary(object):

    def __init__(self, config):

        # ontology source files
        self.hpo_file = config.get("hpo", None)
        self.do_file = config.get("do", None)
        self.omim_file = config.get("omim", None)
        self.snomed_file = config.get("snomed", None)
        self.panelapp_file = config.get("snomed", None)

        self._sanity_checks()

        # loads everything in memory
        self.ontology_terms = self.prepare_onto_df()

    def _sanity_checks(self):
        count_ontologies = 0
        if self.hpo_file:
            if not os.path.exists(self.hpo_file):
                raise ValueError("Provided HPO file does not exist")
            count_ontologies += 1
        if self.do_file:
            if not os.path.exists(self.do_file):
                raise ValueError("Provided DO file does not exist")
            count_ontologies += 1
        if self.omim_file:
            if not os.path.exists(self.omim_file):
                raise ValueError("Provided OMIM file does not exist")
            count_ontologies += 1
        if self.snomed_file:
            if not os.path.exists(self.snomed_file):
                raise ValueError("Provided Snomed CT file does not exist")
            count_ontologies += 1
        if self.panelapp_file:
            if not os.path.exists(self.panelapp_file):
                raise ValueError("Provided PanelApp file does not exist")
            count_ontologies += 1
        assert count_ontologies > 0, "No ontologies were provided!"

    def _read_obo(self, ontology):
        """
        :type ontology: pronto.Ontology
        :return: pandas.DataFrame
        """
        entries = []
        for entry in ontology:
            try:
                # gather main name and any synonyms
                names = [entry.name]
                names.extend([syn.desc for syn in entry.synonyms])
                # loop through names and synonym_ids for orderedmatches
                entries.append({
                    "name": names,
                    "id": entry.id,
                    "primary_name": names[0]
                })
            except Exception, ex:
                logging.error("Failed to parse term {}: {}".format(entry.id, ex.message))
                raise ex
        return pd.DataFrame(entries)

    def _read_omim(self, omim_txt):
        """
        :type omim_txt: str
        :return: pandas.DataFrame
        """
        entries = []
        with open(omim_txt, 'r') as f:
            for line in f.readlines():
                try:
                    # skips header lines and removed or moved entries
                    if line.startswith("#") or line.startswith("Caret"):
                        continue
                    names = []
                    columns = line.strip().split('\t')
                    # main_title
                    names.append(columns[2].split(';')[0])
                    # alt_titles
                    if len(columns) > 3:
                        names.extend([x for x in map(lambda y: y.strip(), columns[3].split(';')) if x > 0])
                    entries.append({
                        "name": names,
                        "id": "OMIM:%s".format(str(columns[1])),
                        "primary_name": names[0]
                    })
                except Exception, ex:
                    logging.error("Failed to parse OMIM term {}: {}".format(line, ex.message))
                    raise ex
        return pd.DataFrame(entries)

    def _read_snomed(self, snomed_csv):
        """
        :type snomed_csv: str
        :return: pandas.DataFrame
        """
        try:
            df = pd.read_csv(snomed_csv, sep='\t', header=0, usecols=['conceptId', 'term']).drop_duplicates()
            # rename and rearrange columns
            df['name'] = df.term
            df['id'] = 'SNOMEDCT:'+df['conceptId'].astype(str)
            df['primary_name'] = df.term
            df = df[['name', 'id', 'primary_name']]
        except Exception, ex:
            logging.error("Failed to parse SNOMED CT: {}".format(ex.message))
            raise ex
        return df

    def _read_panelapp(self, panelapp_json):
        """
        :type panelapp_json: str
        :return: pandas.DataFrame
        """
        # url = 'https://panelapp.genomicsengland.co.uk/WebServices/list_panels/'
        # response = urllib.request.urlopen(url)
        data = json.load(panelapp_json)
        df = pd.DataFrame()
        # prepare add panelapp data
        panel_ids = []
        panel_names = []
        for panel in data['result']:
            panel_ids.append('PANELAPP:' + panel['Panel_Id'])
            panel_names.append(panel['Name'])
        df['name'] = panel_names
        df['id'] = panel_ids
        df['primary_name'] = panel_names
        return df

    def prepare_onto_df(self):
        """combine ontos into dataframe"""
        ontologies = []
        if self.hpo_file:
            ontologies.append(self._read_obo(pronto.Ontology(self.hpo_file)))
        if self.do_file:
            ontologies.append(self._read_obo(pronto.Ontology(self.do_file)))
        if self.omim_file:
            ontologies.append(self._read_omim(self.omim_file))
        if self.snomed_file:
            ontologies.append(self._read_snomed(self.snomed_file))
        if self.panelapp_file:
            ontologies.append(self._read_panelapp(self.panelapp_file))

        dataframe = pd.concat(ontologies)
        # NOTE: do we need this? It is failing for unknown reasons...
        # onto_df = onto_df.drop_duplicates()
        return dataframe
