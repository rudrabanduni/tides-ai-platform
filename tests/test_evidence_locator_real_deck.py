"""Evidence locator on SYNTHETIC text that reproduces artefacts seen in a real deck (live pilot, 2026-11-23).

Real PDF extraction runs words together ("48,300SAM", "LaunchedJUN"), writes "60 percent" where the model
writes "60%", and letter-spaces headings. The locator must still cite these passages, while refusing
passages with different numbers and never linking model inferences the deck does not contain.
"""

from app.modules.intelligence.evidence_locator import locate_passage

DECK = "\n".join([
    "[Page 7]",
    "MARKETSTAM = T otal No. of Partner Clinics*SAM = 60 percent of TAM SOM = 50 percent of SAM",
    "TAM ? For Partner Clinics ? 48,300SAM ? For Partner Clinics ? 28,980SOM for Partner Clinics-14,490",
    "[Page 10]",
    "MILESTONES",
    "Selected for INNOVATE 3.02ndPrototype LaunchedJUN 2024MOU with ACME Hospital for field T esting in 2 year Duration. AUG 2024",
    "[Page 3]",
    "PROBLEM",
    "GEOGRAPHICALLY SKEWED DISTRIBUTION OF TECHNICAL EXPERTISE",
    "INADEQUATELY TRAINED OPERATORS AT RURAL SITES",
])


def test_run_together_numbers_and_percentages_are_located_on_the_right_page():
    passage, page = locate_passage(DECK, "SAM: 28,980 partner clinics (60% of TAM)")
    assert passage and page == 7
    assert "28,980" in passage


def test_run_together_words_are_located():
    passage, page = locate_passage(DECK, "Prototype Launched (Jun 2024)")
    assert passage and page == 10


def test_statement_split_across_lines_is_located():
    passage, page = locate_passage(DECK, "Geographically skewed technical expertise; inadequately trained rural operators")
    assert passage and page == 3


def test_a_different_number_is_never_cited():
    assert locate_passage(DECK, "SAM: 25,000 partner clinics") == (None, None)


def test_inferred_structured_items_do_not_borrow_nearby_passages():
    sdg = [{"sdg_number": 3, "sdg_name": "Good Health and Well-being",
            "explanation": "Addresses skewed technical expertise distribution and untrained rural operators"}]
    assert locate_passage(DECK, sdg) == (None, None)


def test_structured_items_are_located_by_their_identity_field():
    pilots = [{"partner_name": "ACME Hospital", "agreement_type": "MoU", "explanation": "unrelated model text"}]
    passage, page = locate_passage(DECK, pilots)
    assert passage and page == 10
