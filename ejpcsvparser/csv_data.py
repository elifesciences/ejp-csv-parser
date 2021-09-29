import logging
import csv
import sys
import io
import os
from collections import defaultdict, OrderedDict
import ejpcsvparser.utils as utils
import ejpcsvparser.settings as settings

# todo!! clean up these values and the settings
CSV_PATH = settings.CSV_PATH
TMP_DIR = settings.TMP_DIR
ROWS_WITH_COLNAMES = settings.ROWS_WITH_COLNAMES
DATA_START_ROW = settings.DATA_START_ROW
CSV_FILES = settings.CSV_FILES
COLUMN_HEADINGS = settings.CSV_COLUMN_HEADINGS
OVERFLOW_CSV_FILES = settings.OVERFLOW_CSV_FILES

LOGGER = logging.getLogger('csv_data')
HDLR = logging.FileHandler('csv_data.log')
FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
HDLR.setFormatter(FORMATTER)
LOGGER.addHandler(HDLR)
LOGGER.setLevel(logging.INFO)


def memoize(value):
    "Memoization decorator for functions taking one or more arguments."
    class Memodict(dict):
        "Memoization dict"
        def __init__(self, value):
            dict.__init__(self)
            self.value = value

        def __call__(self, *args):
            return self[args]

        def __missing__(self, key):
            ret = self[key] = self.value(*key)
            return ret
    return Memodict(value)


def get_csv_path(path_type):
    """
    sets the location of the path to the author csv file
    returns the path

    This is the only function where the path the our actual data files
    are set.
    """
    path = CSV_PATH + CSV_FILES[path_type]
    return path


@memoize
def get_csv_col_names(table_type):
    LOGGER.info("in get_csv_col_names")
    LOGGER.info(table_type)
    sheet = get_csv_sheet(table_type)
    LOGGER.info(sheet)
    LOGGER.info(str(ROWS_WITH_COLNAMES))
    columns_row = []
    for index, row in enumerate(sheet):
        LOGGER.info("in enumerate")
        LOGGER.info(str(index) + " " + str(row))
        LOGGER.debug(str(index) + " " + str(ROWS_WITH_COLNAMES))
        if int(index) == int(ROWS_WITH_COLNAMES):
            columns_row = row
    return columns_row


@memoize
def get_csv_data_rows(table_type):
    sheet = get_csv_sheet(table_type)
    rows = []
    for row in sheet:
        rows.append(row)
    data_rows = rows[DATA_START_ROW:]
    return data_rows


def get_cell_value(col_name, col_names, row):
    """
    we pass the name of the col and a copy of the col names row in to
    this fucntion so that we don't have to worry about knowing what the
    index of a specific col name is.
    """
    position = col_names.index(col_name)
    if row and position and len(row) > position:
        return row[position]
    return None


def join_lines(line_one, line_two, line_number, data_start_row=DATA_START_ROW):
    "join multiple lines together taking into account the header rows"
    if line_number <= data_start_row:
        # keep blank lines found in the headers
        content = line_two
    else:
        if line_two.lstrip() == '':
            # blank line outside of the header convert to a space
            content = line_one.rstrip("\r\n") + u' '
        else:
            content = line_one.rstrip("\r\n") + line_two.lstrip()
    return content


def do_add_line(content, line_number, data_start_row=DATA_START_ROW):
    "decide if the line should be added to the output"
    add_line = False
    if line_number <= data_start_row or content.rstrip().endswith('"'):
        add_line = True
    return add_line


def flatten_lines(iterable, data_start_row=DATA_START_ROW):
    "iterate through an open file and join lines"
    clean_csv_data = u''
    line_number = 1
    prev_line = u''
    add_line = False
    for content in iterable:
        content = utils.decode_cp1252(content)
        # add the line based on the previous iteration value
        if add_line:
            clean_csv_data += prev_line
            prev_line = u''
        prev_line = join_lines(prev_line, content, line_number, data_start_row)
        add_line = do_add_line(content, line_number, data_start_row)
        line_number += 1
    # Add the final line
    clean_csv_data += prev_line
    return clean_csv_data


@memoize
def clean_csv(path):
    "fix CSV file oddities making it difficult to parse"
    clean_csv_data = u''
    new_path = os.path.join(TMP_DIR, os.path.split(path)[-1])
    with open(path, 'r') as open_read_file:
        clean_csv_data = flatten_lines(open_read_file)
    with open(new_path, 'w') as open_write_file:
        open_write_file.write(clean_csv_data)
    return new_path


@memoize
def get_csv_sheet(table_type):
    LOGGER.info("in get_csv_sheet")
    path = get_csv_path(table_type)
    LOGGER.info(str(path))

    path = clean_csv(path)

    # https://docs.python.org/3/library/functions.html#open
    handle = io.open(path, 'r', newline='', encoding='utf-8', errors='surrogateescape')

    with handle as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        sheet = []
        for row in csvreader:
            sheet.append(row)
    # For overflow file types, parse again with no quotechar
    if table_type in OVERFLOW_CSV_FILES:
        csvfile = open(path)
        csvreader = csv.reader(csvfile, delimiter=',', quotechar=None)
        if table_type in ["ethics", "datasets"]:
            join_cells_from = 3
        else:
            join_cells_from = 2
        for row in csvreader:
            if csvreader.line_num <= DATA_START_ROW:
                continue
            # Merge cells 3 to the end because any commas will cause extra columns
            row[join_cells_from] = ','.join(row[join_cells_from:])
            for index, cell in enumerate(row):
                # Strip leading quotation marks
                row[index] = cell.lstrip('"').rstrip('"')
            sheet[csvreader.line_num-1] = row
        csvfile.close()
    return sheet


@memoize
def index_table_on_article_id(table_type):
    """
    return a dict of the CSV file keyed on article_id

    the name of the manuscript number column is hard wired in this function.
    """

    LOGGER.info("in index_table_on_article_id")

    # get the data and the row of colnames
    data_rows = get_csv_data_rows(table_type)
    col_names = get_csv_col_names(table_type)

    # LOGGER.info("data_rows: " + str(data_rows))
    LOGGER.info("col_names: %s", col_names)

    article_index = defaultdict(list)
    for data_row in data_rows:
        article_id = get_cell_value('poa_m_ms_no', col_names, data_row)
        # author_id = get_cell_value("poa_a_id", col_names, data_row)
        article_index[article_id].append(data_row)
        # print article_id, author_id
    return article_index


@memoize
def index_authors_on_article_id():
    article_index = index_table_on_article_id("authors")
    return article_index


@memoize
def index_authors_on_author_id():
    # """
    # as we are going to be doing a lot of looking up authors by
    # author_id and manuscript_id,
    # so we are going to make a dict of dicts indexed on manuscript id and then author id
    # """
    table_type = "authors"
    col_names = get_csv_col_names(table_type)
    author_table = index_authors_on_article_id()

    article_ids = author_table.keys()
    article_author_index = OrderedDict()  # this is the key item we will return our of this function
    for article_id in article_ids:
        rows = author_table[article_id]
        author_index = defaultdict()
        for row in rows:
            author_id = get_cell_value("poa_a_id", col_names, row)
            author_index[author_id] = row
        article_author_index[article_id] = author_index
    return article_author_index


@memoize
def get_article_attributes(article_id, attribute_type, attribute_label):
    LOGGER.info("in get_article_attributes")
    LOGGER.info("article_id: %s attribute_type: %s attribute_label: %s",
                article_id, attribute_type, attribute_label)
    attributes = []
    LOGGER.info("about to generate attribute index")
    attribute_index = index_table_on_article_id(attribute_type)
    LOGGER.info("generated attribute index")
    # LOGGER.info(str(attribute_index))
    LOGGER.info("about to get col_names for colname %s", attribute_type)
    col_names = get_csv_col_names(attribute_type)
    attribute_rows = attribute_index[str(article_id)]
    for attribute_row in attribute_rows:
        attributes.append(get_cell_value(attribute_label, col_names, attribute_row))
    return attributes


def article_all_values(article_id, file_name, column_name):
    "get the article attributes and return all of them"
    return get_article_attributes(article_id, file_name, column_name)


def article_first_value(article_id, file_name, column_name):
    "get the article attributes and return only the first value"
    attributes = article_all_values(article_id, file_name, column_name)
    if attributes:
        return attributes[0]
    return None


# subjects table
def get_subjects(article_id):
    return article_all_values(article_id, "subjects", COLUMN_HEADINGS["subject_areas"])


# organisms table
def get_organisms(article_id):
    return article_all_values(article_id, "organisms", COLUMN_HEADINGS["organisms"])


# license table
def get_license(article_id):
    return article_first_value(article_id, "license", COLUMN_HEADINGS["license_id"])


# keywords table
def get_keywords(article_id):
    return article_all_values(article_id, "keywords", COLUMN_HEADINGS["keywords"])


# manuscript table
@utils.entities
def get_title(article_id):
    return article_first_value(article_id, "title", COLUMN_HEADINGS["title"])


@utils.entities
def get_abstract(article_id):
    return article_first_value(article_id, "abstract", COLUMN_HEADINGS["abstract"])


def get_doi(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["doi"])


def get_article_type(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["article_type"])


def get_accepted_date(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["accepted_date"])


def get_received_date(article_id):
    return article_first_value(article_id, "received", COLUMN_HEADINGS["received_date"])


def get_receipt_date(article_id):
    return article_first_value(article_id, "received", COLUMN_HEADINGS["receipt_date"])


def get_me_id(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["editor_id"])


@utils.entities
def get_me_last_nm(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["editor_last_name"])


@utils.entities
def get_me_first_nm(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["editor_first_name"])


@utils.entities
def get_me_middle_nm(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["editor_middle_name"])


@utils.entities
def get_me_suffix(article_id):
    try:
        return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["editor_suffix"])
    except ValueError:
        return None


@utils.entities
def get_me_institution(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["editor_institution"])


@utils.entities
def get_me_department(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["editor_department"])


@utils.entities
def get_me_country(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["editor_country"])


def get_ethics(article_id):
    """
    needs a bit of refinement owing to serilaising of data by EJP
    """
    return article_first_value(article_id, "ethics", COLUMN_HEADINGS["ethics"])


# authors table
def get_author_ids(article_id):
    return article_all_values(article_id, "authors", COLUMN_HEADINGS["author_id"])


def get_author_attribute(article_id, author_id, attribute_name):
    article_author_index = index_authors_on_author_id()
    # check for if the data row exists first
    if article_id not in article_author_index:
        return None
    if author_id not in article_author_index[article_id]:
        return None
    # continue
    data_row = article_author_index[article_id][author_id]
    col_names = get_csv_col_names("authors")
    attribute = get_cell_value(attribute_name, col_names, data_row)
    return attribute


def get_author_position(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_position"])


def get_author_email(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["email"])


def get_author_contrib_type(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_type"])


def get_author_dual_corresponding(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["dual_corresponding"])


@utils.entities
def get_author_last_name(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_last_name"])


@utils.entities
def get_author_first_name(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_first_name"])


@utils.entities
def get_author_middle_name(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_middle_name"])


@utils.entities
def get_author_suffix(article_id, author_id):
    try:
        return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_suffix"])
    except ValueError:
        return None


@utils.entities
def get_author_institution(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_institution"])


@utils.entities
def get_author_department(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_department"])


@utils.entities
def get_author_city(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_city"])


@utils.entities
def get_author_country(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_country"])


def get_author_state(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_state"])


def get_author_conflict(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["author_conflict"])


def get_author_orcid(article_id, author_id):
    return get_author_attribute(article_id, author_id, COLUMN_HEADINGS["orcid"])


def get_group_authors(article_id):
    return article_first_value(article_id, "group_authors", COLUMN_HEADINGS["group_author"])


def get_datasets(article_id):
    return article_first_value(article_id, "datasets", COLUMN_HEADINGS["datasets"])


# funding
@memoize
def index_funding_table():
    """
    Rows in the funding CSV are to be uniquely identified by three column values
    article_id + author_id + funder_position
    This will return a three dimensional dict with those hierarchies
    """
    table_type = "funding"

    LOGGER.info("in index_funding_table")

    # get the data and the row of colnames
    data_rows = get_csv_data_rows(table_type)
    col_names = get_csv_col_names(table_type)

    # LOGGER.info("data_rows: " + str(data_rows))
    LOGGER.info("col_names: %s", col_names)

    article_index = OrderedDict()
    for data_row in data_rows:
        article_id = get_cell_value('poa_m_ms_no', col_names, data_row)
        author_id = get_cell_value(COLUMN_HEADINGS["author_id"], col_names, data_row)
        funder_position = get_cell_value(COLUMN_HEADINGS["funder_position"], col_names, data_row)

        # Crude multidimentional dict builder
        if article_id not in article_index:
            article_index[article_id] = OrderedDict()
        if author_id not in article_index[article_id]:
            article_index[article_id][author_id] = OrderedDict()

        article_index[article_id][author_id][funder_position] = data_row

    return article_index


def get_funding_ids(article_id):
    """
    Return funding table keys as a list of tuples
    for a particular article_id
    """
    funding_ids = []

    for key, value in index_funding_table().items():
        if key == article_id:
            for key_2, value_2 in value.items():
                for key_3 in value_2.keys():
                    funding_ids.append((key, key_2, key_3))

    return funding_ids


def get_funding_attribute(article_id, author_id, funder_position, attribute_name):
    funding_article_index = index_funding_table()

    data_row = funding_article_index[str(article_id)][str(author_id)][str(funder_position)]

    col_names = get_csv_col_names("funding")
    attribute = get_cell_value(attribute_name, col_names, data_row)
    return attribute


def get_funder(article_id, author_id, funder_position):
    return get_funding_attribute(
        article_id, author_id, funder_position, COLUMN_HEADINGS["funder"])


def get_award_id(article_id, author_id, funder_position):
    return get_funding_attribute(
        article_id, author_id, funder_position, COLUMN_HEADINGS["award_id"])


def get_funder_identifier(article_id, author_id, funder_position):
    return get_funding_attribute(
        article_id, author_id, funder_position, COLUMN_HEADINGS["funder_identifier"])


def get_funding_note(article_id):
    return article_first_value(article_id, "manuscript", COLUMN_HEADINGS["funding_note"])
