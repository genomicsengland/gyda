import logging


class PhenotypeMapper(object):

    def __init__(self, config):
        """
        :type config: dict
        """
        PhenotypeMapper._sanity_checks(config)
        self.gel_user = config['gel_user']

    @staticmethod
    def _sanity_checks(config):
        assert config is not None, "Empty config!"
        # TODO!
        assert 'gel_user' in config, "Missing gel_user!"

    def map(self, phenotypes):

        logging.info("The user is {}".format(self.gel_user))
        mapped_phenotypes = []
        for phenotype in phenotypes:
            mapped_phenotypes.append(phenotype.lower())

        return mapped_phenotypes
