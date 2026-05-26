def test_auth_token_success(client, user_a):
    response = client.post('/auth/token', json={
        'username': user_a['username'],
        'password': user_a['password']
    })
    assert response.status_code == 200
    body = response.get_json()
    assert 'access_token' in body
    assert body['token_type'] == 'bearer'


def test_auth_token_bad_password(client, user_a):
    response = client.post('/auth/token', json={
        'username': user_a['username'],
        'password': 'wrong-password'
    })
    assert response.status_code == 400
    assert response.get_json()['code'] == 400


def test_auth_token_unknown_user(client):
    response = client.post('/auth/token', json={
        'username': 'ghost',
        'password': 'whatever'
    })
    assert response.status_code == 400


def test_auth_token_missing_fields(client):
    response = client.post('/auth/token', json={'username': 'alice'})
    assert response.status_code == 400


def test_auth_token_malformed_json(client):
    response = client.post('/auth/token', data='not-json', content_type='application/json')
    assert response.status_code == 400
