import re
from collections import OrderedDict
from elifetools import utils as etoolsutils
from elifearticle import utils as eautils
import ejpcsvparser.settings as settings


def allowed_tags():
    "tuple of whitelisted tags"
    return (
        '<i>', '</i>',
        '<italic>', '</italic>',
        '<b>', '</b>',
        '<bold>', '</bold>',
        '<sup>', '</sup>',
        '<sub>', '</sub>',
        '<u>', '</u>',
        '<underline>', '</underline>',
        '<b>', '</b>',
        '<bold>', '</bold>',
        '<p>', '</p>',
    )


def article_type_indexes():
    "boilerplate article-type values based on id in CSV file"
    article_type_index = OrderedDict()
    article_type_index['1'] = {
        'article_type':    'research-article',
        'display_channel': 'Research Article'}
    article_type_index['8'] = {
        'article_type':    'discussion',
        'display_channel': 'Feature Article'}
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
    article_type_index['21'] = {
        'article_type':    'research-article',
        'display_channel': 'Scientific Correspondence'}
    return article_type_index


def license_data(license_id):
    "boilerplate data to populate a license object keyed on the license_id"
    license_data = OrderedDict()
    if not license_id:
        return license_data
    if int(license_id) == 1:
        license_data['license_id'] = license_id
        license_data['license_type'] = "open-access"
        license_data['copyright'] = True
        license_data['href'] = "http://creativecommons.org/licenses/by/4.0/"
        license_data['name'] = "Creative Commons Attribution License"
        license_data['paragraph1'] = "This article is distributed under the terms of the "
        license_data['paragraph2'] = (
            " permitting unrestricted use and redistribution provided that the " +
            "original author and source are credited.")
    elif int(license_id) == 2:
        license_data['license_id'] = license_id
        license_data['license_type'] = "open-access"
        license_data['copyright'] = False
        license_data['href'] = "http://creativecommons.org/publicdomain/zero/1.0/"
        license_data['name'] = "Creative Commons CC0"
        license_data['paragraph1'] = (
            "This is an open-access article, free of all copyright, and may be " +
            "freely reproduced, distributed, transmitted, modified, built upon, or " +
            "otherwise used by anyone for any lawful purpose. The work is made " +
            "available under the ")
        license_data['paragraph2'] = " public domain dedication."
    return license_data


def entity_to_unicode(string):
    """
    Quick convert unicode HTML entities to unicode characters
    using a regular expression replacement
    """
    if not string:
        return string
    # Selected character replacements that have been seen
    replacements = []
    replacements.append((r"&alpha;", u"\u03b1"))
    replacements.append((r"&beta;", u"\u03b2"))
    replacements.append((r"&gamma;", u"\u03b3"))
    replacements.append((r"&delta;", u"\u03b4"))
    replacements.append((r"&epsilon;", u"\u03b5"))
    replacements.append((r"&ordm;", u"\u00ba"))
    replacements.append((r"&iuml;", u"\u00cf"))
    replacements.append((r"&ldquo;", '"'))
    replacements.append((r"&rdquo;", '"'))

    # First, replace numeric entities with unicode
    string = re.sub(r"&#x(....);", eautils.repl, string)
    # Second, replace some specific entities specified in the list
    for entity, replacement in replacements:
        string = re.sub(entity, replacement, string)
    return string


def entities(function):
    """
    Convert entities to unicode as a decorator
    """
    def wrapper(*args, **kwargs):
        value = function(*args, **kwargs)
        return entity_to_unicode(value)
    return wrapper


def decode_brackets(string):
    """
    Decode angle bracket escape sequence
    used to encode XML content
    """
    string = str(string)
    string = string.replace(settings.LESS_THAN_ESCAPE_SEQUENCE, '<')
    string = string.replace(settings.GREATER_THAN_ESCAPE_SEQUENCE, '>')
    return string


def unserialise_angle_brackets(escaped_string):
    unserial_xml = escaped_string.replace(settings.LESS_THAN_ESCAPE_SEQUENCE, "<")
    unserial_xml = unserial_xml.replace(settings.GREATER_THAN_ESCAPE_SEQUENCE, ">")
    return unserial_xml


def convert_to_xml_string(string):
    """
    For input strings with escaped tags and special characters
    issue a set of conversion functions to prepare it prior
    to adding it to an article object
    """
    string = entity_to_unicode(string)
    string = decode_brackets(string)
    string = eautils.replace_tags(string, 'i', 'italic')
    string = eautils.replace_tags(string, 'u', 'underline')
    string = eautils.replace_tags(string, 'b', 'bold')
    string = eautils.replace_tags(string, 'em', 'italic')
    string = etoolsutils.escape_unmatched_angle_brackets(string, allowed_tags())
    return string


def escape_angle_brackets(string):
    "replace angle brackets only for when parsing escaped XML from CSV files"
    try:
        return string.replace('<', '&lt;').replace('>', '&gt;')
    except AttributeError:
        return string


def get_elife_doi(article_id):
    """
    Given an article_id, return a DOI for the eLife journal
    """
    doi = "10.7554/eLife." + str(int(article_id)).zfill(5)
    return doi


def decode_cp1252(string):
    """
    CSV files look to be in CP-1252 encoding (Western Europe)
    Decoding to ASCII is normally fine, except when it gets an O umlaut, for example
    In this case, values must be decoded from cp1252 in order to be added as unicode
    to the final XML output.
    This function helps do that in selected places, like on author surnames
    """
    if not string:
        return string
    try:
        # See if it is not safe to encode to ascii first
        string.encode('ascii')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Wrap the decode in another exception to make sure this never fails
        try:
            string = string.decode('cp1252')
        except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
            pass
    return string


def clean_funder(funder):
    """
    Remove extra content from funder names
    separated by | character
    and anything in parentheses
    """
    funder = funder.split('|')[-1]
    funder = re.sub(r"\(.*\)", "", funder)
    funder = funder.rstrip().lstrip()
    return funder
