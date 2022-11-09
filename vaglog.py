import abc
import csv
import os.path

from collections import Counter, defaultdict
from dataclasses import dataclass

Row = list[str]


@dataclass(slots=True, frozen=True)
class VAGLog:
    timestamp: str
    vcds_version: str
    vcds_data_version: str
    car_controller: str
    engine_type: str
    measure_groups: tuple[str]
    data: dict


class VagLogReaderFactory:
    __slots__ = ('_source', )

    def __init__(self, source: str):
        self._source = source

    def generate_vaglog(self) -> VAGLog:
        if os.path.isfile(self._source) and self._source.lower().endswith('.csv'):
            return CsvVagLogReader(self._source).generate_vaglog()


class VagLogReader(abc.ABC):
    @abc.abstractmethod
    def generate_vaglog(self) -> VAGLog:
        pass


class CsvVagLogReader(VagLogReader):
    __slots__ = ('_filepath', '_labels_list', '_labels', '_timestamp', '_vcds_version',
                 '_vcds_data_version', '_car_controller', '_engine_type', '_measure_groups', '_data')

    MEASURE_GROUP_SIZE = 5

    def __init__(self, filepath: str):
        self._filepath = filepath
        self._labels_list = list()
        self._labels = defaultdict(list)

        self._timestamp = ''
        self._vcds_version = ''
        self._vcds_data_version = ''
        self._car_controller = ''
        self._engine_type = ''
        self._measure_groups = tuple()
        self._data = defaultdict(dict)

    def generate_vaglog(self) -> VAGLog:
        self._process_logfile()
        return VAGLog(
            self._timestamp,
            self._vcds_version,
            self._vcds_data_version,
            self._car_controller,
            self._engine_type,
            self._measure_groups,
            self._data
        )

    @staticmethod
    def is_binary(text: str) -> bool:
        values = set(text)
        binary_set = {'0', '1'}

        if binary_set == values or values == {'0'} or values == {'1'}:
            return True
        return False

    def _process_logfile(self):
        with open(self._filepath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")

            for idx, row in enumerate(csv_reader):
                match idx:
                    case 0:
                        self._process_timestamp_vcds_row(row)
                    case 1:
                        self._process_controller_engine_row(row)
                    case 3:
                        self._process_measure_groups(row)
                    case 4:
                        self._create_labels(row)
                    case 5:
                        self._concat_labels(row)
                    case 6:
                        self._process_measure_units(row)
                        self._set_labels_dict()
                        self._handle_duplicated_labels()
                        self._set_data_structure()
                    case _:
                        self._process_data_row(row)

        # Convert data values to be tuple type
        for key in self._data:
            for label in self._data[key]:
                self._data[key][label] = tuple(self._data[key][label])
        self._data = dict(self._data)

    def _process_timestamp_vcds_row(self, row: Row):
        timestamp = row[4].split('-')[0]
        row[4] = ':'.join(timestamp.split(':')[:3])
        self._timestamp = ' '.join(row[:5])

        if len(row) == 7:
            self._vcds_version = row[5].strip()
            self._vcds_data_version = row[6].strip()

    def _process_controller_engine_row(self, row: Row):
        self._car_controller = row[0].strip()
        self._engine_type = ' '.join(row[2].split())

    def _process_measure_groups(self, row: Row):
        cleaned_row = [x.replace('\'', '').strip() for x in row]
        self._measure_groups = tuple(i for i in cleaned_row if i.replace('\'', '').isdigit())

    def _create_labels(self, row: Row):
        self._labels_list = row

    def _concat_labels(self, row: Row):
        for i in range(len(self._labels_list)):
            self._labels_list[i] += f' {row[i]}'
        self._labels_list = [x.strip() for x in self._labels_list]

    def _process_measure_units(self, row: Row):
        for i, label in enumerate(self._labels_list):
            if 'TIME' in label.upper() or not label:
                self._labels_list[i] += row[i]
            else:
                self._labels_list[i] += f' [{row[i].strip()}]'

    def _set_labels_dict(self):
        i = 1
        for group in self._measure_groups:
            for j in range(i, i + self.MEASURE_GROUP_SIZE):
                label = self._labels_list[j]
                if label:
                    self._labels[group].append(label)
            i += self.MEASURE_GROUP_SIZE

    def _handle_duplicated_labels(self):
        for group in self._labels:
            group_labels = self._labels[group]
            counted_labels = Counter(group_labels)
            for label in group_labels:
                n_occurrences = counted_labels[label]
                if n_occurrences > 1:
                    for count in range(1, n_occurrences+1):
                        self._labels[group][group_labels.index(label)] = f'{label} ({count})'

    def _set_data_structure(self):
        for group, labels in self._labels.items():
            for label in labels:
                self._data[group][label] = list()

    def _process_data_row(self, row: Row):
        group_index = 1

        for group in self._measure_groups:
            label_index = 0
            for j in range(group_index, group_index + self.MEASURE_GROUP_SIZE):
                value = row[j].replace(' ', '')
                if not value:
                    continue

                label = self._labels[group][label_index]

                if self.is_binary(value):
                    self._data[group][label].append(row[j])
                else:
                    self._data[group][label].append(float(row[j]))
                label_index += 1
            group_index += self.MEASURE_GROUP_SIZE
