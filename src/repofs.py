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
from itertools import product
from stat import S_IFDIR, S_IFREG, S_IFLNK, S_IWUSR
from fuse import FUSE, FuseOSError, Operations, fuse_get_context

from gitoper import GitOperations, GitOperError


class RepoFS(Operations):
    _HASH_GIT_START = 2
    _HASH_GIT_START_TREE = 5

    def __init__(self, repo, mount, hash_trees, no_ref_symlinks, nocache):
        self.repo = repo
        self.repo_mode = os.stat(repo).st_mode
        self.no_ref_symlinks = no_ref_symlinks
        # remove write permission and directory flag
        self.mnt_mode = self.repo_mode & ~S_IWUSR & ~S_IFDIR
        self.mount = mount
        self.nocache = nocache
        self.hash_trees = hash_trees
        self.git_start = self._HASH_GIT_START
        self._hex = self._get_hex()
        if self.hash_trees:
            self.git_start = self._HASH_GIT_START_TREE
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

    def _path_to_refs(self, path, refs):
        """Convert path into a list of Git refs.
        /branch paths will start after the branch so as to include
        heads or remotes.
        /tags paths will start from the beginning, because this is
        the name under which tags are stored.
        If a ref exists inside the path, returns the ref,
        otherwise it returns the part of the path after branches"""
        if path.startswith('/branches'):
            path = path.split('/')[2:]
        elif path.startswith('/tags'):
            path = path.split('/')[1:]
        else:
            # Internal error
            raise RepoFSError("Invalid path")

        if len(path) > 1 and self.no_ref_symlinks:
            # check if the path contains a full ref
            for ref in self._git.refs(refs):
                ref = ref.split('/')[1:]
                if len(path) > len(ref) and "/".join(path).startswith("/".join(ref)):
                    return ref

        return path

    def _is_ref(self, path, refs=None):
        """Return true if the specified path (e.g. branches/master, or
        tags/V1.0) refers to one of the specified refs, (e.g.
        refs/heads or refs/tags). """
        if not refs:
            refs = self._branch_refs + self._tag_refs
        path = self._path_to_refs(path, refs)
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
        path = self._path_to_refs(path, refs)
        for ref in self._git.refs(refs):
            ref = ref.split('/')[1:]
            if path == ref[:len(path)] and len(path) < len(ref):
                return True
        return False

    def _get_branch_ref_limit(self, path, refs):
        """
        Returns the path position where the ref path ends.
        """
        # prefix: heads/master
        # /branches/heads/
        # whole path /branches/heads/master/.../
        if self._is_ref(path, refs):
            # /branches/ref/path
            # ref is heads/master
            return len(self._path_to_refs(path, refs)) + 1
        else:
            # /branches/heads
            return path.count("/")

    def _get_tag_ref_limit(self, path, refs):
        if self._is_ref(path, refs):
            return len(self._path_to_refs(path, refs))
        else:
            return path.count("/")

    def _get_branches(self, path):
        elements = path.split("/")
        if elements[1] != "branches":
            raise RepoFSError("_get_branches called with invalid path")

        if len(elements) == 2:
            return self._get_refs(path, self._branch_refs)

        if elements[2] == "heads" or elements[2] == "remotes":
            ref_limit = self._get_branch_ref_limit(path, self._branch_refs)
        else:
            raise FuseOSError(errno.ENOENT)

        if self._is_ref_prefix(path, self._branch_refs):
            return self._get_refs(path, self._branch_refs)
        elif len(elements) > ref_limit and self.no_ref_symlinks:
            ref = "/".join(elements[2:ref_limit+1])
            cpath = "/".join(elements[ref_limit+1:])
            return self._get_commit_content_by_ref(ref, cpath)
        else:
            raise FuseOSError(errno.ENOENT)

    def _get_tags(self, path):
        elements = path.split("/")
        if elements[1] != "tags":
            raise RepoFSError("_get_tags called with invalid path")

        if len(elements) == 2:
            return self._get_refs(path, self._tag_refs)

        ref_limit = self._get_tag_ref_limit(path, self._tag_refs)
        if self._is_ref_prefix(path, self._tag_refs):
            return self._get_refs(path, self._tag_refs)
        elif len(elements) > ref_limit and self.no_ref_symlinks and self._is_ref(path):
            ref = "/".join(elements[1:ref_limit+1])
            cpath = "/".join(elements[ref_limit+1:])
            return self._get_commit_content_by_ref(ref, cpath)
        else:
            raise FuseOSError(errno.ENOENT)

    def _get_commit_content_by_ref(self, ref, cpath):
        commit = self._commit_from_ref(ref)
        elements = [commit, cpath]
        return self._get_commits_from_path_list(elements)

    def _get_refs(self, path, refs):
        """Return the ref elements that match the specified path and
        refs, e.g. refs/heads or refs/tags. """
        # print("path is %s" % path)
        path = self._path_to_refs(path, refs)
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

    def _verify_hash_path(self, elements):
        for elem in elements:
            if elem not in self._hex:
                raise FuseOSError(errno.ENOENT)

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

    def _get_hex(self, repeat=2):
        digits = '0123456789abcdef'
        return list(map(''.join, product(digits, repeat=repeat)))

    def _get_commits_by_hash(self, path):
        """ Return directory entries for path elements under the
        /commits-by-hash entry. """

        elements = path.split("/", 6)[2:]
        # Remove trailing empty slash
        if len(elements) > 0 and elements[-1] == '':
            del elements[-1]

        if self.hash_trees:
            if len(elements) <= 2:
                return self._hex
            elif len(elements) == 3:
                return self._git.all_commits(''.join(elements))
            else:
                return self._get_commits_from_path_list(elements[3:])

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
            if path.count("/") == self.git_start:
                return ""
            else:
                return path.split("/", self.git_start + 1)[-1]
        elif path.startswith("/branches/") and self.no_ref_symlinks:
            ref_limit = self._get_branch_ref_limit(path, self._branch_refs)
            if self._is_ref_prefix(path, self._branch_refs) or path.count("/") <= ref_limit:
                return ""
            else:
                return path.split("/", ref_limit + 1)[-1]
        elif path.startswith("/tags/") and self.no_ref_symlinks:
            if path.count("/") == 2:
                return ""
            else:
                return path.split("/", 3)[-1]
        else:
            raise FuseOSError(errno.ENOENT)

    def _is_metadata_symlink(self, path):
        elements = path.split("/")
        if (path.startswith("/commits-by-date/") and
                elements[-2] in self._commit_metadata_folders() and
                elements[-1] in self._git.all_commits()):
            # XXX Must also check number of slashes
            return True
        elif (path.startswith("/commits-by-hash/") and
                elements[-2] in self._commit_metadata_folders() and
                elements[-1] in self._git.all_commits()):
            return True
        elif ((path.startswith("/branches/") or path.startswith("/tags")) and
                self.no_ref_symlinks and
                self._is_ref(path) and
                elements[-2] in self._commit_metadata_folders() and
                elements[-1] in self._git.all_commits()):
            return True
        return False

    def _is_symlink(self, path):
        if self._is_metadata_symlink(path):
            return True
        elements = path.split("/")[1:]
        if ((path.startswith("/commits-by-date/") and len(elements) >= 6) or
                (path.startswith("/commits-by-hash/") and len(elements) >= self.git_start + 1)):
            return self._git.is_symlink(self._commit_from_path(path),
                        self._git_path(path))
        elif (path.startswith("/branches") and
                self._is_ref(path, self._branch_refs) and
                not self.no_ref_symlinks):
            return True
        elif (path.startswith("/tags") and
                self._is_ref(path, self._tag_refs) and
                not self.no_ref_symlinks):
            return True
        return False

    def _hash_updir(self, c):
        if not self.hash_trees:
            return ""
        return os.path.join(c[:2], c[2:4], c[4:6])

    def _format_to_link(self, commit):
        """ Return the specified commit as a symbolic link to
        commits-by-hash"""
        return os.path.join(self.mount, "commits-by-hash", self._hash_updir(commit), commit) + "/"

    def _commit_hex_path(self, commit):
        if not self.hash_trees:
            return ""

        return os.path.join(commit[:2], commit[2:4], commit[4:6])

    def _target_from_symlink(self, path):
        elements = path.split("/")
        if self._is_metadata_symlink(path):
            return os.path.join(self.mount, "commits-by-hash", self._commit_hex_path(elements[-1]), elements[-1] + "/")
        elif path.startswith("/commits-by-date") and len(elements) >= 6:
            return os.path.join(self.mount, "/".join(elements[1:6]),
                self._git.file_contents(self._commit_from_path(path), self._git_path(path)))
        elif path.startswith("/commits-by-hash") and len(elements) >= self.git_start + 1:
            return os.path.join(self.mount, "/".join(elements[1:self.git_start+1]),
                self._git.file_contents(self._commit_from_path(path), self._git_path(path)))
        elif path.startswith("/branches/"):
            commit = self._commit_from_ref(path[10:])
            if commit not in self._git.all_commits():
                return ""
            return self._format_to_link(commit)
        elif path.startswith("/tags/"):
            commit = self._commit_from_ref(path[6:])
            if commit not in self._git.all_commits():
                return ""
            return self._format_to_link(commit)
        else:
            raise FuseOSError(errno.ENOENT)

    def _commit_from_path(self, path):
        if path.startswith("/commits-by-date/"):
            if path.count("/") < 5:
                return ""
            else:
                return path.split("/", 6)[5]
        elif path.startswith('/commits-by-hash/'):
            if path.count("/") < self.git_start:
                return ""
            else:
                return path.split("/", self.git_start + 1)[self.git_start]
        elif path.startswith("/branches/") and self.no_ref_symlinks:
            if self._is_ref_prefix(path, self._branch_refs):
                return ""
            else:
                ref_limit = self._get_branch_ref_limit(path, self._branch_refs)
                return self._commit_from_ref("/".join(path.split("/")[2:ref_limit+1]))
        elif path.startswith("/tags/") and self.no_ref_symlinks:
            if self._is_ref_prefix(path, self._tag_refs):
                return ""
            else:
                # /tags/tag1/
                ref_limit = self._get_tag_ref_limit(path, self._tag_refs)
                return self._commit_from_ref("/".join(path.split("/")[1:ref_limit+1]))
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
            if self.hash_trees:
                self._verify_hash_path(elements[1:4])

            if len(elements) < self.git_start:
                return True
            elif len(elements) == self.git_start:
                return elements[self.git_start-1] in self._git.all_commits(''.join(elements[1:self.git_start-1]))
            elif elements[self.git_start] in self._commit_metadata_folders():
                if len(elements) == self.git_start + 2:
                    return False
                return True
            else:
                return self._git.is_dir(elements[self.git_start-1], "/".join(elements[self.git_start:]))
        elif elements in [['branches'], ['tags']]:
            return True
        elif elements[0] == 'branches' and len(elements) > 1:
            if self._is_ref_prefix(path, self._branch_refs):
                return True

            if self.no_ref_symlinks:
                prefix = "/".join(self._path_to_refs(path, self._branch_refs))
                if elements[1] == "heads" or elements[1] == "remotes":
                    ref_limit = self._get_branch_ref_limit(path, self._branch_refs)
                else:
                    return False

                if len(elements) < ref_limit:
                    return self._is_ref(path, self._branch_refs)
                elif len(elements) > ref_limit and elements[ref_limit] in self._commit_metadata_folders():
                    if len(elements[ref_limit:]) >= 2:
                        return False
                    return True
                elif self._is_ref(path):
                    return self._git.is_dir(self._commit_from_ref("/".join(elements[1:ref_limit])),
                            "/".join(elements[ref_limit:]))
                else:
                    return False
            return False
        elif elements[0] == 'tags':
            if self._is_ref_prefix(path, self._tag_refs):
                return True
            if self.no_ref_symlinks:
                prefix = "/".join(self._path_to_refs(path, self._branch_refs))
                ref_limit = self._get_tag_ref_limit(path, self._tag_refs)
                # /tags/tagName
                if len(elements) < ref_limit:
                    return self._is_ref(path, self._branch_refs)
                elif len(elements) > ref_limit and elements[ref_limit] in self._commit_metadata_folders():
                    if len(elements[ref_limit:]) >= 2:
                        return False
                    return True
                elif self._is_ref(path):
                    return self._git.is_dir(self._commit_from_ref("/".join(elements[0:ref_limit])),
                            "/".join(elements[ref_limit:]))
                else:
                    return False
            else:
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

    def get_commit_time(self, path):
        try:
            commit = self._commit_from_path(path)
            if not commit:
                return -1
            return self._git.get_commit_time(commit)
        except FuseOSError: # commit doesn't exist on path
            return -1

    def getattr(self, path, fh=None):
        uid, gid, pid = fuse_get_context()
        st = dict(st_uid=uid, st_gid=gid)
        if self._is_dir(path):
            st['st_mode'] = (S_IFDIR | self.mnt_mode)
            st['st_nlink'] = 2
        elif self._is_symlink(path):
            st['st_mode'] = (S_IFLNK | self.mnt_mode)
            st['st_nlink'] = 1
            st['st_size'] = len(self._target_from_symlink(path))
        else:
            st['st_mode'] = (S_IFREG | self.mnt_mode)
            st['st_size'] = self._get_file_size(path)

        t = time()
        st['st_atime'] = st['st_ctime'] = st['st_mtime'] = t

        commit_time = self.get_commit_time(path)
        if commit_time != -1:
            st['st_ctime'] = st['st_mtime'] = commit_time

        return st

    def readdir(self, path, fh):
        dirents = ['.', '..']
        if path == "/":
            dirents.extend(self._get_root())
        elif path.startswith("/commits-by-date"):
            dirents.extend(self._get_commits_by_date(path))
        elif path.startswith("/commits-by-hash"):
            dirents.extend(list(self._get_commits_by_hash(path)))
        elif path.startswith('/branches'):
            dirents.extend(self._get_branches(path))
        elif path.startswith('/tags'):
            dirents.extend(self._get_tags(path))
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


class RepoFSError(Exception):
    pass

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

    foreground = True
    if sys.argv[0].endswith("repofs"):
        foreground = False

    sys.stderr.write("Examining repository.  Please wait..\n")
    start = datetime.datetime.now()
    repo = RepoFS(os.path.abspath(args.repo), os.path.abspath(args.mount), args.hash_trees, args.no_ref_symlinks, args.nocache)
    end = datetime.datetime.now()
    sys.stderr.write("Ready! Repository mounted in %s\n" % (end - start))
    sys.stderr.write("Repository %s is now visible at %s\n" % (args.repo,
                                                               args.mount))
    FUSE(repo, args.mount, nothreads=True, foreground=foreground)

if __name__ == '__main__':
    main()
