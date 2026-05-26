import uuid


def _create_poll(client, auth_header, title='Favorite color', status='active'):
    response = client.post('/polls', headers=auth_header, json={
        'title': title,
        'description': 'pick one',
        'status': status
    })
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()


def _add_option(client, auth_header, poll_id, text, order=1):
    response = client.post(
        f'/polls/{poll_id}/options',
        headers=auth_header,
        json={'option_text': text, 'display_order': order}
    )
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()


def test_polls_get_public(client):
    response = client.get('/polls')
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_polls_post_ok(client, auth_header_a):
    response = client.post('/polls', headers=auth_header_a, json={
        'title': 'Best food', 'description': 'choose', 'status': 'active'
    })
    assert response.status_code == 201
    body = response.get_json()
    assert body['title'] == 'Best food'
    assert body['status'] == 'active'


def test_polls_post_requires_auth(client):
    response = client.post('/polls', json={'title': 'x'})
    assert response.status_code == 401


def test_polls_post_no_title_400(client, auth_header_a):
    response = client.post('/polls', headers=auth_header_a, json={'description': 'x'})
    assert response.status_code == 400


def test_polls_post_bad_status_400(client, auth_header_a):
    response = client.post('/polls', headers=auth_header_a, json={
        'title': 'x', 'status': 'invalid-status'
    })
    assert response.status_code == 400


def test_polls_post_title_too_long_400(client, auth_header_a):
    response = client.post('/polls', headers=auth_header_a, json={'title': 'x' * 121})
    assert response.status_code == 400


def test_polls_show_get_ok(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    response = client.get(f"/polls/{poll['id']}")
    assert response.status_code == 200
    assert response.get_json()['id'] == poll['id']


def test_polls_show_get_404(client):
    response = client.get(f'/polls/{uuid.uuid4()}')
    assert response.status_code == 404


def test_polls_patch_ok(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    response = client.patch(
        f"/polls/{poll['id']}", headers=auth_header_a,
        json={'title': 'Updated title', 'status': 'closed'}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body['title'] == 'Updated title'
    assert body['status'] == 'closed'


def test_polls_patch_not_owner_403(client, auth_header_a, auth_header_b):
    poll = _create_poll(client, auth_header_a)
    response = client.patch(
        f"/polls/{poll['id']}", headers=auth_header_b,
        json={'title': 'hijacked'}
    )
    assert response.status_code == 403


def test_polls_patch_404(client, auth_header_a):
    response = client.patch(
        f"/polls/{uuid.uuid4()}", headers=auth_header_a, json={'title': 'x'}
    )
    assert response.status_code == 404


def test_polls_delete_ok(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    response = client.delete(f"/polls/{poll['id']}", headers=auth_header_a)
    assert response.status_code == 204
    assert client.get(f"/polls/{poll['id']}").status_code == 404


def test_polls_delete_not_owner_403(client, auth_header_a, auth_header_b):
    poll = _create_poll(client, auth_header_a)
    response = client.delete(f"/polls/{poll['id']}", headers=auth_header_b)
    assert response.status_code == 403


def test_polls_options_get_ok(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    _add_option(client, auth_header_a, poll['id'], 'red', order=1)
    _add_option(client, auth_header_a, poll['id'], 'blue', order=2)
    response = client.get(f"/polls/{poll['id']}/options")
    assert response.status_code == 200
    options = response.get_json()
    assert [o['option_text'] for o in options] == ['red', 'blue']


def test_polls_options_get_404(client):
    response = client.get(f"/polls/{uuid.uuid4()}/options")
    assert response.status_code == 404


def test_polls_options_post_ok(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    response = client.post(
        f"/polls/{poll['id']}/options", headers=auth_header_a,
        json={'option_text': 'green', 'display_order': 3}
    )
    assert response.status_code == 201
    assert response.get_json()['option_text'] == 'green'


def test_polls_options_post_not_owner_403(client, auth_header_a, auth_header_b):
    poll = _create_poll(client, auth_header_a)
    response = client.post(
        f"/polls/{poll['id']}/options", headers=auth_header_b,
        json={'option_text': 'green'}
    )
    assert response.status_code == 403


def test_polls_options_post_text_too_long_400(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    response = client.post(
        f"/polls/{poll['id']}/options", headers=auth_header_a,
        json={'option_text': 'x' * 101}
    )
    assert response.status_code == 400


def test_polls_votes_get_ok(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    option = _add_option(client, auth_header_a, poll['id'], 'red')
    client.post(
        f"/polls/{poll['id']}/votes", headers=auth_header_a,
        json={'option_id': option['id']}
    )
    response = client.get(f"/polls/{poll['id']}/votes", headers=auth_header_a)
    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_polls_votes_get_requires_auth(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    response = client.get(f"/polls/{poll['id']}/votes")
    assert response.status_code == 401


def test_polls_votes_post_ok(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    option = _add_option(client, auth_header_a, poll['id'], 'red')
    response = client.post(
        f"/polls/{poll['id']}/votes", headers=auth_header_a,
        json={'option_id': option['id']}
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body['option_id'] == option['id']


def test_polls_votes_post_duplicate_409(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    option = _add_option(client, auth_header_a, poll['id'], 'red')
    first = client.post(
        f"/polls/{poll['id']}/votes", headers=auth_header_a,
        json={'option_id': option['id']}
    )
    assert first.status_code == 201
    second = client.post(
        f"/polls/{poll['id']}/votes", headers=auth_header_a,
        json={'option_id': option['id']}
    )
    assert second.status_code == 409


def test_polls_votes_post_option_wrong_poll_404(client, auth_header_a):
    poll_a = _create_poll(client, auth_header_a, title='A')
    poll_b = _create_poll(client, auth_header_a, title='B')
    option_b = _add_option(client, auth_header_a, poll_b['id'], 'green')
    response = client.post(
        f"/polls/{poll_a['id']}/votes", headers=auth_header_a,
        json={'option_id': option_b['id']}
    )
    assert response.status_code == 404


def test_polls_votes_post_bad_option_uuid_400(client, auth_header_a):
    poll = _create_poll(client, auth_header_a)
    response = client.post(
        f"/polls/{poll['id']}/votes", headers=auth_header_a,
        json={'option_id': 'not-a-uuid'}
    )
    assert response.status_code == 400


def test_polls_results_ok(client, auth_header_a, auth_header_b):
    poll = _create_poll(client, auth_header_a)
    red = _add_option(client, auth_header_a, poll['id'], 'red', order=1)
    blue = _add_option(client, auth_header_a, poll['id'], 'blue', order=2)
    client.post(f"/polls/{poll['id']}/votes", headers=auth_header_a, json={'option_id': red['id']})
    client.post(f"/polls/{poll['id']}/votes", headers=auth_header_b, json={'option_id': red['id']})

    response = client.get(f"/polls/{poll['id']}/results")
    assert response.status_code == 200
    body = response.get_json()
    assert body['poll']['id'] == poll['id']
    tallies = {o['option']['option_text']: o['votes'] for o in body['options']}
    assert tallies == {'red': 2, 'blue': 0}


def test_polls_results_404(client):
    response = client.get(f"/polls/{uuid.uuid4()}/results")
    assert response.status_code == 404
