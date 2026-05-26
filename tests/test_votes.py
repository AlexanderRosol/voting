import uuid


def _setup_vote(client, auth_header):
    poll = client.post('/polls', headers=auth_header, json={'title': 'T'}).get_json()
    option = client.post(
        f"/polls/{poll['id']}/options", headers=auth_header,
        json={'option_text': 'opt'}
    ).get_json()
    vote = client.post(
        f"/polls/{poll['id']}/votes", headers=auth_header,
        json={'option_id': option['id']}
    ).get_json()
    return vote


def test_votes_show_get_requires_auth(client, auth_header_a):
    vote = _setup_vote(client, auth_header_a)
    response = client.get(f"/votes/{vote['id']}")
    assert response.status_code == 401


def test_votes_show_get_ok(client, auth_header_a):
    vote = _setup_vote(client, auth_header_a)
    response = client.get(f"/votes/{vote['id']}", headers=auth_header_a)
    assert response.status_code == 200
    assert response.get_json()['id'] == vote['id']


def test_votes_show_get_404(client, auth_header_a):
    response = client.get(f"/votes/{uuid.uuid4()}", headers=auth_header_a)
    assert response.status_code == 404


def test_votes_delete_ok(client, auth_header_a):
    vote = _setup_vote(client, auth_header_a)
    response = client.delete(f"/votes/{vote['id']}", headers=auth_header_a)
    assert response.status_code == 204
    assert client.get(f"/votes/{vote['id']}", headers=auth_header_a).status_code == 404


def test_votes_delete_not_owner_403(client, auth_header_a, auth_header_b):
    vote = _setup_vote(client, auth_header_a)
    response = client.delete(f"/votes/{vote['id']}", headers=auth_header_b)
    assert response.status_code == 403


def test_votes_delete_404(client, auth_header_a):
    response = client.delete(f"/votes/{uuid.uuid4()}", headers=auth_header_a)
    assert response.status_code == 404
