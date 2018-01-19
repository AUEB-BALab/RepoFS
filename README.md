RepoFS
======
Filesystem view of version control repositories

Installation
=======================

1. `apt-get install git python-dev python libfuse-dev python-pip libgit2-dev`
2. Install [libfuse](https://github.com/libfuse/libfuse) following
the instructions on its GitHub page. See [libfuse-notes](#libfuse-notes)
for installation issues.
3. Run `python setup.py install`

libfuse Notes
==================

1. Install `meson` with `pip3 install meson` in order to get the
newest version. (pip3 has the >=0.38 version that libfuse requires)
2. Install the `ninja` and the `ninja-build` package using
`apt-get install ninja ninja-build` instead of just the `ninja` package.

libgit2 Notes
=============

If you encounter problems installing `pygit2` follow the instructions
on this [page](https://gist.github.com/bendavis78/3157948).

Usage
=====

`repofs <git_repo> <mount_dir>`
