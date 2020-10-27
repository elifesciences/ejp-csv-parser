import unittest
from six.moves import reload_module
from mock import patch
from ejpcsvparser import csv_data as data

from tests import csv_test_settings


def override_settings():
    "override the settings for testing"
    data.CSV_PATH = csv_test_settings.CSV_PATH
    data.ROWS_WITH_COLNAMES = csv_test_settings.ROWS_WITH_COLNAMES
    data.DATA_START_ROW = csv_test_settings.DATA_START_ROW
    data.CSV_FILES = csv_test_settings.CSV_FILES
    data.COLUMN_HEADINGS = csv_test_settings.CSV_COLUMN_HEADINGS
    data.OVERFLOW_CSV_FILES = csv_test_settings.OVERFLOW_CSV_FILES


def clean_csv_fixture_path(path):
    return '/'.join(['tests', 'test_data', 'clean_csv', path])


class TestCsvData(unittest.TestCase):
    "base class for testing CSV data to override settings"
    def setUp(self):
        override_settings()


class TestCleanCsv(TestCsvData):

    def test_join_lines(self):
        join_lines_passes = []
        join_lines_passes.append(("", "\n", 1, "\n"))
        join_lines_passes.append(("", "\n", 10, " "))
        join_lines_passes.append(("one\n", '"', 10, 'one"'))
        join_lines_passes.append(("one\r\n", '    two', 10, 'onetwo'))
        join_lines_passes.append(("\n", "two \n", 10, "two \n"))
        for (line_one, line_two, line_number, expected) in join_lines_passes:
            content = data.join_lines(line_one, line_two, line_number)
            self.assertEqual(
                content, expected,
                '{line_one} + {line_two} does not equal {expected}, got {content}'.format(
                    line_one=line_one,
                    line_two=line_two,
                    expected=expected,
                    content=content
                    ))

    def test_do_add_line(self):
        do_add_line_passes = []
        do_add_line_passes.append(("", 1, True))  # blank header row
        do_add_line_passes.append(('"A typical header row"', 1, True))
        do_add_line_passes.append(("", 10, False))
        do_add_line_passes.append(('"a full line","it is"', 10, True))
        do_add_line_passes.append(('"', 10, True))
        for (content, line_number, expected) in do_add_line_passes:
            add_line = data.do_add_line(content, line_number)
            self.assertEqual(
                add_line, expected,
                '{content} as line number {line} does not match {expected}, got {add_line}'.format(
                    content=content,
                    line=line_number,
                    expected=expected,
                    add_line=add_line
                    ))

    def test_flatten_lines(self):
        "test flattening lines separately"
        flatten_lines_passes = []
        flatten_lines_passes.append((0, ["\"a\n", "   b\n", '"\n'], '"ab"\n'))
        for (data_start_row, iterable, expected) in flatten_lines_passes:
            content = data.flatten_lines(iterable, data_start_row)
            self.assertEqual(
                content, expected,
                '{iterable} does not flatten to {expected}, got {content}'.format(
                    iterable=iterable,
                    expected=expected,
                    content=content
                    ))

    def test_clean_csv(self):
        "test clean_csv using file read and writes"
        clean_csv_passes = []
        clean_csv_passes.append(('manuscript.csv', 'manuscript_expected.csv'))
        clean_csv_passes.append(('datasets.csv', 'datasets_expected.csv'))
        for (input_csv, expected_csv) in clean_csv_passes:
            input_csv_path = clean_csv_fixture_path(input_csv)
            expected_csv_path = clean_csv_fixture_path(expected_csv)
            new_path = data.clean_csv(input_csv_path)
            content = None
            expected_data = None
            with open(new_path, 'rb') as csv_data:
                content = csv_data.read()
            with open(expected_csv_path, 'rb') as expected_csv_data:
                expected_data = expected_csv_data.read()
            # test assertions
            self.assertIsNotNone(content)
            self.assertIsNotNone(expected_data)
            self.assertEqual(content, expected_data,
                             '{input_csv} does not equal {expected_csv}'.format(
                                 input_csv=input_csv,
                                 expected_csv=expected_csv
                                 ))


class TestIndexing(TestCsvData):

    def test_get_csv_path(self):
        path_type = 'authors'
        expected = 'tests/test_data/poa_author.csv'
        self.assertEqual(data.get_csv_path(path_type), expected)

    def test_get_csv_col_names(self):
        table_type = 'license'
        expected = ['poa_m_ms_id', 'poa_m_ms_no', 'poa_l_license_id', 'poa_l_license_dt']
        self.assertEqual(data.get_csv_col_names(table_type), expected)

    def test_get_csv_data_rows(self):
        table_type = 'authors'
        expected_row_count = 115
        self.assertEqual(len(data.get_csv_data_rows(table_type)), expected_row_count)
        # also test some overflow files for coverage
        table_type = 'abstract'
        expected_row_count = 9
        self.assertEqual(len(data.get_csv_data_rows(table_type)), expected_row_count)
        table_type = 'ethics'
        expected_row_count = 9
        self.assertEqual(len(data.get_csv_data_rows(table_type)), expected_row_count)

    def test_index_authors_on_article_id(self):
        # reload module first to avoid memoize remembering data from other test scenarios
        reload_module(data)
        expected_row_count = 9
        article_index = data.index_authors_on_article_id()
        self.assertEqual(len(article_index), expected_row_count)

    def test_index_authors_on_author_id(self):
        # reload module first to avoid memoize remembering data from other test scenarios
        reload_module(data)
        expected_row_count = 9
        article_author_index = data.index_authors_on_author_id()
        self.assertEqual(len(article_author_index), expected_row_count)


class TestArticleAttributes(TestCsvData):

    def test_get_article_attributes(self):
        article_id = 3
        attribute_type = 'title'
        attribute_label = 'poa_m_title_tag'
        expected = ['''This, 'title, includes "quotation", marks & more &#x00FC;''']
        self.assertEqual(data.get_article_attributes(
            article_id, attribute_type, attribute_label), expected)


class TestSubjects(TestCsvData):

    def test_get_subjects(self):
        article_id = 3
        expected = ['Immunology', 'Microbiology and infectious disease']
        self.assertEqual(data.get_subjects(article_id), expected)


class TestOrganisms(TestCsvData):

    def test_get_organisms(self):
        article_id = 3
        expected = ['<i>B. subtilis</i>', '<i>D. melanogaster</i>', '<i>E. coli</i>', 'Mouse']
        self.assertEqual(data.get_organisms(article_id), expected)


class TestLicense(TestCsvData):

    def test_get_license(self):
        article_id = 3
        expected = '1'
        self.assertEqual(data.get_license(article_id), expected)


class TestKeywords(TestCsvData):

    def test_get_keywords(self):
        article_id = 3
        expected = ['innate immunity', 'histones', 'lipid droplet', 'anti-bacterial']
        self.assertEqual(data.get_keywords(article_id), expected)


class TestTitle(TestCsvData):

    def test_get_title(self):
        article_id = 3
        expected = u'''This, 'title, includes "quotation", marks & more \xfc'''
        self.assertEqual(data.get_title(article_id), expected)


class TestAbstract(TestCsvData):

    def test_get_abstract(self):
        article_id = 3
        expected = ('This abstract includes LTLTiGTGTPINK1LTLT/iGTGT &amp; ' +
                    'LTLTiGTGTparkinLTLT/iGTGT LTLT 20 GTGT 10')
        self.assertEqual(data.get_abstract(article_id), expected)


class TestDoi(TestCsvData):

    def test_get_doi(self):
        article_id = 3
        expected = '10.7554/eLife.00003'
        self.assertEqual(data.get_doi(article_id), expected)


class TestArticleType(TestCsvData):

    def test_get_article_type(self):
        article_id = 3
        expected = '10'
        self.assertEqual(data.get_article_type(article_id), expected)


class TestDates(TestCsvData):

    def test_get_accepted_date(self):
        article_id = 3
        expected = '2012-09-05 00:00:00.000'
        self.assertEqual(data.get_accepted_date(article_id), expected)

    def test_get_received_date(self):
        article_id = 3
        expected = '2012-06-20 17:35:02.433'
        self.assertEqual(data.get_received_date(article_id), expected)

    def test_get_receipt_date(self):
        article_id = 3
        expected = '2012-06-27 05:06:17.413'
        self.assertEqual(data.get_receipt_date(article_id), expected)


class TestEditor(TestCsvData):

    def test_get_me_id(self):
        article_id = 3
        expected = '1123'
        self.assertEqual(data.get_me_id(article_id), expected)

    def test_get_me_last_nm(self):
        article_id = 3
        expected = 'Kolter'
        self.assertEqual(data.get_me_last_nm(article_id), expected)

    def test_get_me_first_nm(self):
        article_id = 3
        expected = 'Roberto'
        self.assertEqual(data.get_me_first_nm(article_id), expected)

    def test_get_me_middle_nm(self):
        article_id = 3
        expected = ' '
        self.assertEqual(data.get_me_middle_nm(article_id), expected)

    def test_get_me_suffix(self):
        article_id = 7
        expected = 'Jnr'
        self.assertEqual(data.get_me_suffix(article_id), expected)

    @patch('ejpcsvparser.csv_data.article_first_value')
    def test_get_me_suffix_exception(self, fake_article_first_value):
        fake_article_first_value.side_effect = ValueError('An exception')
        article_id = 7
        expected = None
        self.assertEqual(data.get_me_suffix(article_id), expected)

    def test_get_me_institution(self):
        article_id = 3
        expected = 'Harvard Medical School'
        self.assertEqual(data.get_me_institution(article_id), expected)

    def test_get_me_department(self):
        article_id = 3
        expected = 'Department of Microbiology and Immunobiology'
        self.assertEqual(data.get_me_department(article_id), expected)

    def test_get_me_country(self):
        article_id = 3
        expected = 'United States'
        self.assertEqual(data.get_me_country(article_id), expected)


class TestEthics(TestCsvData):

    def test_get_ethics(self):
        article_id = 3
        expected = ('LTLTxmlGTGTLTLTanimal_subjectsGTGTLTLTinvolved_commentsGTGTAll animals ' +
                    'received human care and experimental treatment  authorized by the Animal ' +
                    'Experimentation Ethics Committee (CEEA) of the University of Barcelona ' +
                    '(expedient number 78/05), in compliance with institutional guidelines ' +
                    'regulated by the European Community.LTLT/involved_commentsGTGT' +
                    'LTLTinvolved_indGTGT1LTLT/involved_indGTGTLTLT/animal_subjectsGTGT' +
                    'LTLThuman_subjectsGTGTLTLTinvolved_indGTGT0LTLT/involved_indGTGT' +
                    'LTLT/human_subjectsGTGTLTLT/xmlGTGT')
        self.assertEqual(data.get_ethics(article_id), expected)
        article_id = 99999
        expected = None
        self.assertEqual(data.get_ethics(article_id), expected)


class TestAuthor(TestCsvData):

    def test_get_author_ids(self):
        article_id = 7
        expected = ['1399', '1400', '1013']
        self.assertEqual(data.get_author_ids(article_id), expected)

    def test_get_author_attribute(self):
        article_id = '7'
        author_id = '1399'
        attribute_name = 'poa_a_last_nm'
        expected = 'Schuman'
        self.assertEqual(data.get_author_attribute(article_id, author_id, attribute_name), expected)

    def test_get_author_suffix(self):
        article_id = '7'
        author_id = '1399'
        attribute_name = 'poa_a_suffix'
        expected = 'Jnr'
        self.assertEqual(data.get_author_attribute(article_id, author_id, attribute_name), expected)

    @patch('ejpcsvparser.csv_data.get_author_attribute')
    def test_get_author_suffix_exception(self, fake_get_author_attribute):
        fake_get_author_attribute.side_effect = ValueError('An exception')
        article_id = 7
        author_id = '1399'
        expected = None
        self.assertEqual(data.get_author_suffix(article_id, author_id), expected)

    @patch('ejpcsvparser.csv_data.index_authors_on_author_id')
    def test_get_author_attribute_bad_article_id(self, fake_index):
        fake_index.return_value = {'99999': [1, 2]}
        article_id = '7'
        author_id = '1399'
        attribute_name = 'poa_a_last_nm'
        expected = None
        self.assertEqual(data.get_author_attribute(article_id, author_id, attribute_name), expected)

    @patch('ejpcsvparser.csv_data.index_authors_on_author_id')
    def test_get_author_attribute_bad_author_id(self, fake_index):
        fake_index.return_value = {'99999': [1, 2]}
        article_id = '99999'
        author_id = '1399'
        attribute_name = 'poa_a_last_nm'
        expected = None
        self.assertEqual(data.get_author_attribute(article_id, author_id, attribute_name), expected)

    def test_get_author_position(self):
        article_id = '7'
        author_id = '1399'
        expected = '1'
        self.assertEqual(data.get_author_position(article_id, author_id), expected)

    def test_get_author_email(self):
        article_id = '7'
        author_id = '1399'
        expected = 'm@example.com'
        self.assertEqual(data.get_author_email(article_id, author_id), expected)

    def test_get_author_contrib_type(self):
        article_id = '7'
        author_id = '1399'
        expected = 'Contributing Author'
        self.assertEqual(data.get_author_contrib_type(article_id, author_id), expected)

    def test_get_author_dual_corresponding(self):
        article_id = '7'
        author_id = '1399'
        expected = ' '
        self.assertEqual(data.get_author_dual_corresponding(article_id, author_id), expected)
        article_id = '7'
        author_id = '1400'
        expected = '1'
        self.assertEqual(data.get_author_dual_corresponding(article_id, author_id), expected)

    def test_get_author_last_name(self):
        article_id = '7'
        author_id = '1399'
        expected = 'Schuman'
        self.assertEqual(data.get_author_last_name(article_id, author_id), expected)

    def test_get_author_first_name(self):
        article_id = '7'
        author_id = '1399'
        expected = 'Meredith'
        self.assertEqual(data.get_author_first_name(article_id, author_id), expected)

    def test_get_author_middle_name(self):
        article_id = '7'
        author_id = '1399'
        expected = 'C'
        self.assertEqual(data.get_author_middle_name(article_id, author_id), expected)

    def test_get_author_institution(self):
        article_id = '7'
        author_id = '1399'
        expected = 'Max Planck Institute for Chemical Ecology'
        self.assertEqual(data.get_author_institution(article_id, author_id), expected)

    def test_get_author_department(self):
        article_id = '7'
        author_id = '1399'
        expected = 'Department of Molecular Ecology'
        self.assertEqual(data.get_author_department(article_id, author_id), expected)

    def test_get_author_city(self):
        article_id = '7'
        author_id = '1399'
        expected = 'Jena'
        self.assertEqual(data.get_author_city(article_id, author_id), expected)

    def test_get_author_country(self):
        article_id = '7'
        author_id = '1399'
        expected = 'Germany'
        self.assertEqual(data.get_author_country(article_id, author_id), expected)

    def test_get_author_state(self):
        article_id = '7'
        author_id = '1399'
        expected = ' '
        self.assertEqual(data.get_author_state(article_id, author_id), expected)
        article_id = '3'
        author_id = '1211'
        expected = 'California'
        self.assertEqual(data.get_author_state(article_id, author_id), expected)

    def test_get_author_conflict(self):
        article_id = '7'
        author_id = '1399'
        expected = ' '
        self.assertEqual(data.get_author_conflict(article_id, author_id), expected)
        article_id = '7'
        author_id = '1013'
        expected = 'Senior Editor, <i>eLife</i>'
        self.assertEqual(data.get_author_conflict(article_id, author_id), expected)

    def test_get_author_orcid(self):
        article_id = '7'
        author_id = '1399'
        expected = ' '
        self.assertEqual(data.get_author_orcid(article_id, author_id), expected)
        article_id = '2725'
        author_id = '12398'
        expected = '0000-0002-8772-6845'
        self.assertEqual(data.get_author_orcid(article_id, author_id), expected)

    def test_get_group_authors(self):
        article_id = 2725
        expected = 'order_start15order_endANECS111'
        self.assertEqual(data.get_group_authors(article_id), expected)
        # test empty row
        article_id = 3
        expected = None
        self.assertEqual(data.get_group_authors(article_id), expected)


class TestDatasets(TestCsvData):

    def test_get_datasets(self):
        article_id = 7
        expected = ('LTLTxmlGTGTLTLTdata_availability_textboxGTGTOnly availability text' +
                    'LTLT/data_availability_textboxGTGTLTLTdatasetsGTGTLTLTdatasets_indGTGT0' +
                    'LTLT/datasets_indGTGTLTLT/datasetsGTGTLTLTprev_published_datasetsGTGT' +
                    'LTLTdatasets_indGTGT0LTLT/datasets_indGTGTLTLT/prev_published_datasetsGTGT' +
                    'LTLT/xmlGTGT')
        self.assertEqual(data.get_datasets(article_id), expected)
        # test missing row
        article_id = 99999
        expected = None
        self.assertEqual(data.get_datasets(article_id), expected)


class TestFunding(TestCsvData):

    def test_index_funding_table(self):
        article_index = data.index_funding_table()
        self.assertIsNotNone(article_index)
        self.assertEqual(list(article_index.keys()), ['7', '12717', '14874', '14997', '21598'])

    def test_get_funding_ids(self):
        article_id = '12717'
        expected = [('12717', '13727', '1'), ('12717', '13727', '2')]
        self.assertEqual(data.get_funding_ids(article_id), expected)

    def test_get_funding_attribute(self):
        article_id = '21598'
        author_id = '23404'
        funder_position = '1'
        attribute_name = 'poa_fund_ref_id'
        expected = '501100000925'
        self.assertEqual(data.get_funding_attribute(
            article_id, author_id, funder_position, attribute_name), expected)

    def test_get_funder(self):
        article_id = '12717'
        author_id = '13727'
        funder_position = '1'
        expected = 'HHS | NIH | National Institute of Neurological Disorders and Stroke (NINDS)'
        self.assertEqual(data.get_funder(article_id, author_id, funder_position), expected)

    def test_get_award_id(self):
        article_id = '12717'
        author_id = '13727'
        funder_position = '1'
        expected = '1R01NS066936'
        self.assertEqual(data.get_award_id(article_id, author_id, funder_position), expected)

    def test_get_funder_identifier(self):
        article_id = '12717'
        author_id = '13727'
        funder_position = '1'
        expected = '100000065'
        self.assertEqual(data.get_funder_identifier(
            article_id, author_id, funder_position), expected)

    def test_get_funding_note(self):
        article_id = '12717'
        expected = ('The funders had no role in study design, data collection and ' +
                    'interpretation, or the decision to submit the work for publication.')
        self.assertEqual(data.get_funding_note(article_id), expected)


if __name__ == '__main__':
    unittest.main()
