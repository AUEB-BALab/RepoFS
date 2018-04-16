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

from itertools import product

from repofs.handlers.commit_handler import CommitHandler
from repofs import utils

class CommitHashHandler(CommitHandler):
    def __init__(self, path, oper, hash_trees):
        self.path = path
        self.oper = oper
        self.hash_trees = hash_trees
        self.path_data = utils.demux_commits_by_hash_path(path, hash_trees)
        self._hex = self._get_hex()

    def _get_hex(self, repeat=2):
        digits = '0123456789abcdef'
        return list(map(''.join, product(digits, repeat=repeat)))

    def _verify_hash_path(self):
        if self.hash_trees and self.path_data['htree_prefix']:
            elements = self.path_data['htree_prefix'].split("/")
            for elem in elements:
                if elem not in self._hex:
                    self._not_exists()

    def _verify_commit(self):
        if (self.path_data['commit'] \
                and self.path_data['commit'] not in self.oper.all_commits()):
            self._not_exists()

    def is_dir(self):
        if not self.path:
            return True

        self._verify_hash_path()
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
            return self._get_metadata_file(self.path_data['commit'])
        return self.oper.file_contents(self.path_data['commit'], self.path_data['commit_path'])

    def get_commit(self): #TODO TESTS
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
        return os.path.join(self.path_data['htree_prefix'], self.path_data['commit'], target)

    def readdir(self):
        if self.hash_trees:
            htree_elem = self.path_data['htree_prefix'].split("/")
            if len(htree_elem) <= 2:
                return self._hex
            elif len(htree_elem) == 3 and not self.path_data['commit']:
                return self.oper.all_commits(''.join(htree_elem))

        if not self.path_data['commit']:
            return self.oper.all_commits()

        return self._get_commit_content()
