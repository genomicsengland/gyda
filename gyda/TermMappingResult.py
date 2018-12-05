class TermMappingResult(object):
    def __init__(self, query=None, result=None):
        if result is None:
            result = []

        # String containing the original query
        self.query = query

        # Expected to contain a list of TermResult objects
        self.result = result
