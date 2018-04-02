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

from repofs.handlers.handler_base import HandlerBase
from repofs.gitoper import GitOperError

class CommitHandler(HandlerBase):
    def _get_commit_content(self):
        # root isn't a commit hash
        if self.path_data['commit'] not in self.oper.all_commits():
            self._not_exists()

        if self._is_metadata_dir():
            return self._get_metadata_dir(self.path_data['commit'])

        try:
            dirents = self.oper.directory_contents(self.path_data['commit'], self.path_data['commit_path'])
        except GitOperError:
            self._dir_not_exists()

        if not self.path_data['commit_path']:
            dirents += self._get_metadata_names()

        return dirents
