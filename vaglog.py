import abc
import csv
import io
import os.path

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union

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


# TODO VagLogFactory seperate from VagLogReaderFactory(?)
class VagLogReaderFactory:
    __slots__ = ('_source', )

    def __init__(self, source: Union[str, bytes, Path, io.StringIO]):
        self._source = source

    def generate_vaglog(self) -> VAGLog:
        if isinstance(self._source, (str, Path)):
            if os.path.isfile(self._source) and self._source.lower().endswith('.csv'):
                return CsvVagLogReader(self._source).generate_vaglog()
        elif isinstance(self._source, io.StringIO):
            return CsvBufferVagLogReader(self._source).generate_vaglog()


class VagLogReader(abc.ABC):
    @abc.abstractmethod
    def generate_vaglog(self) -> VAGLog:
        pass


class CsvVagLogReader(VagLogReader):
    __slots__ = ('_filepath', '_labels', '_labels', '_timestamp', '_vcds_version',
                 '_vcds_data_version', '_car_controller', '_engine_type', '_measure_groups', '_data')

    MEASURE_GROUP_SIZE = 5

    def __init__(self, log_data: Union[str, bytes, Path, io.StringIO]):
        self._log_data = log_data
        self._labels = list()

        self._timestamp = ''
        self._vcds_version = ''
        self._vcds_data_version = ''
        self._car_controller = ''
        self._engine_type = ''
        self._measure_groups = tuple()
        self._data = defaultdict(dict)

    @staticmethod
    def is_binary(text: str) -> bool:
        values = set(text)
        binary_set = {'0', '1'}

        if binary_set == values or values == {'0'} or values == {'1'}:
            return True
        return False

    def generate_vaglog(self) -> VAGLog:
        self._process_log_data()
        self._cleanup_data_structure()

        return VAGLog(
            self._timestamp,
            self._vcds_version,
            self._vcds_data_version,
            self._car_controller,
            self._engine_type,
            self._measure_groups,
            self._data
        )

    def _process_log_data(self):
        with open(self._log_data) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')

            for idx, row in enumerate(csv_reader):
                self._process_log_row(idx, row)

    def _process_log_row(self, idx: int, row: Row):
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
                self._handle_duplicated_labels()
                self._set_data_structure()
            case _:
                self._process_data_row(row)

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
        self._labels = row

    def _concat_labels(self, row: Row):
        for i in range(len(self._labels)):
            self._labels[i] += f' {row[i]}'
        self._labels = [x.strip() for x in self._labels]

    def _process_measure_units(self, row: Row):
        for i, label in enumerate(self._labels):
            if 'TIME' in label.upper() or not label:
                self._labels[i] += row[i]
            else:
                self._labels[i] += f' [{row[i].strip()}]'

    def _handle_duplicated_labels(self):
        for label in self._labels:
            if not label:
                continue
            counted_labels = Counter(self._labels)
            n_occurrences = counted_labels[label]
            if n_occurrences > 1:
                for count in range(1, n_occurrences + 1):
                    self._labels[self._labels.index(label)] = f'{label} ({count})'

    def _set_data_structure(self):
        group_index = 1

        for group in self._measure_groups:
            for j in range(group_index, group_index + self.MEASURE_GROUP_SIZE):
                label = self._labels[j]
                if label:
                    self._data[group][label] = list()

            group_index += self.MEASURE_GROUP_SIZE

    def _process_data_row(self, row: Row):
        group_index = 1

        for group in self._measure_groups:
            for j in range(group_index, group_index + self.MEASURE_GROUP_SIZE):
                value = row[j].replace(' ', '')
                if not value:
                    continue

                label = self._labels[j]
                if self.is_binary(value):
                    self._data[group][label].append(row[j])
                else:
                    self._data[group][label].append(float(row[j]))

            group_index += self.MEASURE_GROUP_SIZE

    def _cleanup_data_structure(self):
        # Convert data values to be tuple type
        for key in self._data:
            for label in self._data[key]:
                self._data[key][label] = tuple(self._data[key][label])
        self._data = dict(self._data)


class CsvBufferVagLogReader(CsvVagLogReader):
    def _process_log_data(self):
        for idx, row in enumerate(self._log_data):
            row = row.replace('\n', '').replace('\r', '').split(',')
            self._process_log_row(idx, row)