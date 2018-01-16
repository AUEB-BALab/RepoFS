#!/usr/bin/env python

import argparse
import errno
import datetime
import os

from time import time
from stat import S_IFDIR, S_IFREG, S_IFLNK
from fuse import FUSE, FuseOSError, Operations, fuse_get_context

from gitoper import GitOperations


class RepoFS(Operations):
    def __init__(self, repo, mount, nocache):
        self.repo = repo
        self.mount = mount
        self.nocache = nocache
        self._git = GitOperations(repo, not nocache, "giterr.log")

    def _month_days(self, year):
        """ Return an array with the number of days in each month
        for the given year. """
        days = []
        for month in range(1, 13):
            this_month = datetime.date(year, month, 1)
            next_month = (this_month.replace(day=28) +
                          datetime.timedelta(days=4))
            last_day = next_month - datetime.timedelta(days=next_month.day)
            days.append(last_day.day)
        return days

    def _get_root(self):
        return ['commits', 'branches', 'tags']

    def _get_branches(self):
        branches = self._git.branches()
        branches = [branch.split(" ")[1].split("/")[-1] for branch in branches]

        return branches

    def _get_tags(self):
        tags = self._git.tags()
        tags = [tag.split(" ")[1].split("/")[-1] for tag in tags]

        return tags

    def _verify_date_path(self, elements):
        """ Raise an exception if the elements array representing a commit
        date path [y, m, d] do not represent a valid date. """
        if len(elements) >= 1 and elements[0] not in self._git.years:
            raise FuseOSError(errno.ENOENT)
        if len(elements) >= 2 and elements[1] not in range(1, 13):
            raise FuseOSError(errno.ENOENT)
        if len(elements) >= 3 and elements[2] not in range(1, self._month_days(
                elements[0])[elements[1] - 1] + 1):
            raise FuseOSError(errno.ENOENT)

    def _string_list(self, l):
        """ Return list l as a list of strings """
        return [str(x) for x in l]

    def _get_commits(self, path):
        """ Return directory entries for path elements under the /commits
        entry. """

        elements = path.split("/", 5)[2:]
        elements[:3] = [int(x) for x in elements[:3]]
        self._verify_date_path(elements[:3])
        # Precondition: path represents a valid date
        if len(elements) == 0:
            # /commits
            return self._string_list(self._git.years)
        elif len(elements) == 1:
            # /commits/yyyy
            return self._string_list(range(1, 13))
        elif len(elements) == 2:
            # /commits/yyyy/mm
            return self._string_list(_month_days(elements[0])[elements[1] - 1])
        elif len(elements) == 3:
            # /commits/yyyy/mm/dd
            return self._git.commits(elements[0], elements[1],
                                             elements[2])
        else:
            if len(elements) < 5:
                elements.append('')
            # /commits/yyyy/mm/dd/hash
            if elements[4] in self._commit_metadata_folders():
                return self._get_metadata_folder(path)
            else:
                dirents = self._git.directory_contents(elements[3],
                                                       elements[4])
                if elements[4] == '': # on the root of a commit folder
                    dirents += self._commit_metadata_names()
                return dirents

    def _commit_metadata_names(self):
        return ['.git-log', '.git-parents', '.git-descendants', '.git-names']

    def _commit_metadata_folders(self):
        return ['.git-parents', '.git-descendants', '.git-names']

    def _commit_metadata_files(self):
        return ['.git-log']

    def _get_metadata_content(self, path):
        commit = self._commit_from_path(path)
        metaname = self._git_path(path)

        if metaname == '.git-log':
            return self._git.commit_log(commit)
        else:
            return ""

    def _get_metadata_folder(self, path):
        commit = self._commit_from_path(path)
        metaname = self._git_path(path)

        if metaname == '.git-parents':
            return self._git.commit_parents(commit)
        elif metaname == '.git-descendants':
            return self._git.commit_descendants(commit)
        elif metaname == '.git-names':
            return self._git.commit_names(commit)
        else:
            return []


    def _commit_from_branch(self, branch):
        return self._git.last_commit_of_branch(branch)

    def _commit_from_tag(self, tag):
        return self._git.commit_of_tag(tag)

    def _git_path(self, path):
        """ Return the path underneath a git commit directory.
            For example, the path of /commits/2017/12/28/ed34f8.../src/foo
            is src/foo.  """
        if path.count("/") == 5:
            return ""
        else:
            return path.split("/", 6)[-1]

    def _is_symlink(self, path):
        if path.startswith("/commits/") and\
                path.split("/")[-2] in self._commit_metadata_folders() and\
                path.split("/")[-1] in self._get_commits():
            return True

        if path.startswith("/branches") and path.count("/") == 2:
            return True

        if path.startswith("/tags") and path.count("/") == 2:
            return True

        return False

    def _target_from_symlink(self, path):
        if path.startswith("/commits/"):
            return os.path.join(self.mount, "commits", path.split("/")[-1] + "/")

        if path.startswith("/branches/"):
            return os.path.join(self.mount, "commits", self._commit_from_branch(path.split("/")[-1]) + "/")

        if path.startswith("/tags/"):
            return os.path.join(self.mount, "commits", self._commit_from_tag(path.split("/")[-1]) + "/")

    def _commit_from_path(self, path):
        if path.count("/") < 5:
            return ""

        return path.split("/", 6)[5]

    def _is_dir(self, path):
        if path == "/":
            return True

        elements = path.split("/", 6)[1:]
        if elements[0] == 'commits':
            elements[1:4] = [int(x) for x in elements[1:4]]
            self._verify_date_path(elements[1:4])
            if len(elements) < 5:
                return True
            elif len(elements) == 5:
                # Includes commit hash
                return elements[4] in self._git.commits(
                    elements[1], elements[2], elements[3])
            elif elements[5] in self._commit_metadata_files():
                return False
            elif elements[5] in self._commit_metadata_folders():
                return True
            else:
                return self._git.is_dir(elements[4], elements[5])
        elif elements == ['branches']:
            return True
        elif elements == ['tags']:
            return True
        return False

    def _get_file_size(self, path):
        if self._git_path(path) in self._commit_metadata_files():
            return len(self._get_metadata_content(path))

        return self._git.file_size(self._commit_from_path(path), self._git_path(path))

    def _get_file_contents(self, path):
        if self._git_path(path) in self._commit_metadata_files():
            return self._get_metadata_content(path)

        return self._git.file_contents(self._commit_from_path(path), self._git_path(path))

    def getattr(self, path, fh=None):
        uid, gid, pid = fuse_get_context()
        st = dict(st_uid=uid, st_gid=gid)
        if self._is_dir(path):
            st['st_mode'] = (S_IFDIR | 0o440)
            st['st_nlink'] = 2
        elif self._is_symlink(path):
            st['st_mode'] = (S_IFLNK | 0o777)
            st['st_nlink'] = 1
            st['st_size'] = len(self._target_from_symlink(path))
        else:
            st['st_mode'] = (S_IFREG | 0o440)
            st['st_size'] = self._get_file_size(path)

        st['st_ctime'] = st['st_mtime'] = st['st_atime'] = time()
        return st

    def readdir(self, path, fh):
        dirents = ['.', '..']
        if path == "/":
            dirents.extend(self._get_root())
        elif path.startswith("/commits"):
            dirents.extend(self._get_commits(path))
        elif path == "/branches":
            dirents.extend(self._get_branches())
        elif path == "/tags":
            dirents.extend(self._get_tags())

        for r in dirents:
            yield r


    def read(self, path, size, offset, fh):
        contents = self._get_file_contents(path)

        return contents[offset:offset + size]


    def readlink(self, path):
        return self._target_from_symlink(path)


    statfs=None

    access=None
    chmod=None
    chown=None
    mknod=None
    rmdir=None
    mkdir=None
    unlink=None
    symlink=None
    rename=None
    link=None
    utimens=None


def main(repo, mount, nocache):
    if not os.path.exists(os.path.join(repo, '.git')):
        raise Exception("Not a git repository")

    FUSE(RepoFS(repo, mount, nocache), mount, nothreads=True, foreground=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="Git repository to be processed.")
    parser.add_argument("mount", help="Path where the FileSystem will be mounted." \
    "If it doesn't exist it is created and if it exists and contains files RepoFS exits.")
    parser.add_argument(
        "-nocache",
        "--nocache",
        help="Do not cache repository metadata. FileSystem updates when the repository changes.",
        action="store_true",
        default=False
    )
    args = parser.parse_args()

    main(args.repo, args.mount, args.nocache)

