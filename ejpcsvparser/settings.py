# csv reading settings
ROWS_WITH_COLNAMES = 3
DATA_START_ROW = 4
LESS_THAN_ESCAPE_SEQUENCE = "LTLT"
GREATER_THAN_ESCAPE_SEQUENCE = "GTGT"

CSV_PATH = "tests/test_data/"

TMP_DIR = "tests/tmp/"

CSV_FILES = {
    "authors": "poa_author.csv",
    "license": "poa_license.csv",
    "manuscript": "poa_manuscript.csv",
    "received": "poa_received.csv",
    "subjects": "poa_subject_area.csv",
    "organisms": "poa_research_organism.csv",
    "abstract": "poa_abstract.csv",
    "title": "poa_title.csv",
    "keywords": "poa_keywords.csv",
    "group_authors": "poa_group_authors.csv",
    "datasets": "poa_datasets.csv",
    "funding": "poa_funding.csv",
    "ethics": "poa_ethics.csv",
}

# Special files that allow quotation marks in their final column: column 3
OVERFLOW_CSV_FILES = ["abstract", "title", "ethics", "datasets"]

CSV_COLUMN_HEADINGS = {
    "author_position": "poa_a_seq",
    "subject_areas": "poa_s_subjectarea",
    "license_id": "poa_l_license_id",
    "title": "poa_m_title_tag",
    "abstract": "poa_m_abstract_tag",
    "doi": "poa_m_doi",
    "article_type": "poa_m_type",
    "accepted_date": "poa_m_accepted_dt",
    "received_date": "poa_r_received_dt",
    "receipt_date": "poa_r_receipt_dt2",
    "editor_id": "poa_m_me_id",
    "editor_last_name": "poa_m_me_last_nm",
    "editor_first_name": "poa_m_me_first_nm",
    "editor_middle_name": "poa_m_me_middle_nm",
    "editor_suffix": "poa_m_me_suffix",
    "editor_institution": "poa_m_me_organization",
    "editor_department": "poa_m_me_department",
    "editor_country": "poa_m_me_country",
    "ethics": "poa_m_ethics_note",
    "author_id": "poa_a_id",
    "email": "poa_a_email",
    "author_type": "poa_a_type_cde",
    "dual_corresponding": "poa_a_dual_corr",
    "author_last_name": "poa_a_last_nm",
    "author_first_name": "poa_a_first_nm",
    "author_middle_name": "poa_a_middle_nm",
    "author_suffix": "poa_a_suffix",
    "author_institution": "poa_a_organization",
    "author_department": "poa_a_department",
    "author_city": "poa_a_city",
    "author_country": "poa_a_country",
    "author_state": "poa_a_state",
    "author_conflict": "poa_a_cmp",
    "organisms": "poa_ro_researchorganism",
    "keywords": "poa_kw_keyword",
    "group_author": "poa_ga",
    "orcid": "ORCID",
    "datasets": "poa_m_dataset_note",
    "award_id": "poa_grant_ref_no",
    "funder_position": "poa_funder_order",
    "funder": "poa_funder",
    "funder_identifier": "poa_fund_ref_id",
    "funding_note": "poa_m_funding_note",
}
