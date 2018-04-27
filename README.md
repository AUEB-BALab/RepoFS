![Build status](https://api.travis-ci.org/AUEB-BALab/RepoFS.png?branch=master)

RepoFS
======
Filesystem view of version control repositories

Installation
=======================

We currently support only Debian based distributions.

Debian Based Distribution (\>= 9.3)
--------------------------------
1. `apt-get install libffi-dev libgit2-dev fuse`
2. `pip install repofs`

Older Debian Distributions (\< 9.3)
---------------------------------
1. `apt-get install python-fuse`
2. Build libgit2 from [source](https://github.com/libgit2/libgit2#quick-start)
3. `pip install repofs`

Regarding issues arrising from the installation of `pygit2`,
follow the instructions on [this page](http://www.pygit2.org/install.html).

Usage
=====

`repofs <git_repo> <mount_dir>`
