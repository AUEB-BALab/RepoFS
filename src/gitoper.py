import datetime
import os
import re
import sys

from subprocess import check_output, CalledProcessError, call
from pygit2 import Repository, Commit, GIT_OBJ_TREE


class GitOperations(object):
    def __init__(self, repo, caching, errpath="giterr.log"):
        self.repo = repo
        self._gitrepo = os.path.join(repo, '.git')
        self._pygit = Repository(repo)
        self._errfile = open(errpath, "w+", 0)
        self._commands = {}
        self._caching = caching
        self._trees = {}
        self._trees_filled = {}
        self._sizes = {}
        self._tags = {}
        self._branches = {}
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
                out = check_output(list, stderr=self._errfile)
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
                    self._errfile.write(message)
                    out = None
            if self._caching:
                self._commands[command] = out
            return out

    def _get_entry(self, obj):
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
            tree = self._get_entry(self._pygit[commit].tree)
        else:
            path += "/"
            try:
                tree = self._get_entry(self._pygit[commit].tree[path])
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

	# Obtain head branch
	head_branch = self.cached_command(['config', '--name-only',
	  '--get-regexp', 'branch.*remote'], return_exit_code = False,
	  silent=True)
	if head_branch:
	  head_branch = re.sub(r'^branch\.(.*)\.remote\n$', r'\1', head_branch)
	else:
	  head_branch = 'master'

        first_years = self.cached_command(['log', '--max-parents=0',
                                         '--date=format:%Y',
                                         '--pretty=%ad',
                                         head_branch]
                                         ).splitlines()
        return int(sorted(first_years)[0])

    def _last_year(self):
        """
        Returns the year of the repo's last commit
        """
        most_recent_branch = self.cached_command(['branch', '-a',
          '--sort=-committerdate']).splitlines()[0]
	# Remote leading * (for HEAD) and spaces
	most_recent_branch = re.sub(r'^\*?\s+', r'', most_recent_branch)
        return int(self.cached_command(['log', '-n', '1',
                                         '--date=format:%Y',
                                         '--pretty=%ad',
                                         most_recent_branch]
                                         ))

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

    def _format_to_link(self, commit):
        time = datetime.datetime.fromtimestamp(commit.commit_time).strftime("%Y/%m/%d")
        return "../commits/%s/%s" % (time, commit.id)

    def _get_commit_from_ref(self, ref):
        commit = self._pygit.revparse_single(ref)
        if isinstance(commit, Commit):
            return commit

        if hasattr(commit, "target"):
            return self._pygit[commit.target]

        return None

    def last_commit_of_branch(self, branch):
        """
        Returns the last commit of a branch.
        """
        if branch in self._branches:
            return self._branches[branch]

        commit = self._get_commit_from_ref(branch)
        path = ""
        if commit:
            path = self._format_to_link(commit)

        self._branches[branch] = path
        return path

    def commit_of_tag(self, tag):
        """
        Returns the commit of a tag.
        """
        if tag in self._tags:
            return self._tags[tag]

        commit = self._get_commit_from_ref(tag)
        path = ""
        # tag is pointing to a commit
        if commit:
            path = self._format_to_link(commit)

        self._tags[tag] = path
        return path

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

        tree = self._get_tree(commit, path)
        return [c[0] for c in tree]

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
            return self._get_entry(self._pygit[commit].tree[path]).data
        except KeyError:
            return ""

    def file_size(self, commit, path):
        if not commit in self._sizes:
            self._sizes[commit] = {}

        if path in self._sizes[commit]:
            return self._sizes[commit][path]

        try:
            size = self._get_entry(self._pygit[commit].tree[path]).size
        except KeyError:
            size = 0

        self._sizes[commit][path] = size
        return size
