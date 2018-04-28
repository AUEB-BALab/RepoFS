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

import sys
import os
import argparse
import datetime
from fuse import FUSE

from repofs import RepoFS

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="Git repository to be processed.")
    parser.add_argument("mount", help="Path where the FileSystem will be mounted." \
    "If it doesn't exist it is created and if it exists and contains files RepoFS exits.")
    parser.add_argument(
        "--hash-trees",
        help="Store 256 entries (first two digits) at each level" \
            "of commits-by-hash for the first three levels.",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--no-ref-symlinks",
        help="Do not create symlinks for commits of refs.",
        action="store_true",
        default=False
    )
    args = parser.parse_args()

    if not os.path.exists(os.path.join(args.repo, '.git')):
        raise Exception("Not a git repository")

    foreground = True
    if sys.argv[0].endswith("repofs"):
        foreground = False

    sys.stderr.write("Examining repository.  Please wait..\n")
    start = datetime.datetime.now()
    repo = RepoFS(os.path.abspath(args.repo), os.path.abspath(args.mount), args.hash_trees, args.no_ref_symlinks)
    end = datetime.datetime.now()
    sys.stderr.write("Ready! Repository mounted in %s\n" % (end - start))
    sys.stderr.write("Repository %s is now visible at %s\n" % (args.repo,
                                                               args.mount))
    FUSE(repo, os.path.abspath(args.mount), nothreads=True, foreground=foreground)

if __name__ == '__main__':
    main()
