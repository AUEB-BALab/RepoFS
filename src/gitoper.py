import os

from subprocess import check_output, CalledProcessError, call


class GitOperations(object):
    def __init__(self, repo, errpath="giterr.log"):
        self.repo = repo
        self._gitrepo = os.path.join(repo, '.git')
        self._errfile = open(errpath, "w+", 0)

    def branches(self):
        """
        Returns branches in the form:
        <commit_hash> refs/heads/<branchname>
        """
        try:
            branchrefs = check_output(['git', '--git-dir', self._gitrepo, 'for-each-ref',\
                    '--format=%(objectname) %(refname)', 'refs/heads/'],
                    stderr=self._errfile).splitlines()
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
            tagrefs = check_output(['git', '--git-dir', self._gitrepo, 'for-each-ref',\
                    '--format=%(objectname) %(refname)', 'refs/tags/'],
                    stderr=self._errfile).splitlines()
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
            commits = check_output(['git', '--git-dir', self._gitrepo,\
                    'log', '--pretty=format:%H'],
                    stderr=self._errfile).splitlines()
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
            commit = check_output(['git', '--git-dir', self._gitrepo,\
                    'rev-list', '-n', '1', branch],
                    stderr=self._errfile).strip()
            return commit
        except CalledProcessError as e:
            print "last commit of branch error: %s" % str(e)
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
            contents = check_output(['git', '--git-dir', self._gitrepo, 'ls-tree',\
                    '--name-only', commit, path], stderr=self._errfile).splitlines()

            contents = [c.split("/")[-1] for c in contents]
            return contents
        except CalledProcessError as e:
            print "directory_contents error: %s" % str(e)
            return []

    def is_dir(self, commit, path):
        try:
            object_type = check_output(['git', '--git-dir', self._gitrepo, 'cat-file',\
                    '-t', "%s:%s" % (commit, path)], stderr=self._errfile).strip()
            if object_type == "tree":
                return True

            return False
        except CalledProcessError as e:
            return False

    def file_contents(self, commit, path):
        if not self.path_exists(commit, path):
            return ""

        return check_output(['git', '--git-dir', self._gitrepo, 'show',\
                "%s:%s" % (commit, path)], stderr=self._errfile)

    def file_size(self, commit, path):
        contents = self.file_contents(commit, path)
        if not contents:
            return 0

        return len(contents)

    def path_exists(self, commit, path):
        try:
            check_output(['git', '--git-dir', self._gitrepo, 'cat-file',\
                    '-e', "%s:%s" % (commit, path)], stderr=self._errfile)
            return True
        except CalledProcessError as e:
            return False
