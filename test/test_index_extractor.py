import os
import unittest

from mecip import process_file
from mecip import ProfessorIndexExtractor

import pandas as pd


class IndexExtractorTest(unittest.TestCase):

    def test_extractor(self):

        extractor = ProfessorIndexExtractor()

        BASE_PATH = './resources/lattes'

        raw_data = [process_file(os.path.join(BASE_PATH, filename)) for filename in os.listdir(BASE_PATH)]

        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1024)
        print(extractor.compute_index(raw_data))

