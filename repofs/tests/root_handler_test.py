#!/usr/bin/env python
#
# Copyright 2017-2021 Vitalis Salis and Diomidis Spinellis
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

from unittest import TestCase, main
from repofs.handlers.root import RootHandler

class RootHandlerTest(TestCase):
    def test_handler(self):
        handler = RootHandler()
        self.assertTrue(handler.is_dir())
        self.assertEqual(handler.readdir(), ['commits-by-date', 'commits-by-hash', 'branches', 'tags'])

if __name__ == "__main__":
    main()
