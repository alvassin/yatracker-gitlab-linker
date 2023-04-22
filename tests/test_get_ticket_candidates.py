from yatracker_linker.views.event import get_ticket_candidates


def test_get_no_candidates():
    assert get_ticket_candidates('bla bla bla') == []


def test_get_ticket_candidates_from_branch_name():
    assert get_ticket_candidates('TICKET-1') == ['TICKET-1']
    assert get_ticket_candidates('ticket-1') == ['TICKET-1']

    # Sometimes we want to make multiple MR for one ticket
    assert get_ticket_candidates('ticket-1-1') == ['TICKET-1']


def test_get_ticket_candidates_from_description():
    x = 'Some job: TICKET-1\nAnother job: ticket-2'
    assert get_ticket_candidates(x) == ['TICKET-1', 'TICKET-2']
