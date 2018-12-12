from unittest import TestCase

from gyda.PhenotypeMappers import ZoomaMapper


class TestZoomaMapper(TestCase):
    def test_run(self):
        zooma_mapper = ZoomaMapper()
        a = zooma_mapper.run(["Homocystinuria, B6-responsive and nonresponsive types"])
        a = 1
