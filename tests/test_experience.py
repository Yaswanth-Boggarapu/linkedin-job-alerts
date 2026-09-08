import experience


def rank(title, description=None):
    return experience.classify({"title": title, "description": description})


def test_graduate_beats_the_role_noun():
    assert rank("Graduate Data Scientist")[1] == "Graduate/Intern"


def test_intern_and_placement_are_most_junior():
    assert rank("Data Analyst Intern")[0] == 0
    assert rank("Data Science Placement")[0] == 0


def test_senior_titles_rank_last():
    assert rank("Senior Data Engineer")[0] == 5
    assert rank("Lead Data Scientist")[0] == 5


def test_ai_engineer_is_not_junior():
    """Substring matching used to read the 'i ' in 'AI Engineer' as junior."""
    assert rank("AI Engineer")[1] == "Not stated"


def test_roman_numeral_two_is_mid():
    assert rank("Software Engineer II")[1] == "Mid"


def test_years_of_experience_from_description():
    assert rank("Data Scientist", "You need 5+ years of experience.")[0] == 5
    assert rank("Data Scientist", "Ideal with 1 year of experience.")[0] == 0


def test_years_ignored_when_not_about_experience():
    assert rank("Data Scientist", "We have been trading 20 years.")[1] == "Not stated"


def test_unknown_sorts_last():
    assert rank("Data Scientist")[0] == 9
