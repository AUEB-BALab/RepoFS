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

import datetime
import os
import re
import sys
import StringIO

from subprocess import check_output, CalledProcessError, call
from pygit2 import Repository, Commit, GIT_OBJ_TREE, GIT_FILEMODE_LINK


class GitOperations(object):
    def __init__(self, repo):
        self.repo = repo
        self._gitrepo = os.path.join(repo, '.git')
        self._pygit = Repository(repo)
        self._commands = {}
        self._trees = {}
        self._trees_filled = {}
        self._sizes = {}
        self._refs = {}
        self._commits_iterator = None
        self.years = range(self._first_year(), self._last_year() + 1)

    def cached_command(self, list, return_exit_code=False, silent=False):
        """
        Executes the specified git command and returns its result.
        Subsequent executions of the same command return the cached result
        If return_exit_code is set, then the return value is True of False
        depending on whether the command exited with 0 or not.
	If silent is true then failed executions return None,
	without displaying an error.
        """

        list = ['git', '--git-dir', self._gitrepo] + list
        command = " ".join(list)
        if command in self._commands:
            return self._commands[command]
        else:
            try:
                # print(command)
                out = check_output(list)
                if return_exit_code:
                    out = True
            except CalledProcessError as e:
                if return_exit_code:
                    out = False
		elif silent:
		    out = None
                else:
                    message = "Error calling %s: %s" % (command, str(e))
                    sys.stderr.write(message)
                    out = None
            self._commands[command] = out
            return out

    def _get_entry(self, commit, path=None, return_tree=False):
        try:
            if path:
                obj = self._pygit[commit].tree[path]
            elif path == '':
                obj = self._pygit[commit].tree
            else:
                obj = self._pygit[commit]
        except KeyError as e:
            raise GitOperError("pygit entry does not exist\n%s" % (str(e)))

        if return_tree:
            return obj

        return self._pygit[obj.id]

    def _fill_trees(self, commit, contents):
        if not commit in self._trees:
            self._trees[commit] = set()

        trees = []
        for cont in contents:
            if cont[1] == "tree" and cont[0] not in self._trees[commit]:
                trees.append(cont[0])

        self._trees[commit].update(trees)

    def _get_tree(self, commit, path):
        if not path:
            tree = self._get_entry(commit, '')
        else:
            path += "/"
            try:
                tree = self._get_entry(commit, path)
            except KeyError:
                return []

        return [(c.name, c.type) for c in tree]

    def _cache_tree(self, commit, path):
        tree = self._get_tree(commit, path)
        paths_and_names = [(os.path.join(path, c[0]), c[1]) for c in tree]
        self._fill_trees(commit, paths_and_names)
        if not commit in self._trees_filled:
            self._trees_filled[commit] = set()
        self._trees_filled[commit].update([path])

    def _first_year(self):
        """
        Returns the year of the repo's first commit(s)
        Not implemented using pygit2 because its faster
        to get the year via shell command and it creates
        only one process on boot time.
        """

        first_years = self.cached_command(['log', '--max-parents=0',
                                         '--date=format:%Y',
                                         '--pretty=%ad']
                                         ).splitlines()
        return int(sorted(first_years)[0])

    def _last_year(self):
        """
        Returns the year of the repo's last commit
        """
        return int(self.cached_command(['log', '-n', '1', '--all',
                                         '--date=format:%Y',
                                         '--pretty=%ad']
                                         ))

    def refs(self, refs):
        """
        Returns the specified refs in the form:
        <commit_hash> refs/{heads,remotes,tags}/<branchname>
        """
        refs = self.cached_command(['for-each-ref',
                '--format=%(objectname) %(refname)'] + refs).splitlines()
        return [ref.strip() for ref in refs]

    def commits_by_date(self, y, m, d):
        """
        Returns a list of commit hashes for the given year, month, day
        """
        start = datetime.date(y, m, d)
        end = start + datetime.timedelta(days=1)
        # T00:00:00 is at the start of the specified day
        commits = self.cached_command(['log',
                                       '--after',
                                       '%04d-%02d-%02dT00:00:00' % (start.year,
                                                           start.month,
                                                           start.day),
                                       '--before',
                                       '%04d-%02d-%02dT00:00:00' % (end.year,
                                                           end.month,
                                                           end.day),
                                       '--all', '--pretty=%H']).splitlines()
        commits = [commit.strip() for commit in commits]
        return commits

    def _get_commits_iterator(self):
        return StringIO.StringIO(self.cached_command(['log', '--all', '--pretty=%H']))

    def all_commits(self, prefix=""):
        """
        Returns a list of all commit hashes
        """
        commits = self._get_commits_iterator()

        if prefix:
            commits = iter([c for c in commits if c.startswith(prefix)])

        for commit in commits:
            yield commit.strip()

    def _get_commit_from_ref(self, ref):
        commit = self._pygit.revparse_single(ref)
        if isinstance(commit, Commit):
            return commit

        if hasattr(commit, "target"):
            return self._pygit[commit.target]

        return None

    def commit_of_ref(self, ref):
        """
        Returns the last commit of a ref.
        """
        # Check cache
        if ref in self._refs:
            return self._refs[ref]

        commit = self._get_commit_from_ref(ref)
        self._refs[ref] = ""
        if commit:
            self._refs[ref] = str(commit.id)

        return self._refs[ref]

    def commit_parents(self, commit):
        """
        Returns commit parents
        """
        parents = self._get_entry(commit).parents
        return [str(p.id) for p in parents]

    def commit_descendants(self, commit):
        """
        Returns commit descendants
        """
        return []

    def commit_names(self, commit):
        """
        Returns names associated with commit
        """
        return []

    def get_commit_time(self, commit):
        return self._get_entry(commit).commit_time

    def directory_contents(self, commit, path):
        """
        Returns the contents of the directory
        specified by `path`
        """

        tree = self._get_tree(commit, path)
        return [c[0] for c in tree]

    def is_symlink(self, commit, path):
        # the root of the repository can't be a symlink
        if not path:
            return False

        entry = self._get_entry(commit, path, return_tree=True)
        if entry.filemode == GIT_FILEMODE_LINK:
            return True

        return False

    def is_dir(self, commit, path):
        if commit in self._trees and path in self._trees[commit]:
            return True

        if commit not in self._trees:
            self._trees[commit] = set([''])
            self._trees_filled[commit] = set([''])
            self._cache_tree(commit, '')

        elements = path.split("/")
        for i in range(len(elements) - 1):
            subpath = "/".join(elements[:i + 1])
            if subpath in self._trees[commit] and subpath not in self._trees_filled[commit]:
                self._cache_tree(commit, subpath)

        return path in self._trees[commit]

    def file_contents(self, commit, path):
        try:
            return self._get_entry(commit, path).data
        except KeyError:
            return ""

    def file_size(self, commit, path):
        if not commit in self._sizes:
            self._sizes[commit] = {}

        if path in self._sizes[commit]:
            return self._sizes[commit][path]

        try:
            size = self._get_entry(commit, path).size
        except KeyError:
            size = 0

        self._sizes[commit][path] = size
        return size

    def author(self, commit):
        return self._get_entry(commit).author.name

    def author_email(self, commit):
        return self._get_entry(commit).author.email

class GitOperError(Exception):
    pass
