import datetime
import os
import sys

from subprocess import check_output, CalledProcessError, call
from pygit2 import Repository, GIT_OBJ_TREE


class GitOperations(object):
    def __init__(self, repo, caching, errpath="giterr.log"):
        self.repo = repo
        self._gitrepo = os.path.join(repo, '.git')
        self._pygit = Repository(repo)
        self._errfile = open(errpath, "w+", 0)
        self._cache = {}
        self._caching = caching
        self._trees = {}
        self._sizes = {}
        self.years = range(self._first_year(), self._last_year() + 1)
        # A format for links to link back to commits
        self._link_format = ['--format=../commits/%cd/%H',
                             '--date=format:%Y/%m/%d', '--']

    def cached_command(self, list, return_exit_code=False):
        """
        Executes the specified git command and returns its result.
        Subsequent executions of the same command return the cached result
        If return_exit_code is set, then the return value is True of False
        depending on whether the command exited with 0 or not.
        """

        list = ['git', '--git-dir', self._gitrepo] + list
        command = " ".join(list)
        if command in self._cache:
            return self._cache[command]
        else:
            try:
                # print(command)
                out = check_output(list, stderr=self._errfile)
                if return_exit_code:
                    out = True
            except CalledProcessError as e:
                if return_exit_code:
                    out = False
                else:
                    message = "Error calling %s: %s" % (command, str(e))
                    sys.stderr.write(message)
                    self._errfile.write(message)
                    out = None
            if self._caching:
                self._cache[command] = out
            return out

    def _get_entry(self, obj):
        return self._pygit[obj.id]

    def fill_trees(self, commit, contents):
        if not commit in self._trees:
            self._trees[commit] = set([''])

        trees = []
        for cont in contents:
            if cont[1] == "tree" and cont[0] not in self._trees[commit]:
                trees.append(cont[0])

        self._trees[commit].update(trees)

    def _first_year(self):
        """
        Returns the year of the repo's first commit(s)
        Not implemented using pygit2 because its faster
        to get the year via shell command and it creates
        only one process on boot time.
        """
        first_years = self.cached_command(['log', '--max-parents=0',
                                         '--date=format:%Y',
                                         '--pretty=%ad',
                                         'master']
                                         ).splitlines()
        return int(sorted(first_years)[0])

    def _last_year(self):
        """
        Returns the year of the repo's last commit
        """
        return datetime.datetime.fromtimestamp(
            self._pygit[self._pygit.head.target].commit_time
        ).year

    def branches(self):
        """
        Returns branches in the form:
        <commit_hash> refs/heads/<branchname>
        """
        branchrefs = self.cached_command(['for-each-ref',
                '--format=%(objectname) %(refname)', 'refs/heads/']
                                         ).splitlines()
        branches = [ref.strip() for ref in branchrefs]
        return branches

    def tags(self):
        """
        Returns tags in the form:
        <commit_hash> refs/tags/<tagname>
        """
        tagrefs = self.cached_command(['for-each-ref',
                '--format=%(objectname) %(refname)', 'refs/tags/']
                                      ).splitlines()
        tags = [ref.strip() for ref in tagrefs]
        return tags

    def commits(self, y, m, d):
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
                                       '--pretty=%H']).splitlines()
        commits = [commit.strip() for commit in commits]
        return commits

    def last_commit_of_branch(self, branch):
        """
        Returns the last commit of a branch.
        """
        commit = self.cached_command(['log', '-n', '1', branch] +
                                     self._link_format
                                     ).strip()
        return commit

    def commit_of_tag(self, tag):
        """
        Returns the commit of a tag.
        """
        commit = self.cached_command(['log', '-n', '1', tag] +
                                     self._link_format
                                     ).strip()
        return commit

    def commit_log(self, commit):
        """
        Returns commit log
        """
        return check_output(
            ['git', '--git-dir', self._gitrepo, 'log', commit],
            stderr=self._errfile
        )

    def commit_parents(self, commit):
        """
        Returns commit parents
        """
        return []

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

    def directory_contents(self, commit, path):
        """
        Returns the contents of the directory
        specified by `path`
        """
        if not path:
            tree = self._get_entry(self._pygit[commit].tree)
        else:
            path += "/"
            try:
                tree = self._get_entry(self._pygit[commit].tree[path])
            except KeyError:
                return []

        contents = [c.name for c in tree]

        paths_and_names = [(os.path.join(path, c.name), c.type) for c in tree]
        self.fill_trees(commit, paths_and_names)

        return contents

    def is_dir(self, commit, path):
        if commit in self._trees and path in self._trees[commit]:
            return True

        try:
            return self._get_entry(self._pygit[commit].tree[path]).type == GIT_OBJ_TREE
        except KeyError:
            return False

    def file_contents(self, commit, path):
        try:
            return self._get_entry(self._pygit[commit].tree[path]).data
        except KeyError:
            return ""

    def file_size(self, commit, path):
        if not commit in self._sizes:
            self._sizes[commit] = {}

        if path in self._sizes[commit]:
            return self._sizes[commit][path]

        contents = self.file_contents(commit, path)
        size = 0
        if contents:
            size = len(contents)

        self._sizes[commit][path] = size
        return size
