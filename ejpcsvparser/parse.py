from __future__ import print_function
import logging
import time
from collections import OrderedDict
from xml.dom import minidom
from xml.parsers.expat import ExpatError
from elifearticle import article as ea
from elifearticle import utils as eautils
from elifetools import utils as etoolsutils
import ejpcsvparser.utils as utils
import ejpcsvparser.csv_data as data

LOGGER = logging.getLogger('parse')
HDLR = logging.FileHandler('parse.log')
FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
HDLR.setFormatter(FORMATTER)
LOGGER.addHandler(HDLR)
LOGGER.setLevel(logging.INFO)


def instantiate_article(article_id):
    LOGGER.info("in instantiate_article for %s", article_id)
    doi = data.get_doi(article_id)
    if doi is not None:
        # Fallback if doi string is blank, default to eLife concatenated
        if doi.strip() == "":
            doi = utils.get_elife_doi(article_id)
        article = ea.Article(doi, title=None)
        return article
    return None


def set_title(article, article_id):
    LOGGER.info("in set_title")
    title = data.get_title(article_id)
    if title:
        article.title = utils.convert_to_xml_string(title)
        return True
    LOGGER.error("could not set title ")
    return False


def set_abstract(article, article_id):
    LOGGER.info("in set_abstract")
    raw_abstract = data.get_abstract(article_id)
    if raw_abstract:
        abstract = utils.decode_cp1252(raw_abstract)
        article.abstract = utils.convert_to_xml_string(abstract)
        article.manuscript = article_id
        return True
    LOGGER.error("could not set abstract ")
    return False


def set_article_type(article, article_id):
    LOGGER.info("in set_article_type")
    article_type_id = data.get_article_type(article_id)
    article_type_index = utils.article_type_indexes()
    if article_type_id in article_type_index:
        article_type = article_type_index[str(article_type_id)]
        article.article_type = article_type['article_type']
        article.display_channel = article_type['display_channel']
        return True
    return False


def set_license(article, article_id):
    LOGGER.info("in set_license")
    # if no article return False
    if not article:
        return False
    license_id = data.get_license(article_id)
    license_object = ea.License(license_id)
    data_values = utils.license_data(license_id)
    # if no data to populate the license return False
    if not data_values:
        return False
    # set the object attributes from the data if present
    for name in ['license_id', 'license_type', 'copyright', 'href',
                 'name', 'paragraph1', 'paragraph2']:
        eautils.set_attr_if_value(license_object, name, data_values.get(name))
    article.license = license_object
    return True


def add_date_to_article(article, date_type, date_string):
    "add a date to the article object"
    if not article:
        return False
    date_struct = None
    date_parts = []
    if date_string:
        date_parts = date_string.split()

    if date_parts:
        try:
            date_struct = time.strptime(date_parts[0], "%Y-%m-%d")
        except ValueError:
            LOGGER.info("unable to convert date %s given %s for article %s",
                        date_type, date_parts, article.doi)
    else:
        return False

    if date_string and date_struct:
        article_date = ea.ArticleDate(date_type, date_struct)
        article.add_date(article_date)
        LOGGER.info("set date_type %s from %s as %s",
                    date_type, date_string, article_date)
        return True
    return False


def set_dates(article, article_id):
    LOGGER.info("in set_dates")
    if not article:
        return False

    accepted_date = data.get_accepted_date(article_id)
    date_status = add_date_to_article(article, "accepted", accepted_date)
    if date_status is not True:
        return False

    received_date = data.get_received_date(article_id)
    if received_date.strip() == "":
        # Use the alternate date column receipt_date if received_date is blank
        received_date = data.get_receipt_date(article_id)
    date_status = add_date_to_article(article, "received", received_date)
    if date_status is not True:
        return False

    # set the license date to be the same as the accepted date
    if article.get_date('accepted'):
        date_license = ea.ArticleDate("license", article.get_date('accepted').date)
        article.add_date(date_license)
    return True


def set_ethics(article, article_id):
    LOGGER.info("in set_ethics")
    ethics = None
    parse_status = None
    ethic = data.get_ethics(article_id)
    LOGGER.info(ethic)
    if ethic:
        parse_status, ethics = parse_ethics(ethic)
    if ethic and parse_status is not True:
        LOGGER.error("could not set ethics due to parsing error")
        return False
    if ethics:
        for ethics_value in ethics:
            article.add_ethic(ethics_value)
    return True


def set_datasets(article, article_id):
    LOGGER.info("in set_datasets")
    datasets = data.get_datasets(article_id)
    dataset_objects = None
    data_availability = None
    parse_status = None
    LOGGER.info(datasets)
    if datasets:
        parse_status, dataset_objects, data_availability = parse_datasets(datasets)
    if datasets and parse_status is not True:
        LOGGER.error("could not set datasets due to parsing error")
        return False
    if dataset_objects:
        for dataset in dataset_objects:
            article.add_dataset(dataset)
    if data_availability:
        article.data_availability = utils.convert_to_xml_string(data_availability)
    return True


def set_categories(article, article_id):
    LOGGER.info("in set_categories")
    categories = data.get_subjects(article_id)
    if categories:
        for category in categories:
            article.add_article_category(category)
    return True


def set_organsims(article, article_id):
    LOGGER.info("in set_organsims")
    research_organisms = data.get_organisms(article_id)
    if research_organisms:
        for research_organism in research_organisms:
            if research_organism.strip() != "":
                article.add_research_organism(utils.convert_to_xml_string(research_organism))
    return True


def set_keywords(article, article_id):
    LOGGER.info("in set_keywords")
    keywords = data.get_keywords(article_id)
    if keywords:
        for keyword in keywords:
            article.add_author_keyword(keyword)
    return True


def build_author(article_id, author_id, author_type):
    "build an author object with the basic name data"
    first_name = utils.decode_cp1252(data.get_author_first_name(article_id, author_id))
    last_name = utils.decode_cp1252(data.get_author_last_name(article_id, author_id))
    middle_name = utils.decode_cp1252(data.get_author_middle_name(article_id, author_id))
    suffix = utils.decode_cp1252(data.get_author_suffix(article_id, author_id))
    # initials = middle_name_initials(middle_name)
    if middle_name.strip() != "":
        # Middle name add to the first name / given name
        first_name += " " + middle_name
    author = ea.Contributor(author_type, last_name, first_name)
    if suffix and suffix.strip() != "":
        author.suffix = suffix
    return author


def author_affiliation(article_id, author_id):
    "create and set author affiliation details"
    affiliation = ea.Affiliation()

    department = utils.decode_cp1252(data.get_author_department(article_id, author_id))
    if department.strip() != "":
        affiliation.department = department
    affiliation.institution = utils.decode_cp1252(
        data.get_author_institution(article_id, author_id))
    city = utils.decode_cp1252(data.get_author_city(article_id, author_id))
    if city.strip() != "":
        affiliation.city = city
    affiliation.country = data.get_author_country(article_id, author_id)

    contrib_type = data.get_author_contrib_type(article_id, author_id)
    dual_corresponding = data.get_author_dual_corresponding(article_id, author_id)
    if (contrib_type == "Corresponding Author" or
            (dual_corresponding.strip() != '' and int(dual_corresponding.strip()) == 1)):
        affiliation.email = data.get_author_email(article_id, author_id)
    return affiliation


def set_author_info(article, article_id):
    """
    author information
    Save the contributor and their position in the list in a dict,
    for both authors and group authors,
    Then add the contributors to the article object in order of their position
    """
    LOGGER.info("in set_author_info")
    authors_dict = {}

    # check there are any authors before continuing
    author_ids = data.get_author_ids(article_id)
    if not author_ids and not data.get_group_authors(article_id):
        LOGGER.error("could not find any author data")
        return False

    if author_ids:
        for author_id in author_ids:

            author_type = "author"
            author = build_author(article_id, author_id, author_type)

            affiliation = author_affiliation(article_id, author_id)
            # set corresponding if the affiliation has an email
            if affiliation.email:
                author.corresp = True

            conflict = data.get_author_conflict(article_id, author_id)
            if conflict.strip() != "":
                author.set_conflict(utils.convert_to_xml_string(conflict))

            orcid = data.get_author_orcid(article_id, author_id)
            if orcid.strip() != "":
                author.orcid = orcid

            author.auth_id = author_id
            author.set_affiliation(affiliation)

            author_position = data.get_author_position(article_id, author_id)
            # Add the author to the dictionary recording their position in the list
            authors_dict[int(author_position)] = author

    # Add group author collab contributors, if present
    group_authors = data.get_group_authors(article_id)
    if group_authors:
        # Parse the group authors string
        group_author_dict = parse_group_authors(group_authors)

        if group_author_dict:
            for author_position in sorted(group_author_dict.keys()):
                collab = group_author_dict.get(author_position)
                author = ea.Contributor("author", None, None, collab)

                # Add the author to the dictionary recording their position in the list
                authors_dict[int(author_position)] = author

    # Finally add authors to the article sorted by their position
    for author_position in sorted(authors_dict.keys()):
        # print article_id, author_position, author
        article.add_contributor(authors_dict.get(author_position))

    return True


def set_editor_info(article, article_id):
    LOGGER.info("in set_editor_info")

    author_type = "editor"

    first_name = utils.decode_cp1252(data.get_me_first_nm(article_id))
    last_name = utils.decode_cp1252(data.get_me_last_nm(article_id))
    middle_name = utils.decode_cp1252(data.get_me_middle_nm(article_id))
    suffix = utils.decode_cp1252(data.get_me_suffix(article_id))
    # no first and last name then return False
    if not(first_name and last_name):
        LOGGER.error("could not set editor")
        return False
    # initials = middle_name_initials(middle_name)
    if middle_name.strip() != "":
        # Middle name add to the first name / given name
        first_name += " " + middle_name
    # create an instance of the POSContributor class
    editor = ea.Contributor(author_type, last_name, first_name)
    if suffix and suffix.strip() != "":
        editor.suffix = suffix
    LOGGER.info("editor is: %s", str(editor))
    LOGGER.info("getting ed id for article %s", article_id)
    LOGGER.info("editor id is %s", data.get_me_id(article_id))
    LOGGER.info(str(type(data.get_me_id(article_id))))
    editor.auth_id = data.get_me_id(article_id)
    affiliation = ea.Affiliation()
    department = data.get_me_department(article_id)
    if department.strip() != "":
        affiliation.department = department
    affiliation.institution = data.get_me_institution(article_id)
    affiliation.country = data.get_me_country(article_id)

    # editor.auth_id = `int(author_id)`we have a me_id, but I need to determine
    # whether that Id is the same as the relevent author id
    editor.set_affiliation(affiliation)
    article.add_contributor(editor)
    return True


def set_funding(article, article_id):
    """
    Instantiate one eLifeFundingAward for each funding award
    Add principal award recipients in the order of author position for the article
    Finally add the funding objects to the article in the order of funding position
    """
    LOGGER.info("in set_funding")
    if not article:
        return False

    # Set the funding note from the manuscript level
    article.funding_note = data.get_funding_note(article_id)

    # Query for all funding award data keys
    funder_ids = data.get_funding_ids(article_id)

    # Keep track of funding awards by position in a dict
    funding_awards = OrderedDict()

    # First pass, build the funding awards
    if funder_ids:
        for (funder_article_id, author_id, funder_position) in funder_ids:
            # print (article_id, author_id, funder_position)
            funder_identifier = data.get_funder_identifier(
                funder_article_id, author_id, funder_position)
            funder = utils.decode_cp1252(utils.clean_funder(
                data.get_funder(funder_article_id, author_id, funder_position)))
            award_id = data.get_award_id(funder_article_id, author_id, funder_position)

            if funder_position not in funding_awards.keys():
                # Initialise the object values
                funding_awards[funder_position] = ea.FundingAward()
                if funder:
                    funding_awards[funder_position].institution_name = funder
                if funder_identifier and funder_identifier.strip() != "":
                    funding_awards[funder_position].institution_id = funder_identifier
                if award_id and award_id.strip() != "":
                    funding_awards[funder_position].add_award_id(award_id)

    # Second pass, add the primary award recipients in article author order
    for position in sorted(funding_awards.keys()):
        for contrib in article.contributors:
            for (funder_article_id, author_id, funder_position) in funder_ids:
                if position == funder_position and contrib.auth_id == author_id:
                    funding_awards[position].add_principal_award_recipient(contrib)

    # Add funding awards to the article object, sorted by position
    for position in sorted(funding_awards.keys()):
        article.add_funding_award(funding_awards.get(position))
    return True


def parse_ethics(ethic):
    """
    Given angle bracket escaped XML string, parse
    animal and human ethic comments, and return
    a list of strings if involved_comments tag
    is found. Boiler plate prefix added too.
    """

    ethics = []
    reparsed = None
    parse_status = None

    # Decode escaped angle brackets
    LOGGER.info("ethic is %s", ethic)
    ethic_xml = utils.unserialise_angle_brackets(ethic)
    ethic_xml = etoolsutils.escape_ampersand(ethic_xml)
    LOGGER.info("ethic is %s", ethic_xml)

    # Parse XML
    try:
        reparsed = minidom.parseString(ethic_xml)
        parse_status = True
    except ExpatError:
        parse_status = False
        LOGGER.info("ethic reparsed is %s", reparsed)

    # Extract comments
    if reparsed:
        for ethic_type in 'animal_subjects', 'human_subjects':
            ethic_node = reparsed.getElementsByTagName(ethic_type)[0]
            for node in ethic_node.childNodes:
                if node.nodeName == 'involved_comments':
                    text_node = node.childNodes[0]
                    ethic_text = text_node.nodeValue

                    # Add boilerplate
                    if ethic_type == 'animal_subjects':
                        ethic_text = 'Animal experimentation: ' + ethic_text.strip()
                    elif ethic_type == 'human_subjects':
                        ethic_text = 'Human subjects: ' + ethic_text.strip()

                    # Decode unicode characters
                    ethics.append(utils.entity_to_unicode(ethic_text))

    return parse_status, ethics


def parse_dataset_node(dataset_node, dataset_type):
    "extract attributes from a minidom node and populate a Dataset object"
    dataset = ea.Dataset()

    dataset.dataset_type = dataset_type

    for node in dataset_node.childNodes:

        if node.nodeName == 'authors_text_list' and node.childNodes:
            text_node = node.childNodes[0]
            for author_name in text_node.nodeValue.split(','):
                if author_name.strip() != '':
                    dataset.add_author(author_name.lstrip())

        if node.nodeName == 'title':
            text_node = node.childNodes[0]
            dataset.title = utils.entity_to_unicode(text_node.nodeValue)

        if node.nodeName == 'id':
            text_node = node.childNodes[0]
            dataset.source_id = utils.entity_to_unicode(text_node.nodeValue)

        if node.nodeName == 'license_info':
            text_node = node.childNodes[0]
            dataset.license_info = utils.entity_to_unicode(text_node.nodeValue)

        if node.nodeName == 'year' and node.childNodes:
            text_node = node.childNodes[0]
            dataset.year = utils.entity_to_unicode(text_node.nodeValue)

    return dataset


def parse_datasets(datasets_content):
    """
    Datasets content is XML with escaped angle brackets
    """
    datasets = []
    data_availability = None
    reparsed = None
    parse_status = None

    # Decode escaped angle brackets
    LOGGER.info("datasets is %s", datasets_content)
    datasets_xml = utils.escape_angle_brackets(datasets_content)
    datasets_xml = utils.unserialise_angle_brackets(datasets_xml)
    datasets_xml = etoolsutils.escape_ampersand(datasets_xml)
    LOGGER.info("datasets is %s", datasets_xml)

    # Parse XML
    try:
        reparsed = minidom.parseString(datasets_xml)
        parse_status = True
    except ExpatError:
        LOGGER.info("datasets reparsed is %s", reparsed)
        parse_status = False

    # Extract comments
    if reparsed:
        for dataset_type in 'datasets', 'prev_published_datasets':
            datasets_nodes = reparsed.getElementsByTagName(dataset_type)[0]
            for dataset_node in datasets_nodes.getElementsByTagName("dataset"):
                datasets.append(parse_dataset_node(dataset_node, dataset_type))

        # Parse the data availability statement
        if reparsed.getElementsByTagName('data_availability_textbox'):
            data_availability_node = reparsed.getElementsByTagName('data_availability_textbox')
            if data_availability_node[0].childNodes:
                data_availability = utils.entity_to_unicode(
                    data_availability_node[0].childNodes[0].nodeValue)

    return parse_status, datasets, data_availability


def parse_group_authors(group_authors):
    """
    Given a raw group author value from the data files,
    check for empty, whitespace, zero
    If not empty, remove extra numbers from the end of the string
    Return a dictionary of dict[author_position] = collab_name
    """
    group_author_dict = OrderedDict()
    if not group_authors:
        group_author_dict = None
    elif group_authors.strip() == "" or group_authors.strip() == "0":
        group_author_dict = None
    else:

        # Parse out elements into a list, clean and
        #  add the the dictionary using some steps

        # Split the string on the first delimiter
        group_author_list = group_authors.split('order_start')

        for group_author_string in group_author_list:
            if group_author_string == "":
                continue

            # Now split on the second delimiter
            position_and_name = group_author_string.split('order_end')

            author_position = position_and_name[0]

            # Strip numbers at the end
            if len(position_and_name) > 1:
                group_author = position_and_name[1].rstrip("1234567890")

                # Finally, add to the dict noting the authors position
                group_author_dict[author_position] = group_author

    return group_author_dict


def build_article(article_id):
    """
    Given an article_id, instantiate and populate the article objects
    """
    error_count = 0
    error_messages = []

    # Only happy with string article_id - cast it now to be safe!
    article_id = str(article_id)

    article = instantiate_article(article_id)

    # Run each of the below functions to build the article object components
    article_set_functions = [
        set_title, set_abstract, set_article_type, set_license, set_dates, set_ethics,
        set_datasets, set_categories, set_organsims, set_author_info, set_editor_info,
        set_keywords, set_funding]
    for set_function in article_set_functions:
        if not set_function(article, article_id):
            error_count = error_count + 1
            error_messages.append("article_id " + str(article_id)
                                  + " error in " + set_function.__name__)

    # Building from CSV data it must be a POA type, set it
    if article:
        article.is_poa = True

    print(error_count)

    # default conflict text
    if article:
        article.conflict_default = "The authors declare that no competing interests exist."

    if error_count == 0:
        return article, error_count, error_messages

    return None, error_count, error_messages
