from setuptools import setup

with open("README.md", "r") as readme:
    long_description = readme.read()


setup(
    name='repofs',
    version='0.2.6',
    description='File system view of git repositories',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/AUEB-BALab/RepoFS',
    license='Apache Software License',
    packages=[
        'repofs',
        'repofs.handlers'
    ],
    install_requires=['fusepy', 'pygit2'],
    scripts=[
        'bin/repofs'
    ],
    author='Vitalis Salis',
    author_email='vitsalis@gmail.com'
)
