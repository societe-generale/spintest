"""Setup for `spintest` package."""

from setuptools import setup, find_packages


def parse_requirements(requirements_file):
    with open(requirements_file) as rf:
        requirements = rf.read()
    return requirements


setup(
    name="spintest",
    version="0.1.1",
    license='BSD-3-Clause',
    author="Matthieu Gouel",
    author_email="matthieu.gouel@gmail.com",
    url="https://github.com/societe-generale/spintest",
    description="Functional scenario interpreter",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: BSD License",
    ],
    include_package_data=True,
    packages=find_packages(),
    install_requires=parse_requirements('requirements.txt'),
)
