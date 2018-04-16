#!/usr/bin/env python
#
# Copyright 2017-2018 Vitalis Salis and Diomidis Spinellis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import datetime

from repofs.handlers.commit_handler import CommitHandler
from repofs import utils

class CommitDateHandler(CommitHandler):
    def __init__(self, path, oper):
        self.path = path
        self.oper = oper
        self.path_data = utils.demux_commits_by_date_path(path)

    def _days_per_month(self, year):
        """ Return an array with the number of days in each month
        for the given year. """
        days = []
        for month in range(1, 13):
            this_month = datetime.date(year, month, 1)
            next_month = (this_month.replace(day=28) +
                          datetime.timedelta(days=4))
            last_day = next_month - datetime.timedelta(days=next_month.day)
            days.append(last_day.day)
        return days

    def _date_path_to_int(self):
        return [int(x) for x in self.path_data['date_path'].split("/")]

    def _month_dates(self, year, month):
        """ Return an array with the dates in the given year and month
        The month is 1-based.
        """
        return range(1, self._days_per_month(year)[month - 1] + 1)

    def _string_list(self, l):
        """ Return list l as a list of strings """
        return [str(x) for x in l]

    def _verify_date_path(self):
        """ Raise an exception if the elements array representing a commit
        date path [y, m, d] do not represent a valid date. """

        try:
            elements = self._date_path_to_int()
        except ValueError: # path is not int
            self._not_exists()

        if len(elements) >= 1 and elements[0] not in self.oper.years:
            self._not_exists()
        if len(elements) >= 2 and elements[1] not in range(1, 13):
            self._not_exists()
        if len(elements) >= 3 and elements[2] not in range(1, self._days_per_month(
                elements[0])[elements[1] - 1] + 1):
            self._not_exists()

    def _verify_commit(self):
        if (self.path_data['commit'] \
                and self.path_data['commit'] not in self.oper.all_commits()):
            self._not_exists()

    def is_dir(self):
        if not self.path:
            return True

        self._verify_date_path()
        self._verify_commit()

        if not self.path_data['commit_path']:
            return True

        if self._is_metadata_dir():
            return True

        return self.oper.is_dir(self.path_data['commit'], self.path_data['commit_path'])

    def is_symlink(self):
        if not self.path_data['commit_path'] or self._is_metadata_name():
            return False
        if self.is_metadata_symlink():
            return True
        return self.oper.is_symlink(self.path_data['commit'], self.path_data['commit_path'])

    def file_contents(self):
        if self._is_metadata_file():
            return self._get_metadata_file(self.path_data['commit_path'])

        return self.oper.file_contents(self.path_data['commit'], self.path_data['commit_path'])

    def get_commit(self):
        return self.path_data['commit']

    def file_size(self):
        if self._is_metadata_file():
            return len(self._get_metadata_file(self.path_data['commit']))

        return self.oper.file_size(self.get_commit(), self.path_data['commit_path'])

    def get_symlink_target(self):
        if not self.path_data['commit_path']:
            self._not_exists()

        if self.is_metadata_symlink():
            return self.path_data['commit_path'].split("/")[-1]

        target = self.oper.file_contents(self.path_data['commit'], self.path_data['commit_path'])
        return os.path.join(self.path_data['date_path'], self.path_data['commit'], target)

    def readdir(self):
        if not self.path_data['date_path']:
            return self._string_list(self.oper.years)

        self._verify_date_path()
        self._verify_commit()
        elements = self._date_path_to_int()
        if len(elements) == 1:
            return self._string_list(range(1, 13))
        elif len(elements) == 2:
            return self._string_list(self._month_dates(elements[0],
                                                       elements[1]))
        elif not self.path_data['commit']:
            return self.oper.commits_by_date(elements[0], elements[1],
                                             elements[2])
        else:
            # /commits-by-date/yyyy/mm/dd/hash
            return self._get_commit_content()
