RepoFS
======
Filesystem view of version control repositories

Installing Dependencies
=======================

1. Install [libfuse](https://github.com/libfuse/libfuse) following
the instructions on its GitHub page. See [libfuse-notes](#libfuse-notes)
for installation issues.
2. Install [fusepy](https://github.com/terencehonles/fusepy) using
`pip install fusepy`

libfuse Notes
==================

1. Install `meson` with `pip3 install meson` in order to get the
newest version. (pip3 has the >=0.38 version that libfuse requires)
2. Install the `ninja` and the `ninja-build` package using
`apt-get install ninja ninja-build` instead of just the `ninja` package.
