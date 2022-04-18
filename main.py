import os
import pandas as pd
import shutil


from mecip import ProfessorIndexExtractor
from mecip import process_file

if __name__ == '__main__':

    extractor = ProfessorIndexExtractor()

    INPUT_PATH, OUTPUT_PATH = './lattes', './output'

    if os.path.exists(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)

    raw_data = [process_file(os.path.join(INPUT_PATH, filename)) for filename in os.listdir(INPUT_PATH)]

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1024)

    output = extractor.compute_index(raw_data)

    os.mkdir(OUTPUT_PATH)

    output.sort_values('nome', inplace=True)
    output.to_csv(os.path.join(OUTPUT_PATH, 'indices.csv'), sep=',', header=True, encoding='iso-8859-1', index=False)

    for k, v in {'log': extractor.logging, 'errors': extractor.inconsistencies}.items():

        for key, items in v.items():

            directory_path = os.path.join(OUTPUT_PATH, key)

            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            with open(os.path.join(directory_path, k + '.txt'), mode='w+', encoding='iso-8859-1') as file:
                for group, value in items.items():
                    file.write(group + '\n')
                    for _v_ in value:
                        for line in _v_.split('\n'):
                            file.write('   ' + line + '\n')
                    file.write('\n')




