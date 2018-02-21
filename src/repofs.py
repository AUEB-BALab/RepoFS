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

import argparse
import errno
import datetime
import os
import sys

from time import time
from stat import S_IFDIR, S_IFREG, S_IFLNK
from fuse import FUSE, FuseOSError, Operations, fuse_get_context

from gitoper import GitOperations, GitOperError


class RepoFS(Operations):
    def __init__(self, repo, mount, nocache):
        self.repo = repo
        self.mount = mount
        self.nocache = nocache
        self._git = GitOperations(repo, not nocache, "giterr.log")
        self._branch_refs = ['refs/heads/', 'refs/remotes/']
        self._tag_refs = ['refs/tags']

    def _days_per_month(self, year):
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

    def _month_dates(self, year, month):
        """ Return an array with the dates in the given year and month
        The month is 1-based.
        """
        return range(1, self._days_per_month(year)[month - 1] + 1)

    def _get_root(self):
        return ['commits-by-date', 'commits-by-hash', 'branches', 'tags']

    def _path_to_refs(self, path):
        """Convert path into a list of Git refs.
        /branch paths will start after the branch so as to include
        heads or remotes.
        /tags paths will start from the beginning, because this is
        the name under which tags are stored."""
        if path.startswith('/branches'):
            return path.split('/')[2:]
        elif path.startswith('/tags'):
            return path.split('/')[1:]
        else:
            # Internal error
            raise FuseOSError(errno.EIO)

    def _is_ref(self, path, refs):
        """Return true if the specified path (e.g. branches/master, or
        tags/V1.0) refers to one of the specified refs, (e.g.
        refs/heads or refs/tags). """
        path = self._path_to_refs(path)
        for ref in self._git.refs(refs):
            ref = ref.split('/')[1:]
            # print('Check path [%s] == ref [%s]' % (path, ref))
            if path == ref:
                return True
        return False

    def _is_ref_prefix(self, path, refs):
        """Return true if the specified path refers to a ref name prefix
        up to a path separator for the specified refs, e.g.
        refs/heads or refs/tags. """
        path = self._path_to_refs(path)
        for ref in self._git.refs(refs):
            ref = ref.split('/')[1:]
            if path == ref[:len(path)] and len(path) < len(ref):
                return True
        return False

    def _get_refs(self, path, refs):
        """Return the ref elements that match the specified path and
        refs, e.g. refs/heads or refs/tags. """
        # print("path is %s" % path)
        path = self._path_to_refs(path)
        result = set()
        found = False
        # Find common prefix
        for ref in self._git.refs(refs):
            ref = ref.split('/')[1:]
            # print('Look for path [%s] in ref [%s]' % (path, ref))
            if path == ref[:len(path)]:
                # Common prefix found
                found = True
                if len(ref) > len(path):
                    # print("append %s" % (ref[len(path)]))
                    result.add(ref[len(path)])

        if not found:
            raise FuseOSError(errno.ENOTDIR)
        return result

    def _verify_date_path(self, elements):
        """ Raise an exception if the elements array representing a commit
        date path [y, m, d] do not represent a valid date. """
        if len(elements) >= 1 and elements[0] not in self._git.years:
            raise FuseOSError(errno.ENOENT)
        if len(elements) >= 2 and elements[1] not in range(1, 13):
            raise FuseOSError(errno.ENOENT)
        if len(elements) >= 3 and elements[2] not in range(1, self._days_per_month(
                elements[0])[elements[1] - 1] + 1):
            raise FuseOSError(errno.ENOENT)

    def _string_list(self, l):
        """ Return list l as a list of strings """
        return [str(x) for x in l]

    def _get_commits_from_path_list(self, elements):
        """ Given a path's elements starting from a commit's hash
        return the corresponding contents of a commits directory.  """
        if len(elements) < 2:
            elements.append('')

        # root isn't a commit hash
        if elements[0] not in self._git.all_commits():
            raise FuseOSError(errno.ENOENT)

        # Last two elements from /commits-by-hash/hash or
        # /commits-by-date/yyyy/mm/dd/hash
        if elements[1] in self._commit_metadata_folders():
            return self._get_metadata_folder(elements[0], elements[1])
        else:
            try:
                dirents = self._git.directory_contents(elements[0],
                                                       elements[1])
            except GitOperError:
                raise FuseOSError(errno.ENOTDIR)
            if elements[1] == '': # on the root of a commit folder
                dirents += self._commit_metadata_names()
            return dirents

    def _dates_to_int(self, dates):
        # if not integers raise OSError
        try:
            return [int(x) for x in dates]
        except ValueError:
            raise FuseOSError(errno.ENOENT)

    def _get_commits_by_date(self, path):
        """ Return directory entries for path elements under the
        /commits-by-date entry. """

        elements = path.split("/", 6)[2:]
        # Remove trailing empty slash
        if len(elements) > 0 and elements[-1] == '':
            del elements[-1]

        elements[:3] = self._dates_to_int(elements[:3])

        self._verify_date_path(elements[:3])
        # Precondition: path represents a valid date
        if len(elements) == 0:
            # /commits-by-date
            return self._string_list(self._git.years)
        elif len(elements) == 1:
            # /commits-by-date/yyyy
            return self._string_list(range(1, 13))
        elif len(elements) == 2:
            # /commits-by-date/yyyy/mm
            return self._string_list(self._month_dates(elements[0],
                                                       elements[1]))
        elif len(elements) == 3:
            # /commits-by-date/yyyy/mm/dd
            return self._git.commits_by_date(elements[0], elements[1],
                                             elements[2])
        else:
            # /commits-by-date/yyyy/mm/dd/hash
            return self._get_commits_from_path_list(elements[3:])

    def _get_commits_by_hash(self, path):
        """ Return directory entries for path elements under the
        /commits-by-hash entry. """

        elements = path.split("/", 3)[2:]
        # Remove trailing empty slash
        if len(elements) > 0 and elements[-1] == '':
            del elements[-1]
        if len(elements) == 0:
            # /commits-by-hash
            return self._git.all_commits()
        else:
            # /commits-by-hash/hash
            return self._get_commits_from_path_list(elements)

    def _commit_metadata_names(self):
        return self._commit_metadata_folders()

    def _commit_metadata_folders(self):
        return ['.git-parents', '.git-descendants', '.git-names']

    def _get_metadata_folder(self, commit, metaname):
        if metaname == '.git-parents':
            return self._git.commit_parents(commit)
        elif metaname == '.git-descendants':
            return self._git.commit_descendants(commit)
        elif metaname == '.git-names':
            return self._git.commit_names(commit)
        else:
            return []

    def _commit_from_ref(self, ref):
        return self._git.commit_of_ref(ref)

    def _git_path(self, path):
        """ Return the path underneath a git commit directory.
            For example, the path of /commits-by-date/2017/12/28/ed34f8.../src/foo
            is src/foo.  """
        if path.startswith("/commits-by-date/"):
            if path.count("/") == 5:
                return ""
            else:
                return path.split("/", 6)[-1]
        elif path.startswith('/commits-by-hash/'):
            if path.count("/") == 2:
                return ""
            else:
                return path.split("/", 3)[-1]
        else:
            raise FuseOSError(errno.ENOENT)

    def _is_symlink(self, path):
        if (path.startswith("/commits-by-date/")  and
                path.split("/")[-2] in self._commit_metadata_folders() and
                path.split("/")[-1] in self._git.all_commits()):
            # XXX Must also check number of slashes
            return True
        elif (path.startswith("/commits-by-hash/") and
                path.split("/")[-2] in self._commit_metadata_folders() and
                path.split("/")[-1] in self._git.all_commits()):
            return True
        elif path.startswith("/branches") and self._is_ref(path,
                                                           self._branch_refs):
            return True
        elif path.startswith("/tags") and self._is_ref(path, self._tag_refs):
            return True
        return False

    def _target_from_symlink(self, path):
        if path.startswith("/commits-by-date/"):
            return os.path.join(self.mount, "commits-by-hash", path.split("/")[-1] + "/")
        elif path.startswith("/commits-by-hash/"):
            return os.path.join(self.mount, "commits-by-hash", path.split("/")[-1] + "/")
        elif path.startswith("/branches/"):
            return self._commit_from_ref(path[10:]) + '/'
        elif path.startswith("/tags/"):
            return self._commit_from_ref(path[6:]) + '/'
        else:
            raise FuseOSError(errno.ENOENT)

    def _commit_from_path(self, path):
        if path.startswith("/commits-by-date/"):
            if path.count("/") < 5:
                return ""
            else:
                return path.split("/", 6)[5]
        elif path.startswith('/commits-by-hash/'):
            if path.count("/") < 2:
                return ""
            else:
                return path.split("/", 3)[2]
        else:
            raise FuseOSError(errno.ENOENT)


    def _is_dir(self, path):
        if path == "/":
            return True

        elements = path.split("/", 6)[1:]
        if elements[0] == 'commits-by-date':
            elements[1:4] = self._dates_to_int(elements[1:4])
            self._verify_date_path(elements[1:4])
            if len(elements) < 5:
                return True
            elif len(elements) == 5:
                # Includes commit hash
                return elements[4] in self._git.commits_by_date(
                    elements[1], elements[2], elements[3])
            elif elements[5] in self._commit_metadata_folders():
                return True
            else:
                return self._git.is_dir(elements[4], elements[5])
        elif elements[0] == 'commits-by-hash':
            if len(elements) < 2:
                return True
            elif len(elements) == 2:
                # Includes commit hash
                return elements[1] in self._git.all_commits()
            elif elements[2] in self._commit_metadata_folders():
                if len(elements) == 4:
                    return False
                return True
            else:
                return self._git.is_dir(elements[1], "/".join(elements[2:]))
        elif elements in [['branches'], ['tags']]:
            return True
        elif elements[0] == 'branches':
            return self._is_ref_prefix(path, self._branch_refs)
        elif elements[0] == 'tags':
            return self._is_ref_prefix(path, self._tag_refs)
        return False

    def _get_file_size(self, path):
        try:
            return self._git.file_size(self._commit_from_path(path), self._git_path(path))
        except GitOperError:
            raise FuseOSError(errno.ENOENT)

    def _get_file_contents(self, path):
        try:
            return self._git.file_contents(self._commit_from_path(path), self._git_path(path))
        except GitOperError:
            raise FuseOSError(errno.ENOENT)

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
        elif path.startswith("/commits-by-date"):
            dirents.extend(self._get_commits_by_date(path))
        elif path.startswith("/commits-by-hash"):
            dirents.extend(self._get_commits_by_hash(path))
        elif path.startswith('/branches'):
            dirents.extend(self._get_refs(path, self._branch_refs))
        elif path.startswith('/tags'):
            dirents.extend(self._get_refs(path, self._tag_refs))
        else:
            raise FuseOSError(errno.ENOENT)

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


def main():
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

    if not os.path.exists(os.path.join(args.repo, '.git')):
        raise Exception("Not a git repository")

    sys.stderr.write("Examining repository.  Please wait..\n")
    start = datetime.datetime.now()
    repo = RepoFS(args.repo, args.mount, args.nocache)
    end = datetime.datetime.now()
    sys.stderr.write("Ready! Repository mounted in %s\n" % (end - start))
    sys.stderr.write("Repository %s is now visible at %s\n" % (args.repo,
                                                               args.mount))
    FUSE(repo, args.mount, nothreads=True, foreground=True)

if __name__ == '__main__':
    main()
