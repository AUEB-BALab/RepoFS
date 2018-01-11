import os
import sys

from subprocess import check_output, CalledProcessError, call


class GitOperations(object):
    def __init__(self, repo, caching, errpath="giterr.log"):
        self.repo = repo
        self._gitrepo = os.path.join(repo, '.git')
        self._errfile = open(errpath, "w+", 0)
        self._cache = {}
        self._caching = caching

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

    def branches(self):
        """
        Returns branches in the form:
        <commit_hash> refs/heads/<branchname>
        """
        try:
            branchrefs = self.cached_command(['for-each-ref',
                    '--format=%(objectname) %(refname)', 'refs/heads/']
                                             ).splitlines()
            branches = [ref.strip() for ref in branchrefs]
            return branches
        except CalledProcessError as e:
            print "branches error: %s" % str(e)
            return None

    def tags(self):
        """
        Returns tags in the form:
        <commit_hash> refs/tags/<tagname>
        """
        try:
            tagrefs = self.cached_command(['for-each-ref',
                    '--format=%(objectname) %(refname)', 'refs/tags/']
                                          ).splitlines()
            tags = [ref.strip() for ref in tagrefs]
            return tags
        except CalledProcessError as e:
            print "tags error: %s" % str(e)
            return None

    def commits(self):
        """
        Returns a list of commit hashes
        """
        try:
            commits = self.cached_command(['log', '--pretty=format:%H']
                                          ).splitlines()
            commits = [commit.strip() for commit in commits]
            return commits
        except CalledProcessError as e:
            print "commits error: %s" % str(e)
            return None

    def last_commit_of_branch(self, branch):
        """
        Returns the last commit of a branch.
        """
        try:
            commit = self.cached_command(['rev-list', '-n', '1', branch, '--']
                                         ).strip()
            return commit
        except CalledProcessError as e:
            print "last commit of branch error: %s" % str(e)
            return None

    def commit_of_tag(self, tag):
        """
        Returns the commit of a tag.
        """
        try:
            commit = self.cached_command(['rev-list', '-n', '1', tag, '--']
                                         ).strip()
            return commit
        except CalledProcessError as e:
            print "commit of tag error: %s" % str(e)
            return None

    def commit_log(self, commit):
        """
        Returns commit log
        """
        try:
            return check_output(
                ['git', '--git-dir', self._gitrepo, 'log', commit],
                stderr=self._errfile
            )
        except CalledProcessError as e:
            print "commit_log error: %s" % str(e)
            return None

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
        if path:
            path += "/"

        if not self.path_exists(commit, path):
            return []

        try:
            contents = self.cached_command(['ls-tree',
                    '--name-only', commit, path]).splitlines()

            contents = [c.split("/")[-1] for c in contents]
            return contents
        except CalledProcessError as e:
            print "directory_contents error: %s" % str(e)
            return []

    def is_dir(self, commit, path):
        try:
            object_type = self.cached_command(['cat-file', '-t',
                                               '--allow-unknown-type',
                                               "%s:%s" % (commit, path)]).strip()
            return object_type == "tree"
        except CalledProcessError as e:
            return False

    def file_contents(self, commit, path):
        if not self.path_exists(commit, path):
            return ""

        return check_output(['git', '--git-dir', self._gitrepo, 'show',
                "%s:%s" % (commit, path)], stderr=self._errfile)

    def file_size(self, commit, path):
        contents = self.file_contents(commit, path)
        if not contents:
            return 0

        return len(contents)

    def path_exists(self, commit, path):
        return self.cached_command(['cat-file', '-e', "%s:%s" % (commit, path)], True)
