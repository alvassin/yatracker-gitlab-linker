import pytest

from yatracker_linker.views.events import get_ticket_candidates


def test_get_no_candidates():
    assert get_ticket_candidates('bla bla bla') == []


@pytest.mark.parametrize('branch_name,expected_results', [
    ('TICKET-1', ['TICKET-1']),
    ('ticket-1', ['TICKET-1']),

    # Multiple MR (and branches) for one issue
    ('ticket-1-1', ['TICKET-1']),
    ('branch-name-ticket-1-1', ['TICKET-1']),
])
def test_get_ticket_candidates_from_branch_name(branch_name, expected_results):
    assert get_ticket_candidates(branch_name) == expected_results


def test_get_ticket_candidates_from_description():
    x = 'Some job: TICKET-1\nAnother job: ticket-2'
    assert get_ticket_candidates(x) == ['TICKET-1', 'TICKET-2']
