from app import app

def test_home():
    tester = app.test_client()
    response = tester.get('/')
    assert response.status_code == 200
    assert b"Bienvenido" in response.data

def test_analisis_correcto():
    tester = app.test_client()
    response = tester.post('/analisis', json={"valores": [1, 2, 3, 4]})
    assert response.status_code == 200
    data = response.get_json()
    assert data["suma"] == 10
    assert data["promedio"] == 2.5

def test_analisis_error():
    tester = app.test_client()
    response = tester.post('/analisis', json={})
    assert response.status_code == 400
