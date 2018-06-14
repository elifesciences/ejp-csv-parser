import unittest
import time
from mock import patch
from ejpcsvparser import parse
from elifearticle.article import Article


def generate_date(date_string="2013-10-03", date_format="%Y-%m-%d"):
    "generate struct_time object for testing"
    return time.strptime(date_string, date_format)


class TestParse(unittest.TestCase):

    def setUp(self):
        pass


    def test_build_article(self):
        "build an article"
        article_id = 21598
        article, error_count, error_messages = parse.build_article(article_id)
        self.assertIsNotNone(article)
        article_id = 99999
        article, error_count, error_messages = parse.build_article(article_id)
        self.assertIsNone(article)


    def test_instantiate_article(self):
        article_id = 21598
        article = parse.instantiate_article(article_id)
        self.assertIsNotNone(article, 'could not instantiate article object')
        self.assertEqual(article.doi, '10.7554/eLife.21598')
        # test non-existing data for test coverage
        article_id = 99999
        self.assertIsNone(parse.instantiate_article(article_id))


    @patch('ejpcsvparser.csv_data.get_doi')
    def test_instantiate_article_no_doi(self, fake_get_doi):
        fake_get_doi.return_value = ''
        article_id = 21598
        article = parse.instantiate_article(article_id)
        self.assertIsNotNone(article, 'could not instantiate article object')
        self.assertEqual(article.doi, '10.7554/eLife.21598')


    def test_set_title(self):
        article = parse.instantiate_article('12')
        return_value = parse.set_title(article, '12')
        self.assertTrue(return_value)
        self.assertEqual(article.title, 'A title with Y<sup>1</sup>S<sup>2</sup>P<sup>3</sup>T<sup>4</sup>S<sup>5</sup>P<sup>6</sup>S<sup>7</sup> repeats, <italic>Drosophila</italic> and "quotations".')
        # test not finding a value
        article = Article()
        return_value = parse.set_title(article, '99999')
        self.assertFalse(return_value)


    def test_set_abstract(self):
        article = parse.instantiate_article('12')
        return_value = parse.set_abstract(article, '12')
        self.assertTrue(return_value)
        self.assertEqual(article.abstract, 'In this abstract are consensus Y<sup>1</sup>S<sup>2</sup>P<sup>3</sup>T<sup>4</sup>S<sup>5</sup>P<sup>6</sup>S<sup>7</sup> repeats, <italic>Drosophila</italic> and "quotations".')
        # test not finding a value
        article = Article()
        return_value = parse.set_abstract(article, '99999')
        self.assertFalse(return_value)


    def test_set_article_type(self):
        article = parse.instantiate_article('12')
        return_value = parse.set_article_type(article, '12')
        self.assertTrue(return_value)
        self.assertEqual(article.article_type, 'research-article')
        self.assertEqual(article.display_channel, 'Short Report')
        # test not finding a value
        article = Article()
        return_value = parse.set_article_type(article, '99999')
        self.assertFalse(return_value)


    @patch('ejpcsvparser.csv_data.get_article_type')
    def test_set_article_type_by_id(self, fake_get_article_type):
        "test allowable and disallowable article_type_id values"
        article_id = 21598
        article = parse.instantiate_article(article_id)
        # test id 1
        fake_get_article_type.return_value = '1'
        return_value = parse.set_article_type(article, article_id)
        self.assertTrue(return_value)
        self.assertEqual(article.article_type, 'research-article')
        self.assertEqual(article.display_channel, 'Research Article')
        # test id 10
        fake_get_article_type.return_value = '10'
        return_value = parse.set_article_type(article, article_id)
        self.assertTrue(return_value)
        self.assertEqual(article.article_type, 'research-article')
        self.assertEqual(article.display_channel, 'Feature Article')
        # test id 14
        fake_get_article_type.return_value = '14'
        return_value = parse.set_article_type(article, article_id)
        self.assertTrue(return_value)
        self.assertEqual(article.article_type, 'research-article')
        self.assertEqual(article.display_channel, 'Short Report')
        # test id 15
        fake_get_article_type.return_value = '15'
        return_value = parse.set_article_type(article, article_id)
        self.assertTrue(return_value)
        self.assertEqual(article.article_type, 'research-article')
        self.assertEqual(article.display_channel, 'Research Advance')
        # test id 19
        fake_get_article_type.return_value = '19'
        return_value = parse.set_article_type(article, article_id)
        self.assertTrue(return_value)
        self.assertEqual(article.article_type, 'research-article')
        self.assertEqual(article.display_channel, 'Tools and Resources')
        # test id that does not exist, recreate the object first
        article_id = 21598
        article = parse.instantiate_article(article_id)
        fake_get_article_type.return_value = '99999'
        return_value = parse.set_article_type(article, article_id)
        self.assertFalse(return_value)
        self.assertEqual(article.article_type, 'research-article')  # object default value
        self.assertEqual(article.display_channel, None)


    def test_set_license(self):
        article = parse.instantiate_article('12')
        return_value = parse.set_license(article, '12')
        self.assertTrue(return_value)
        self.assertIsNotNone(article.license, 'did not create a license')
        self.assertEqual(article.license.license_id, '1')
        self.assertEqual(article.license.license_type, 'open-access')
        self.assertEqual(article.license.copyright, True)
        self.assertEqual(article.license.href, 'http://creativecommons.org/licenses/by/4.0/')
        self.assertEqual(article.license.name, 'Creative Commons Attribution License')
        self.assertEqual(article.license.paragraph1, 'This article is distributed under the terms of the ')
        self.assertEqual(article.license.paragraph2, ' permitting unrestricted use and redistribution provided that the original author and source are credited.')
        # test license_id 2
        article = parse.instantiate_article('2935')
        return_value = parse.set_license(article, '2935')
        self.assertTrue(return_value)
        self.assertIsNotNone(article.license, 'did not create a license')
        self.assertEqual(article.license.license_id, '2')
        self.assertEqual(article.license.license_type, 'open-access')
        self.assertEqual(article.license.copyright, False)
        self.assertEqual(article.license.href, 'http://creativecommons.org/publicdomain/zero/1.0/')
        self.assertEqual(article.license.name, 'Creative Commons CC0')
        self.assertEqual(article.license.paragraph1, 'This is an open-access article, free of all copyright, and may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose. The work is made available under the ')
        self.assertEqual(article.license.paragraph2, ' public domain dedication.')
        # test not finding a value
        article = Article()
        return_value = parse.set_license(article, '99999')
        self.assertFalse(return_value)


    def test_set_dates(self):
        article = parse.instantiate_article('12')
        return_value = parse.set_dates(article, '12')
        self.assertTrue(return_value)
        self.assertEqual(article.get_date('received').date, generate_date("2012-05-04"))
        self.assertEqual(article.get_date('accepted').date, generate_date("2012-11-29"))
        self.assertEqual(article.get_date('license').date, generate_date("2012-11-29"))
        # test not finding a value
        article = Article()
        return_value = parse.set_dates(article, '99999')
        self.assertFalse(return_value)


    @patch('ejpcsvparser.csv_data.get_received_date')
    def test_set_dates_no_received_date(self, fake_get_received_date):
        fake_get_received_date.return_value = ' '
        article = parse.instantiate_article('12')
        return_value = parse.set_dates(article, '12')
        self.assertTrue(return_value)
        self.assertEqual(article.get_date('received').date, generate_date("2012-05-28"))


    def test_set_ethics(self):
        article = parse.instantiate_article('12')
        return_value = parse.set_ethics(article, '12')
        self.assertTrue(return_value)
        self.assertEqual(article.ethics, [u'Animal experimentation: All surgical procedures and experiments were conducted according to the German federal animal welfare guidelines and were approved by the animal ethics committee responsible for T\xfcbingen, Germany (Regierungspraesidium T\xfcbingen) under protocol numbers 3/07 and 5/09. Animals were deeply anaesthetized with Urethane (1.6-2 mg/kg), with the depth of anesthesia maintained throughout the course of the experiment with supplementary doses as required. Every attempt was made to ensure minimum discomfort to the animals at all times.'])
        # test not finding a value, currently still returns True
        article = Article()
        return_value = parse.set_ethics(article, '99999')
        self.assertTrue(return_value)
        self.assertEqual(article.ethics, [])


    @patch('ejpcsvparser.csv_data.get_ethics')
    def test_set_ethics_bad_data(self, fake_get_ethics):
        "test bad ethics data that cannot be parsed"
        fake_get_ethics.return_value = 'LTLTbad_ethicsGTGTLTLT</omg>GTGT'
        article = parse.instantiate_article('12')
        return_value = parse.set_ethics(article, '12')
        self.assertFalse(return_value)
        self.assertEqual(article.ethics, [])


    def test_set_datasets(self):
        article = parse.instantiate_article('14997')
        return_value = parse.set_datasets(article, '14997')
        self.assertTrue(return_value)
        self.assertEqual(len(article.datasets), 2)

        # check dataset 1
        self.assertEqual(article.datasets[0].dataset_type, 'datasets')
        self.assertEqual(article.datasets[0].authors, ['Cembrowski M', 'Spruston N'])
        self.assertEqual(
            article.datasets[0].source_id,
            'http://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?token=adsveykeprejbej&acc=GSE74985')
        self.assertEqual(article.datasets[0].year, '2016')
        self.assertEqual(
            article.datasets[0].title,
            'Hipposeq: an RNA-seq based atlas of gene expression in excitatory hippocampal neurons')
        self.assertEqual(article.datasets[0].license_info, 'GSE74985')
        # check dataset 2
        self.assertEqual(article.datasets[1].dataset_type, 'prev_published_datasets')
        self.assertEqual(article.datasets[1].authors, ['Cembrowski M', 'Spruston N'])
        self.assertEqual(article.datasets[1].source_id, 'http://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE67403')
        self.assertEqual(article.datasets[1].year, '2016')
        self.assertEqual(article.datasets[1].title, 'Spatial gene expression gradients underlie prominent heterogeneity of CA1 pyramidal neurons')
        self.assertEqual(article.datasets[1].license_info, 'GSE67403')
        # check data availability
        self.assertEqual(article.data_availability, u'\u2022Data Availability text <italic>"here"</italic> & such')

        # test not finding a value, currently still returns True
        article = Article()
        return_value = parse.set_datasets(article, '99999')
        self.assertTrue(return_value)
        self.assertEqual(article.datasets, [])
        self.assertEqual(article.data_availability, None)


    @patch('ejpcsvparser.csv_data.get_datasets')
    def test_set_datasets_bad_data(self, fake_get_datasets):
        "test bad ethics data that cannot be parsed"
        fake_get_datasets.return_value = 'LTLTbad_datasetsGTGTLTLT</omg>GTGT'
        article = parse.instantiate_article('12')
        return_value = parse.set_datasets(article, '12')
        self.assertFalse(return_value)
        self.assertEqual(article.datasets, [])


    def test_set_categories(self):
        article = parse.instantiate_article('12')
        return_value = parse.set_categories(article, '12')
        self.assertTrue(return_value)
        self.assertEqual(article.article_categories, ['Neuroscience'])
        # test not finding a value, currently still returns True
        article = Article()
        return_value = parse.set_categories(article, '99999')
        self.assertTrue(return_value)


    @patch('ejpcsvparser.csv_data.get_subjects')
    def test_set_categories_bad_data(self, fake_get_subjects):
        fake_get_subjects.return_value = None
        article = parse.instantiate_article('12')
        return_value = parse.set_categories(article, '12')
        self.assertFalse(return_value)


    def test_set_organsims(self):
        article = parse.instantiate_article('12')
        return_value = parse.set_organsims(article, '12')
        self.assertTrue(return_value)
        self.assertEqual(article.research_organisms, ['Rat'])
        # test not finding a value, currently still returns True
        article = Article()
        return_value = parse.set_organsims(article, '99999')
        self.assertTrue(return_value)


    @patch('ejpcsvparser.csv_data.get_organisms')
    def test_set_organisms_bad_data(self, fake_get_organisms):
        fake_get_organisms.return_value = None
        article = parse.instantiate_article('12')
        return_value = parse.set_organsims(article, '12')
        self.assertFalse(return_value)


    def test_set_keywords(self):
        article = parse.instantiate_article('12')
        return_value = parse.set_keywords(article, '12')
        self.assertTrue(return_value)
        self.assertEqual(
            article.author_keywords,
            ['circuits', 'in vivo', 'spiking patterns',
             'STDP', 'synaptic plasticity', 'visual cortex'])
        # test not finding a value, currently still returns True
        article = Article()
        return_value = parse.set_keywords(article, '99999')
        self.assertTrue(return_value)


    @patch('ejpcsvparser.csv_data.get_keywords')
    def test_set_keywords_bad_data(self, fake_get_keywords):
        fake_get_keywords.return_value = None
        article = parse.instantiate_article('12')
        return_value = parse.set_keywords(article, '12')
        self.assertFalse(return_value)


    def test_set_author_info(self):
        "test settings some authors"
        # article 7 has an author with a competing interest
        article = parse.instantiate_article('7')
        return_value = parse.set_author_info(article, '7')
        self.assertTrue(return_value)
        self.assertEqual(len(article.contributors), 3)
        # article 7 contributor 3
        contrib = article.contributors[2]
        self.assertEqual(contrib.contrib_type, 'author')
        self.assertEqual(contrib.surname, 'Baldwin')
        self.assertEqual(contrib.given_name, 'Ian T')
        self.assertEqual(contrib.corresp, True)
        self.assertEqual(contrib.equal_contrib, False)
        self.assertEqual(contrib.auth_id, '1013')
        self.assertEqual(contrib.orcid, None)
        self.assertEqual(contrib.suffix, None)
        self.assertEqual(contrib.collab, None)
        self.assertEqual(contrib.conflict, ['Senior Editor, eLife'])
        self.assertEqual(contrib.group_author_key, None)
        aff = article.contributors[2].affiliations[0]
        self.assertEqual(aff.phone, None)
        self.assertEqual(aff.fax, None)
        self.assertEqual(aff.department, 'Department of Molecular Ecology')
        self.assertEqual(aff.institution, 'Max Planck Institute for Chemical Ecology')
        self.assertEqual(aff.city, 'Jena')
        self.assertEqual(aff.country, 'Germany')
        self.assertEqual(aff.text, None)

        # article 2935 has some group authors
        article = parse.instantiate_article('2935')
        return_value = parse.set_author_info(article, '2935')
        self.assertTrue(return_value)
        self.assertEqual(len(article.contributors), 53)
        # article 2935 contributor 34 is a group author
        contrib = article.contributors[33]
        self.assertEqual(contrib.contrib_type, 'author')
        self.assertEqual(contrib.surname, None)
        self.assertEqual(contrib.given_name, None)
        self.assertEqual(contrib.collab, 'ICGC Breast Cancer Group')

        # test not finding a value
        article = Article()
        return_value = parse.set_author_info(article, '99999')
        self.assertFalse(return_value)


    @patch('ejpcsvparser.csv_data.get_author_ids')
    def test_set_author_info_bad_data(self, fake_get_author_ids):
        fake_get_author_ids.return_value = None
        article = parse.instantiate_article('12')
        return_value = parse.set_author_info(article, '12')
        self.assertFalse(return_value)


    def test_set_editor_info(self):
        article = parse.instantiate_article('12717')
        return_value = parse.set_editor_info(article, '12717')
        self.assertTrue(return_value)
        self.assertEqual(len(article.contributors), 1)
        self.assertEqual(len([contrib for contrib in article.contributors
                              if contrib.contrib_type == 'editor']), 1)
        editor = article.contributors[0]
        self.assertEqual(editor.contrib_type, 'editor')
        self.assertEqual(editor.surname, 'Cooper')
        self.assertEqual(editor.given_name, 'Jonathan A')
        aff = article.contributors[0].affiliations[0]
        self.assertEqual(aff.department, 'Division of Basic Sciences')
        self.assertEqual(aff.institution, 'Fred Hutchinson Cancer Research Center')
        self.assertEqual(aff.country, 'United States')


    @patch('ejpcsvparser.csv_data.get_me_first_nm')
    def test_set_editor_info_bad_data(self, fake_get_me_first_nm):
        fake_get_me_first_nm.return_value = None
        article = parse.instantiate_article('12')
        return_value = parse.set_editor_info(article, '12')
        self.assertFalse(return_value)


    def test_set_funding(self):
        article = parse.instantiate_article('12717')
        # set the authors in order to populate teh principal_award_recipients correctly
        parse.set_author_info(article, '12717')
        return_value = parse.set_funding(article, '12717')
        self.assertTrue(return_value)
        self.assertEqual(len(article.funding_awards), 2)
        award = article.funding_awards[0]
        self.assertEqual(award.award_group_id, None)
        self.assertEqual(award.award_ids, ['1R01NS066936'])
        self.assertEqual(award.institution_name,
                         'National Institute of Neurological Disorders and Stroke')
        self.assertEqual(award.institution_id, '100000065')
        self.assertEqual(len(award.principal_award_recipients), 1)
        self.assertEqual(award.principal_award_recipients[0].surname, 'Solecki')
        self.assertEqual(award.principal_award_recipients[0].given_name, 'David J')


    @patch('ejpcsvparser.csv_data.get_funding_ids')
    def test_set_funding_bad_data(self, fake_get_funding_ids):
        fake_get_funding_ids.return_value = None
        article = parse.instantiate_article('12')
        return_value = parse.set_funding(article, '12')
        self.assertFalse(return_value)


    def test_parse_ethics(self):
        "test examples of parsing ethics data"
        ethic = "LTLTxmlGTGTLTLTanimal_subjectsGTGTLTLTinvolved_indGTGT0LTLT/involved_indGTGTLTLT/animal_subjectsGTGTLTLThuman_subjectsGTGTLTLTclinical_trial_indGTGT0LTLT/clinical_trial_indGTGTLTLTinvolved_commentsGTGTWe obtained informed consent and consent to publish from participants enrolled in this study.Ethical approval references:Genome Analysis of myeloid and lymphoid malignancies (10/H0306/40)Genomic Analysis of Mesothelioma (11/EE/0444)Myeloid and lymphoid cancer genome analysis (07/S1402/90)The Treatment of Down Syndrome Children with Acute Myeloid Leukemia and Myelodysplastic Syndrome(AAML0431)CLL (chronic lymphocytic leukaemia) genome analysis (07/Q0104/3)CGP-Exome sequencing of Down syndrome associated acute myeloid leukemia samples (IRB 13-010133)Cancer Genome Project - Global approaches to characterising the molecular basis of paediatric ependymoma (05/MRE04/70)PREDICT-Cohort (09/H0801/96)ICGC Prostate (Evaluation of biomarkers in urological diseases) (LREC 03/018)ICGC Prostate (779) (Prostate Complex CRUK Sample Cohort) (MREC/01/4/061)ICGC Prostate (Tissue collection at radical prostatectomy) (CRE-2011.373)Somatic molecular genetics of human cancers, melanoma and myeloma (Dana Farber Cancer Institute)(08/H0308/303)Breast Cancer Genome Analysis for the International Cancer Genome Consortium Working Group (09/H0306/36)Genome analysis of tumours of the bone (09/H0308/165)LTLT/involved_commentsGTGTLTLTinvolved_indGTGT1LTLT/involved_indGTGTLTLT/human_subjectsGTGTLTLT/xmlGTGT"
        ethics = parse.parse_ethics(ethic)
        self.assertEqual(ethics[0], 'Human subjects: We obtained informed consent and consent to publish from participants enrolled in this study.Ethical approval references:Genome Analysis of myeloid and lymphoid malignancies (10/H0306/40)Genomic Analysis of Mesothelioma (11/EE/0444)Myeloid and lymphoid cancer genome analysis (07/S1402/90)The Treatment of Down Syndrome Children with Acute Myeloid Leukemia and Myelodysplastic Syndrome(AAML0431)CLL (chronic lymphocytic leukaemia) genome analysis (07/Q0104/3)CGP-Exome sequencing of Down syndrome associated acute myeloid leukemia samples (IRB 13-010133)Cancer Genome Project - Global approaches to characterising the molecular basis of paediatric ependymoma (05/MRE04/70)PREDICT-Cohort (09/H0801/96)ICGC Prostate (Evaluation of biomarkers in urological diseases) (LREC 03/018)ICGC Prostate (779) (Prostate Complex CRUK Sample Cohort) (MREC/01/4/061)ICGC Prostate (Tissue collection at radical prostatectomy) (CRE-2011.373)Somatic molecular genetics of human cancers, melanoma and myeloma (Dana Farber Cancer Institute)(08/H0308/303)Breast Cancer Genome Analysis for the International Cancer Genome Consortium Working Group (09/H0306/36)Genome analysis of tumours of the bone (09/H0308/165)')


    def test_parse_group_authors(self):
        "test group author edge cases"
        group_author_dict = parse.parse_group_authors(None)
        self.assertIsNone(group_author_dict)
        group_author_dict = parse.parse_group_authors('')
        self.assertIsNone(group_author_dict)
        group_author_dict = parse.parse_group_authors('0')
        self.assertIsNone(group_author_dict)


    def test_build_article_and_check(self):
        "build one article and check some values"
        article_id = 21598
        article, error_count, error_messages = parse.build_article(article_id)
        self.assertEqual(article.title, 'Cryo-EM structures of the autoinhibited <italic>E. coli</italic> ATP synthase in three rotational states')


if __name__ == '__main__':
    unittest.main()
