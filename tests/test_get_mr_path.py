from yatracker_gitlab_linker.views.event import get_mr_url_path


def test_get_mr_path():
    assert get_mr_url_path(
        'https://gitlab.net/alvassin/example/-/merge_requests/1',
        'alvassin/example'
    ) == 'alvassin/example/-/merge_requests/1'
