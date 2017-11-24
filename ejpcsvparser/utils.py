import re
import ejpcsvparser.settings as settings
from elifetools import utils as etoolsutils
from elifearticle import utils as eautils


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


def repl(match):
    # Convert hex to int to unicode character
    chr_code = int(match.group(1), 16)
    return unichr(chr_code)


def entity_to_unicode(string):
    """
    Quick convert unicode HTML entities to unicode characters
    using a regular expression replacement
    """
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
    string = re.sub(r"&#x(....);", repl, string)
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
    string = entity_to_unicode(string).encode('utf-8')
    string = decode_brackets(string)
    string = eautils.replace_tags(string, 'i', 'italic')
    string = eautils.replace_tags(string, 'u', 'underline')
    string = eautils.replace_tags(string, 'b', 'bold')
    string = eautils.replace_tags(string, 'em', 'italic')
    string = etoolsutils.escape_unmatched_angle_brackets(string, allowed_tags())
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
    try:
        # See if it is not safe to encode to ascii first
        junk = string.encode('ascii')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Wrap the decode in another exception to make sure this never fails
        try:
            string = string.decode('cp1252')
        except:
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