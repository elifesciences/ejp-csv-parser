from __future__ import print_function
import logging
import time
from collections import OrderedDict
from xml.dom import minidom
from elifearticle import article as ea
from elifearticle import utils as eautils
from elifetools import utils as etoolsutils
import ejpcsvparser.utils as utils
import ejpcsvparser.csv_data as data

logger = logging.getLogger('parse')
hdlr = logging.FileHandler('parse.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)


def instantiate_article(article_id):
    logger.info("in instantiate_article for " + str(article_id))
    try:
        doi = data.get_doi(article_id)
        # Fallback if doi string is blank, default to eLife concatenated
        if doi.strip() == "":
            doi = utils.get_elife_doi(article_id)
        #title = get_title(article_id)
        article = ea.Article(doi, title=None)
        return article
    except:
        logger.error("could not create article class")
        return None


def set_title(article, article_id):
    logger.info("in set_title")
    try:
        title = data.get_title(article_id)
        article.title = utils.convert_to_xml_string(title)
        return True
    except:
        logger.error("could not set title ")
        return False


def set_abstract(article, article_id):
    logger.info("in set_abstract")
    try:
        abstract = utils.decode_cp1252(data.get_abstract(article_id))
        article.abstract = utils.convert_to_xml_string(abstract)
        article.manuscript = article_id
        return True
    except:
        logger.error("could not set abstract ")
        return False


def set_article_type(article, article_id):
    logger.info("in set_article_type")
    try:
        article_type_id = data.get_article_type(article_id)

        # Boilerplate article-type values based on id in CSV file
        article_type_index = OrderedDict()

        article_type_index['1'] = {
            'article_type':    'research-article',
            'display_channel': 'Research Article'}
        article_type_index['10'] = {
            'article_type':    'research-article',
            'display_channel': 'Feature Article'}
        article_type_index['14'] = {
            'article_type':    'research-article',
            'display_channel': 'Short Report'}
        article_type_index['15'] = {
            'article_type':    'research-article',
            'display_channel': 'Research Advance'}
        article_type_index['19'] = {
            'article_type':    'research-article',
            'display_channel': 'Tools and Resources'}

        article_type = article_type_index[str(article_type_id)]
        article.article_type = article_type['article_type']
        article.display_channel = article_type['display_channel']
        return True
    except:
        logger.error("could not set article_type")
        return False

def set_license(article, article_id):
    logger.info("in set_license")
    try:
        license_id = data.get_license(article_id)
        license_object = ea.License(license_id)

        # Boilerplate license values based on the license_id
        if int(license_id) == 1:
            license_object.license_id = license_id
            license_object.license_type = "open-access"
            license_object.copyright = True
            license_object.href = "http://creativecommons.org/licenses/by/4.0/"
            license_object.name = "Creative Commons Attribution License"
            license_object.paragraph1 = "This article is distributed under the terms of the "
            license_object.paragraph2 = (
                " permitting unrestricted use and redistribution provided that the " +
                "original author and source are credited.")
        elif int(license_id) == 2:
            license_object.license_id = license_id
            license_object.license_type = "open-access"
            license_object.copyright = False
            license_object.href = "http://creativecommons.org/publicdomain/zero/1.0/"
            license_object.name = "Creative Commons CC0"
            license_object.paragraph1 = (
                "This is an open-access article, free of all copyright, and may be " +
                "freely reproduced, distributed, transmitted, modified, built upon, or " +
                "otherwise used by anyone for any lawful purpose. The work is made " +
                "available under the ")
            license_object.paragraph2 = " public domain dedication."

        article.license = license_object
        return True
    except:
        logger.error("could not set license")
        return False

def set_dates(article, article_id):
    logger.info("in set_dates")
    try:
        accepted_date = data.get_accepted_date(article_id)
        t_accepted = time.strptime(accepted_date.split()[0], "%Y-%m-%d")
        accepted = ea.ArticleDate("accepted", t_accepted)
        article.add_date(accepted)
        logger.info(str(accepted_date))

        received_date = data.get_received_date(article_id)
        if received_date.strip() == "":
            # Use the alternate date column receipt_date if received_date is blank
            received_date = data.get_receipt_date(article_id)
        t_received = time.strptime(received_date.split()[0], "%Y-%m-%d")
        received = ea.ArticleDate("received", t_received)
        article.add_date(received)

        # set the license date to be the same as the accepted date
        date_license = ea.ArticleDate("license", t_accepted)
        article.add_date(date_license)
        return True
    except:
        logger.error("could not set dates")
        return False


def set_ethics(article, article_id):
    logger.info("in set_ethics")
    try:
        ethic = data.get_ethics(article_id)
        logger.info(ethic)
        if ethic:
            ethics = parse_ethics(ethic)
            for e in ethics:
                article.add_ethic(e)
        return True
    except:
        logger.error("could not set ethics")
        return False


def set_datasets(article, article_id):
    logger.info("in set_datasets")
    try:
        datasets = data.get_datasets(article_id)
        logger.info(datasets)
        if datasets:
            dataset_objects = parse_datasets(datasets)
            for dataset in dataset_objects:
                article.add_dataset(dataset)
        return True
    except:
        logger.error("could not set datasets")
        return False

def set_categories(article, article_id):
    logger.info("in set_categories")
    try:
        categories = data.get_subjects(article_id)
        for category in categories:
            article.add_article_category(category)
        return True
    except:
        logger.error("could not set categories")
        return False

def set_organsims(article, article_id):
    logger.info("in set_categories")
    try:
        research_organisms = data.get_organisms(article_id)
        for research_organism in research_organisms:
            if research_organism.strip() != "":
                article.add_research_organism(research_organism)
        return True
    except:
        logger.error("could not set organisms")
        return False


def set_keywords(article, article_id):
    logger.info("in set_keywords")
    try:
        keywords = data.get_keywords(article_id)
        for keyword in keywords:
            article.add_author_keyword(keyword)
        return True
    except:
        logger.error("could not set keywords")
        return False


def set_author_info(article, article_id):
    """
    author information
    Save the contributor and their position in the list in a dict,
    for both authors and group authors,
    Then add the contributors to the article object in order of their position
    """
    logger.info("in set_author_info")
    authors_dict = {}

    # check there are any authors before continuing
    author_ids = data.get_author_ids(article_id)
    if not author_ids and not data.get_group_authors(article_id):
        logger.error("could not find any author data")
        return False

    try:
        for author_id in author_ids:

            author_type = "author"

            first_name = utils.decode_cp1252(data.get_author_first_name(article_id, author_id))
            last_name = utils.decode_cp1252(data.get_author_last_name(article_id, author_id))
            middle_name = utils.decode_cp1252(data.get_author_middle_name(article_id, author_id))
            #initials = middle_name_initials(middle_name)
            if middle_name.strip() != "":
                # Middle name add to the first name / given name
                first_name += " " + middle_name
            author = ea.Contributor(author_type, last_name, first_name)
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
                email = data.get_author_email(article_id, author_id)
                affiliation.email = data.get_author_email(article_id, author_id)
                author.corresp = True

            conflict = data.get_author_conflict(article_id, author_id)
            if conflict.strip() != "":
                author.set_conflict(conflict)

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
                    author_type = "author"
                    last_name = None
                    first_name = None
                    collab = group_author_dict.get(author_position)
                    author = ea.Contributor(author_type, last_name, first_name, collab)

                    # Add the author to the dictionary recording their position in the list
                    authors_dict[int(author_position)] = author

        # Finally add authors to the article sorted by their position
        for author_position in sorted(authors_dict.keys()):
            #print article_id, author_position, author
            article.add_contributor(authors_dict.get(author_position))

        return True
    except:
        logger.error("could not set authors")
        return False


def set_editor_info(article, article_id):
    logger.info("in set_editor_info")
    try:
        author_type = "editor"

        first_name = utils.decode_cp1252(data.get_me_first_nm(article_id))
        last_name = utils.decode_cp1252(data.get_me_last_nm(article_id))
        middle_name = utils.decode_cp1252(data.get_me_middle_nm(article_id))
        #initials = middle_name_initials(middle_name)
        if middle_name.strip() != "":
            # Middle name add to the first name / given name
            first_name += " " + middle_name
        # create an instance of the POSContributor class
        editor = ea.Contributor(author_type, last_name, first_name)
        logger.info("editor is: " + eautils.unicode_value(editor))
        logger.info("getting ed id for article " + str(article_id))
        logger.info("editor id is " + str(data.get_me_id(article_id)))
        logger.info(str(type(data.get_me_id(article_id))))
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
    except:
        logger.error("could not set editor")
        return False


def set_funding(article, article_id):
    """
    Instantiate one eLifeFundingAward for each funding award
    Add principal award recipients in the order of author position for the article
    Finally add the funding objects to the article in the order of funding position
    """
    logger.info("in set_funding")
    try:
        # Set the funding note from the manuscript level
        article.funding_note = data.get_funding_note(article_id)

        # Query for all funding award data keys
        funder_ids = data.get_funding_ids(article_id)

        # Keep track of funding awards by position in a dict
        funding_awards = OrderedDict()

        # First pass, build the funding awards
        for (article_id, author_id, funder_position) in funder_ids:
            #print (article_id, author_id, funder_position)
            funder_identifier = data.get_funder_identifier(article_id, author_id, funder_position)
            funder = utils.decode_cp1252(utils.clean_funder(
                data.get_funder(article_id, author_id, funder_position)))
            award_id = data.get_award_id(article_id, author_id, funder_position)

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
            award = funding_awards.get(position)
            for contrib in article.contributors:
                for (article_id, author_id, funder_position) in funder_ids:
                    if position == funder_position and contrib.auth_id == author_id:
                        funding_awards[position].add_principal_award_recipient(contrib)

        # Add funding awards to the article object, sorted by position
        for position in sorted(funding_awards.keys()):
            article.add_funding_award(funding_awards.get(position))
        return True
    except:
        logger.error("could not set funding")
        return False


def parse_ethics(ethic):
    """
    Given angle bracket escaped XML string, parse
    animal and human ethic comments, and return
    a list of strings if involved_comments tag
    is found. Boiler plate prefix added too.
    """

    ethics = []

    # Decode escaped angle brackets
    logger.info("ethic is " + str(ethic))
    ethic_xml = utils.unserialise_angle_brackets(ethic)
    ethic_xml = etoolsutils.escape_ampersand(ethic_xml)
    logger.info("ethic is " + str(ethic_xml))

    # Parse XML
    reparsed = minidom.parseString(ethic_xml)

    # Extract comments
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

    return ethics

def parse_datasets(datasets_content):
    """
    Datasets content is XML with escaped angle brackets
    """
    datasets = []

    # Decode escaped angle brackets
    logger.info("datasets is " + str(datasets_content))
    datasets_xml = utils.unserialise_angle_brackets(datasets_content)
    datasets_xml = etoolsutils.escape_ampersand(datasets_xml)
    logger.info("datasets is " + str(datasets_xml))

    # Parse XML
    reparsed = minidom.parseString(datasets_xml)

    # Extract comments
    for dataset_type in 'datasets', 'prev_published_datasets':
        datasets_nodes = reparsed.getElementsByTagName(dataset_type)[0]

        for d_nodes in datasets_nodes.getElementsByTagName("dataset"):
            dataset = ea.Dataset()

            dataset.dataset_type = dataset_type

            for node in d_nodes.childNodes:

                if node.nodeName == 'authors_text_list' and len(node.childNodes) > 0:
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

                if node.nodeName == 'year' and len(node.childNodes) > 0:
                    text_node = node.childNodes[0]
                    dataset.year = utils.entity_to_unicode(text_node.nodeValue)

            datasets.append(dataset)

    return datasets

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
    else:
        return None, error_count, error_messages
