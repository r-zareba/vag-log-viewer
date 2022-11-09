import os
from vaglog import VagLogReaderFactory


DATA_DIR = os.path.join('tests', 'data')
PATH = os.path.join(DATA_DIR, '12.csv')

vag_log = VagLogReaderFactory(PATH).generate_vaglog()
print(vag_log)


# for filename in os.listdir(DATA_DIR):
#     file = os.path.join(DATA_DIR, filename)
#     vag_log = VagLogReaderFactory(file).generate_vaglog()
#
#     print(f'\nProcessing {file} \n')
#
#     for k, v in vag_log.data.items():
#         for i in v:
#             print(f'len: {k=} {i=} -- {len(vag_log.data[k][i])}')
#             for j in vag_log.data[k][i]:
#                 pass
                # print(f'GROUP: {k}, {i}, {j}')


