from setuptools import setup
import ejpcsvparser

with open("README.md") as fp:
    README = fp.read()

setup(
    name="ejpcsvparser",
    version=ejpcsvparser.__version__,
    description="EJP CSV parser for building article objects.",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=["ejpcsvparser"],
    license="MIT",
    install_requires=["elifearticle", "GitPython", "configparser"],
    url="https://github.com/elifesciences/ejp-csv-parser",
    maintainer="eLife Sciences Publications Ltd.",
    maintainer_email="tech-team@elifesciences.org",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
    ],
)
