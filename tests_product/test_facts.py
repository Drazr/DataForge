import pytest

from product.core import Appointment
from product.facts import matches_fact, reference_value, time_value


@pytest.mark.parametrize('spoken', [
    'DF 4821', 'D F 4 8 2 1', 'The reference code is D F four eight two one',
    'delta foxtrot four eight two one',
])
def test_reference_equivalents_match(spoken):
    assert matches_fact('reference', spoken, Appointment())


@pytest.mark.parametrize('spoken', [
    'DF 4822', 'DF 4821 please confirm', '4821', '', 'reference code is probably DF 4821',
])
def test_reference_rejects_wrong_partial_or_extra_content(spoken):
    assert not matches_fact('reference', spoken, Appointment())


@pytest.mark.parametrize('spoken', [
    '9:20 AM', '9.20 a.m.', 'nine twenty am', 'The appointment time is nine twenty A M',
])
def test_time_equivalents_match(spoken):
    assert matches_fact('time', spoken, Appointment())


@pytest.mark.parametrize('spoken', ['9:20 PM', '9:28 AM', 'nine AM', 'around 9:20 AM', ''])
def test_time_rejects_wrong_or_qualified_content(spoken):
    assert not matches_fact('time', spoken, Appointment())


def test_unknown_fact_has_no_parser():
    assert not matches_fact('location', 'Riverside Community Studio', Appointment())
    assert reference_value('reference code is') is None
    assert time_value('twenty past nine') is None
