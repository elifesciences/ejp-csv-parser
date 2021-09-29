# ejp-csv-parser

EJP CSV parser for building article objects.

This library reads CSV files containing article manuscript data, creates objects defined in the `elifearticle` library, and sets object properties from the CSV data values.

Currently it reads CSV files for data including: title, abstract, DOI, editor, authors, group authors, license, received date, subjects, keywords, research organisms, datasets, funding, and ethics.

The `settings.py` module defines file names, column names, angle bracket escape sequence, folder names, and similar settings which can be adjusted slightly if required.

The `parse.py` module is a good starting place to invoke the library, if given an article ID value, it can read the CSV files for data, create objects and set their properties for that particular article.

The `csv_data.py` module contains the logic for reading the CSV files, linking rows from multiple files by their index columns, escaping and converting some character encoding, and accounting for comma characters that are not intende to delimit data fields.

The objects instantiated by this library are used to generate a JATS XML file for a Publish on Accept (PoA) research article.

## Requirements and install

a) Install from `pypi` package index

```
pip install ejpcsvparser
```

b) Install locally

Clone the git repo

`git clone https://github.com/elifesciences/ejp-csv-parser.git`

Create a python virtual environment and activate it

```
python3 -m venv venv
source venv/bin/activate
```

Install it locally

```
pip install -r requirements.txt
python setup.py install
```

In order to run the transform function as written, it will require `strip-coverletter` to be installed and ready to run locally, which will also require `Docker` to be installed and running.

## Example usage

This library is meant to be integrated into another operational system, where the CSV files are downloaded from an S3 bucket and then processed. The test scenarios may provide more details about how it could be invoked, and the following example is a simple way to see how it works using interactive Python and using files from the `"tests/test_data/"` folder as the CSV input:

```python
>>> from ejpcsvparser import parse
>>> article, error_count, error_messages = parse.build_article(21598)
>>> print(article.doi)
10.7554/eLife.21598
>>> print(article.title)
Cryo-EM structures of the autoinhibited <italic>E. coli</italic> ATP synthase in three rotational states
```

## Run code tests

Use `pytest` for testing, install it if missing:

```
pip install pytest
```

Run tests

```
pytest
```

Run tests with coverage

```
coverage run -m pytest
```

then report on code coverage

```
converage report -m
```

## License

Licensed under [MIT](https://opensource.org/licenses/mit-license.php).
