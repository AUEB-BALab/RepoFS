![Build status](https://api.travis-ci.org/AUEB-BALab/RepoFS.png?branch=master)

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

Debian Based Distribution (\>= 9.3)
--------------------------------
1. `apt-get install python-pygit2 python-fuse`
2. `python setup.py install`

Older Debian Distributions (\< 9.3)
---------------------------------
1. `apt-get install python-fuse`
2. Build libgit2 from [source](https://github.com/libgit2/libgit2#quick-start)
3. `python setup.py install`

Regarding issues arrising from the installation of `pygit2`,
follow the instructions on [this page](www.pygit2.org/install.html).

Usage
=====

`repofs <git_repo> <mount_dir>`
