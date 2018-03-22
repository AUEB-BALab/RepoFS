RepoFS
======
Filesystem view of version control repositories

Installation
=======================

OSX
---
1. Install the [latest release of
   OSXFUSE](https://github.com/osxfuse/osxfuse/releases)
2. `brew install libgit2`
3. `python setup.py install`

Debian Based Distribution >= 9.3
--------------------------------
1. `apt-get install python-pygit2 python-fuse`
2. `python setup.py install`

Usage
=====

`repofs <git_repo> <mount_dir>`
