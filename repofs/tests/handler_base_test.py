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

from unittest import TestCase, main

from repofs.handlers.handler_base import HandlerBase

class HandlerBaseTest(TestCase):
    def setUp(self):
        self.handler_base = HandlerBase()

    def test_is_dir(self):
        with self.assertRaises(NotImplementedError):
            self.handler_base.is_dir("foobar")

    def test_is_symlink(self):
        with self.assertRaises(NotImplementedError):
            self.handler_base.is_symlink("foobar")

    def test_file_contents(self):
        with self.assertRaises(NotImplementedError):
            self.handler_base.file_contents("foobar")

    def test_readdir(self):
        with self.assertRaises(NotImplementedError):
            self.handler_base.readdir("foobar")

if __name__ == "__main__":
    main()
