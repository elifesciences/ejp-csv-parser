import logging
import csv
from collections import defaultdict, OrderedDict
import ejpcsvparser.utils as utils
import ejpcsvparser.settings as settings

# todo!! clean up these values and the settings
CSV_PATH = settings.CSV_PATH
ROWS_WITH_COLNAMES = settings.ROWS_WITH_COLNAMES
DATA_START_ROW = settings.DATA_START_ROW
CSV_FILES = settings.CSV_FILES
COLUMN_HEADINGS = settings.CSV_COLUMN_HEADINGS
OVERFLOW_CSV_FILES = settings.OVERFLOW_CSV_FILES

logger = logging.getLogger('csv_data')
hdlr = logging.FileHandler('csv_data.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)


def memoize(f):
    "Memoization decorator for functions taking one or more arguments."
    class Memodict(dict):
        "Memoization dict"
        def __init__(self, f):
            dict.__init__(self)
            self.f = f
        def __call__(self, *args):
            return self[args]
        def __missing__(self, key):
            ret = self[key] = self.f(*key)
            return ret
    return Memodict(f)


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
    logger.info("in get_csv_col_names")
    logger.info(table_type)
    sheet = get_csv_sheet(table_type)
    logger.info(sheet)
    logger.info(str(ROWS_WITH_COLNAMES))
    for index, row in enumerate(sheet):
        logger.info("in enumerate")
        logger.info(str(index) + " " + str(row))
        logger.debug(str(index) + " " + str(ROWS_WITH_COLNAMES))
        if int(index) == int(ROWS_WITH_COLNAMES):
            return row

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
    cell_value = row[position]
    return cell_value


@memoize
def get_csv_sheet(table_type):
    logger.info("in get_csv_sheet")
    path = get_csv_path(table_type)
    logger.info(str(path))
    with open(path) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        sheet = []
        for row in csvreader:
            sheet.append(row)
    # For overflow file types, parse again with no quotechar
    if table_type in OVERFLOW_CSV_FILES:
        csvfile = open(path)
        csvreader = csv.reader(csvfile, delimiter=',', quotechar=None)
        if table_type == "ethics":
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

    logger.info("in index_table_on_article_id")

    # get the data and the row of colnames
    data_rows = get_csv_data_rows(table_type)
    col_names = get_csv_col_names(table_type)

    # logger.info("data_rows: " + str(data_rows))
    logger.info("col_names: " + str(col_names))

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
    logger.info("in get_article_attributes")
    logger.info("article_id: " + str(article_id) + " attribute_type: " +
                attribute_type + " attribute_label:" +  attribute_label)
    attributes = []
    logger.info("about to generate attribute index")
    attribute_index = index_table_on_article_id(attribute_type)
    logger.info("generated attribute index")
    # logger.info(str(attribute_index))
    logger.info("about to get col_names for colname " + str(attribute_type))
    col_names = get_csv_col_names(attribute_type)
    attribute_rows = attribute_index[str(article_id)]
    for attribute_row in attribute_rows:
        attributes.append(get_cell_value(attribute_label, col_names, attribute_row))
    return attributes


# subjects table

def get_subjects(article_id):
    attribute = get_article_attributes(article_id, "subjects",
                                       COLUMN_HEADINGS["subject_areas"])
    return attribute

# organisms table

def get_organisms(article_id):
    attribute = get_article_attributes(article_id, "organisms",
                                       COLUMN_HEADINGS["organisms"])
    return attribute

# license table

def get_license(article_id):
    attribute = get_article_attributes(article_id, "license",
                                       COLUMN_HEADINGS["license_id"])[0]
    return attribute

# keywords table

def get_keywords(article_id):
    attribute = get_article_attributes(article_id, "keywords",
                                       COLUMN_HEADINGS["keywords"])
    return attribute

# manuscript table

@utils.entities
def get_title(article_id):
    attributes = get_article_attributes(article_id, "title",
                                        COLUMN_HEADINGS["title"])
    attribute = attributes[0]
    return attribute

@utils.entities
def get_abstract(article_id):
    attributes = get_article_attributes(article_id, "abstract",
                                        COLUMN_HEADINGS["abstract"])
    attribute = attributes[0]
    return attribute

def get_doi(article_id):
    attribute = get_article_attributes(article_id, "manuscript",
                                       COLUMN_HEADINGS["doi"])[0]
    return attribute

def get_article_type(article_id):
    attribute = get_article_attributes(article_id, "manuscript",
                                       COLUMN_HEADINGS["article_type"])[0]
    return attribute

def get_accepted_date(article_id):
    attribute = get_article_attributes(article_id, "manuscript",
                                       COLUMN_HEADINGS["accepted_date"])[0]
    return attribute

def get_received_date(article_id):
    attribute = get_article_attributes(article_id, "received",
                                       COLUMN_HEADINGS["received_date"])[0]
    return attribute

def get_receipt_date(article_id):
    attribute = get_article_attributes(article_id, "received",
                                       COLUMN_HEADINGS["receipt_date"])[0]
    return attribute

def get_me_id(article_id):
    attribute = get_article_attributes(article_id, "manuscript",
                                       COLUMN_HEADINGS["editor_id"])[0]
    return attribute

@utils.entities
def get_me_last_nm(article_id):
    attribute = get_article_attributes(article_id, "manuscript",
                                       COLUMN_HEADINGS["editor_last_name"])[0]
    return attribute

@utils.entities
def get_me_first_nm(article_id):
    attribute = get_article_attributes(article_id, "manuscript",
                                       COLUMN_HEADINGS["editor_first_name"])[0]
    return attribute

@utils.entities
def get_me_middle_nm(article_id):
    attribute = get_article_attributes(article_id, "manuscript",
                                       COLUMN_HEADINGS["editor_middle_name"])[0]
    return attribute

@utils.entities
def get_me_institution(article_id):
    attribute = get_article_attributes(article_id, "manuscript",
                                       COLUMN_HEADINGS["editor_institution"])[0]
    return attribute

@utils.entities
def get_me_department(article_id):
    attribute = get_article_attributes(article_id, "manuscript",
                                       COLUMN_HEADINGS["editor_department"])[0]
    return attribute

@utils.entities
def get_me_country(article_id):
    attribute = get_article_attributes(article_id, "manuscript",
                                       COLUMN_HEADINGS["editor_country"])[0]
    return attribute

def get_ethics(article_id):
    """
    needs a bit of refinement owing to serilaising of data by EJP
    """
    try:
        attribute = get_article_attributes(article_id, "ethics",
                                           COLUMN_HEADINGS["ethics"])[0]
    except IndexError:
        attribute = None
    return attribute

# authors table
def get_author_ids(article_id):
    author_ids = get_article_attributes(article_id, "authors",
                                        COLUMN_HEADINGS["author_id"])
    return author_ids

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
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_position"])
    return attribute

def get_author_email(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["email"])
    return attribute

def get_author_contrib_type(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_type"])
    return attribute

def get_author_dual_corresponding(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["dual_corresponding"])
    return attribute

@utils.entities
def get_author_last_name(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_last_name"])
    return attribute

@utils.entities
def get_author_first_name(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_first_name"])
    return attribute

@utils.entities
def get_author_middle_name(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_middle_name"])
    return attribute

@utils.entities
def get_author_institution(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_institution"])
    return attribute

@utils.entities
def get_author_department(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_department"])
    return attribute

@utils.entities
def get_author_city(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_city"])
    return attribute

@utils.entities
def get_author_country(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_country"])
    return attribute

def get_author_state(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_state"])
    return attribute

def get_author_conflict(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["author_conflict"])
    return attribute

def get_author_orcid(article_id, author_id):
    attribute = get_author_attribute(article_id, author_id,
                                     COLUMN_HEADINGS["orcid"])
    return attribute

def get_group_authors(article_id):
    # Wrap in an exception because some empty rows throws IndexError
    try:
        attribute = get_article_attributes(article_id, "group_authors",
                                           COLUMN_HEADINGS["group_author"])[0]
    except IndexError:
        attribute = None
    return attribute

def get_datasets(article_id):
    try:
        attribute = get_article_attributes(article_id, "datasets",
                                           COLUMN_HEADINGS["datasets"])[0]
    except IndexError:
        attribute = None
    return attribute

# funding
@memoize
def index_funding_table():
    """
    Rows in the funding CSV are to be uniquely identified by three column values
    article_id + author_id + funder_position
    This will return a three dimensional dict with those hierarchies
    """
    table_type = "funding"

    logger.info("in index_funding_table")

    # get the data and the row of colnames
    data_rows = get_csv_data_rows(table_type)
    col_names = get_csv_col_names(table_type)

    # logger.info("data_rows: " + str(data_rows))
    logger.info("col_names: " + str(col_names))

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

    #print article_index
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
    attribute = get_funding_attribute(
        article_id, author_id, funder_position, COLUMN_HEADINGS["funder"])
    return attribute

def get_award_id(article_id, author_id, funder_position):
    attribute = get_funding_attribute(
        article_id, author_id, funder_position, COLUMN_HEADINGS["award_id"])
    return attribute

def get_funder_identifier(article_id, author_id, funder_position):
    attribute = get_funding_attribute(
        article_id, author_id, funder_position, COLUMN_HEADINGS["funder_identifier"])
    return attribute

def get_funding_note(article_id):
    attribute = get_article_attributes(
        article_id, "manuscript", COLUMN_HEADINGS["funding_note"])[0]
    return attribute
