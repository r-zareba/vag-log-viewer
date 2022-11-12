import os

from vaglog import VagLogReaderFactory, VAGLog


# timestamp = datetime.strptime(timestamp, '%A %d %B %Y %H:%M:%S')
import pytest


TEST_DATA_DIR = os.path.join('tests', 'data')


def get_vaglog_for_test(path: str) -> VAGLog:
    return VagLogReaderFactory(path).generate_vaglog()


def get_all_test_files_paths() -> list[str]:
    return [os.path.join(TEST_DATA_DIR, file) for file in os.listdir(TEST_DATA_DIR) if file.lower().endswith('.csv')]


@pytest.mark.parametrize('logfile_path', get_all_test_files_paths())
def test_vaglog_reader_run(logfile_path: str):
    vaglog = get_vaglog_for_test(logfile_path)
    assert vaglog


@pytest.mark.parametrize('logfile,groups_len_expected', [
    ('1.csv', 3),
    ('2.csv', 3),
    ('3.csv', 2),
    ('4.csv', 2),
    ('5.csv', 3),
    ('6.csv', 3),
    ('7.csv', 1),
    ('8.csv', 3),
    ('9.csv', 2),
    ('10.csv', 3),
    ('11.csv', 2),
    ('12.csv', 3),
    ('13.csv', 2),
    ('14.csv', 1),
    ('15.csv', 3),
    ('16.csv', 2),
    ('17.csv', 3),
    ('18.csv', 1),
    ('19.csv', 3),
    ('20.csv', 3)
])
def test_measure_groups_len(logfile: str, groups_len_expected: int):
    path = os.path.join(TEST_DATA_DIR, logfile)
    vaglog = get_vaglog_for_test(path)
    assert len(vaglog.measure_groups) == groups_len_expected


@pytest.mark.parametrize('logfile,data_rows_len_expected', [
    ('1.csv', 11),
    ('2.csv', 71),
    ('3.csv', 2755),
    ('4.csv', 70),
    ('5.csv', 21),
    ('6.csv', 24),
    ('7.csv', 108),
    ('8.csv', 17),
    ('9.csv', 21),
    ('10.csv', 116),
    ('11.csv', 24),
    ('12.csv', 161),
    ('13.csv', 77),
    ('14.csv', 160),
    ('15.csv', 46),
    ('16.csv', 15),
    ('17.csv', 16),
    ('18.csv', 29),
    ('19.csv', 24),
    ('20.csv', 11),
])
def test_data_rows_len(logfile: str, data_rows_len_expected: int):
    path = os.path.join(TEST_DATA_DIR, logfile)
    vaglog = get_vaglog_for_test(path)
    for group, values in vaglog.data.items():
        for label in values:
            if 'bin' in label.lower():  # Ignore bit fields as they miss data sometimes
                continue
            assert len(vaglog.data[group][label]) == data_rows_len_expected


@pytest.mark.parametrize('logfile_path', get_all_test_files_paths())
def test_vaglog_labels_uniqueness(logfile_path: str):
    vaglog = get_vaglog_for_test(logfile_path)
    n_total_labels = sum(len(vaglog.data[x]) for x in vaglog.data)

    merged_data = dict()
    for measure_group in vaglog.data:
        merged_data = merged_data | vaglog.data[measure_group]

    # Number of summed labels should be same as dict merging result (No duplicated keys in the vaglog data)
    assert n_total_labels == len(merged_data)
