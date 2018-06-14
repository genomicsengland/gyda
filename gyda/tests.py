import os
import logging
import unittest
from gyda.phenotype_mapper import PhenotypeMapper
from gyda.ontologies_dictionary import OntologiesDictionary


CONFIG = {
    "hpo": "/Users/matthewwerlock/Documents/ontologies/hp.obo",
    "do": "/Users/matthewwerlock/Documents/ontologies/doid-merged.obo",
    "omim": "/Users/matthewwerlock/Documents/ontologies/mimTitles.txt",
    "panelapp": "/Users/matthewwerlock/Documents/ontologies/panelapp.json"
    "snomed": "/Users/matthewwerlock/Documents/ontologies/sct2_Description_Full-en_INT_20180131.txt"
}

CONFIG_SMALL = {
    "hpo": "/Users/matthewwerlock/Documents/ontologies/hp.obo",
    "do": "/Users/matthewwerlock/Documents/ontologies/doid-merged.obo",
    "omim": "/Users/matthewwerlock/Documents/ontologies/mimTitles.txt",
    "panelapp": "/Users/matthewwerlock/Documents/ontologies/panelapp.json"
}


class TestOntologyDictionary(unittest.TestCase):
    # credentials

    def setUp(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M')

    def test_parse_ontologies(self):

        self.ontologies = OntologiesDictionary(CONFIG)
        pass


class TestPhenotypeMapper (unittest.TestCase):
    # credentials

    def setUp(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M')

    def test_map_phenotype(self):
        self.phenotype_mapper = PhenotypeMapper(CONFIG_SMALL)
        # test = ["this", "that"]
        test = [
            "intellectual disability",
            "smith - magenis syndrome",
            "combined oxidative phosphorylation deficiency 13",
            "coach syndrome",
            "retinitis pigmentosa 4",
            "coenzyme q10 deficiency primary 1",
            "familial colon cancer",
            "non - specific"
            "hartnup disorder",
            "cone - rod dystrophy 2"
        ]
        mapped_phenotypes = self.phenotype_mapper.map_phenotypes(test)
        print(mapped_phenotypes.to_string())
        # self.assertIsNone(mapped_phenotypes)


if __name__ == '__main__':
    unittest.main()
