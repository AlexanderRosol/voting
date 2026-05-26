import uuid


def test_users_get_requires_auth(client):
    response = client.get('/users')
    assert response.status_code == 401


def test_users_get_ok(client, auth_header_a, user_a):
    response = client.get('/users', headers=auth_header_a)
    assert response.status_code == 200
    body = response.get_json()
    assert isinstance(body, list)
    usernames = [u['username'] for u in body]
    assert 'alice' in usernames


def test_users_post_ok(client):
    response = client.post('/users', json={
        'username': 'carol',
        'email': 'carol@example.com',
        'password': 'carolpw1'
    })
    assert response.status_code == 201
    body = response.get_json()
    assert body['username'] == 'carol'
    assert body['email'] == 'carol@example.com'
    assert 'password' not in body
    uuid.UUID(body['id'])


def test_users_post_missing_password(client):
    response = client.post('/users', json={
        'username': 'carol',
        'email': 'carol@example.com'
    })
    assert response.status_code == 400


def test_users_post_bad_email(client):
    response = client.post('/users', json={
        'username': 'carol',
        'email': 'not-an-email',
        'password': 'carolpw1'
    })
    assert response.status_code == 400


def test_users_post_username_too_long(client):
    response = client.post('/users', json={
        'username': 'x' * 31,
        'email': 'x@example.com',
        'password': 'xpassword'
    })
    assert response.status_code == 400


def test_users_post_duplicate_username(client, user_a):
    response = client.post('/users', json={
        'username': user_a['username'],
        'email': 'different@example.com',
        'password': 'whateverpw'
    })
    assert response.status_code == 400


def test_users_show_get_requires_auth(client, user_a):
    response = client.get(f"/users/{user_a['id']}")
    assert response.status_code == 401


def test_users_show_get_ok(client, auth_header_a, user_a):
    response = client.get(f"/users/{user_a['id']}", headers=auth_header_a)
    assert response.status_code == 200
    assert response.get_json()['username'] == 'alice'


def test_users_show_get_404(client, auth_header_a):
    response = client.get(f"/users/{uuid.uuid4()}", headers=auth_header_a)
    assert response.status_code == 404


def test_users_put_ok(client, auth_header_a, user_a):
    response = client.put(
        f"/users/{user_a['id']}",
        headers=auth_header_a,
        json={'username': 'alice2', 'email': 'alice2@example.com'}
    )
    assert response.status_code == 200
    assert response.get_json()['username'] == 'alice2'


def test_users_put_not_owner_403(client, auth_header_b, user_a):
    response = client.put(
        f"/users/{user_a['id']}",
        headers=auth_header_b,
        json={'username': 'hacked', 'email': 'hacked@example.com'}
    )
    assert response.status_code == 403


def test_users_put_404(client, auth_header_a):
    response = client.put(
        f"/users/{uuid.uuid4()}",
        headers=auth_header_a,
        json={'username': 'x', 'email': 'x@example.com'}
    )
    assert response.status_code == 404


def test_users_delete_ok(client, auth_header_a, user_a):
    response = client.delete(f"/users/{user_a['id']}", headers=auth_header_a)
    assert response.status_code == 204


def test_users_delete_not_owner_403(client, auth_header_b, user_a):
    response = client.delete(f"/users/{user_a['id']}", headers=auth_header_b)
    assert response.status_code == 403


def test_users_delete_404(client, auth_header_a):
    response = client.delete(f"/users/{uuid.uuid4()}", headers=auth_header_a)
    assert response.status_code == 404
