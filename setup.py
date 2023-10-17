from setuptools import setup, find_packages

setup(
    name="badchess",
    version="0.1",
    description="A library for making bad chess moves",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pytest",
    ],
    tests_require=[
        "pytest",
    ],
)
