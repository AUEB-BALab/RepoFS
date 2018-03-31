import utils
import errno

from fuse import FuseOSError
from itertools import product

from commit_handler import CommitHandler

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
                    raise FuseOSError(errno.ENOENT)

    def _verify_commit(self):
        if (self.path_data['commit'] \
                and self.path_data['commit'] not in self.oper.all_commits()):
            raise FuseOSError(errno.ENOENT)

    def _get_commit_content(self):
        # root isn't a commit hash
        if self.path_data['commit'] not in self.oper.all_commits():
            raise FuseOSError(errno.ENOENT)

        if self._is_metadata_dir():
            return self._get_metadata_dir(self.path_data['commit'])

        try:
            dirents = self.oper.directory_contents(self.path_data['commit'], self.path_data['commit_path'])
        except GitOperError:
            raise FuseOSError(errno.ENOTDIR)

        if not self.path_data['commit_path']:
            dirents += self._get_metadata_names()

        return dirents

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
        if not self.path_data['commit_path'] or self._is_metadata_dir():
            return False
        if self._is_metadata_symlink():
            return True
        return self.oper.is_symlink(self.path_data['commit'], self.path_data['commit_path'])

    def file_contents(self):
        return self.oper.file_contents(self.path_data['commit'], self.path_data['commit_path'])

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
