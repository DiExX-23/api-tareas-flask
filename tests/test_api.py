# 👇 Configura el path para importar desde la raíz del proyecto
import sys
import os
import json
import pytest

# Asegura que 'app.py' se pueda importar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 👇 Importa la app y los modelos desde app.py
from app import app, db, Usuario, Tarea

# 🔄 Configura la base de datos de pruebas
@pytest.fixture
def cliente():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # DB temporal
    with app.app_context():
        db.create_all()
    yield app.test_client()
    with app.app_context():
        db.drop_all()

# 🔐 Test: Registro de un nuevo usuario
def test_registro_usuario(cliente):
    respuesta = cliente.post("/register", json={
        "username": "prueba",
        "password": "123456"
    })
    assert respuesta.status_code == 201
    assert respuesta.get_json()["mensaje"] == "Usuario registrado"

# 🔐 Test: Login y obtención de token
def test_login(cliente):
    # Crear usuario primero
    cliente.post("/register", json={
        "username": "test",
        "password": "123"
    })
    respuesta = cliente.post("/login", json={
        "username": "test",
        "password": "123"
    })
    datos = respuesta.get_json()
    assert "access_token" in datos
    assert respuesta.status_code == 200

# ✅ Test: Crear tarea usando JWT
def test_crear_tarea(cliente):
    # Registro y login para obtener token
    cliente.post("/register", json={"username": "user1", "password": "pass"})
    login = cliente.post("/login", json={"username": "user1", "password": "pass"})
    token = login.get_json()["access_token"]

    # Crear tarea autenticado
    headers = {"Authorization": f"Bearer {token}"}
    tarea = {"titulo": "Aprender Flask"}
    respuesta = cliente.post("/tareas", json=tarea, headers=headers)

    assert respuesta.status_code == 201
    assert respuesta.get_json()["titulo"] == "Aprender Flask"

# 📋 Test: Obtener lista de tareas
def test_obtener_tareas(cliente):
    # Registro y login
    cliente.post("/register", json={"username": "user2", "password": "pass"})
    login = cliente.post("/login", json={"username": "user2", "password": "pass"})
    token = login.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Crear tarea
    cliente.post("/tareas", json={"titulo": "Leer documentación"}, headers=headers)

    # Obtener tareas
    respuesta = cliente.get("/tareas", headers=headers)
    assert respuesta.status_code == 200
    assert isinstance(respuesta.get_json(), list)

# 📝 Test: Actualizar una tarea
def test_actualizar_tarea(cliente):
    cliente.post("/register", json={"username": "user3", "password": "pass"})
    login = cliente.post("/login", json={"username": "user3", "password": "pass"})
    token = login.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Crear una tarea
    cliente.post("/tareas", json={"titulo": "Tarea antigua"}, headers=headers)

    # Actualizar la tarea
    nueva_data = {"titulo": "Tarea actualizada", "completado": True}
    respuesta = cliente.put("/tareas/1", json=nueva_data, headers=headers)

    assert respuesta.status_code == 200
    assert respuesta.get_json()["titulo"] == "Tarea actualizada"
    assert respuesta.get_json()["completado"] is True

# 🗑️ Test: Eliminar una tarea
def test_eliminar_tarea(cliente):
    cliente.post("/register", json={"username": "user4", "password": "pass"})
    login = cliente.post("/login", json={"username": "user4", "password": "pass"})
    token = login.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Crear una tarea
    cliente.post("/tareas", json={"titulo": "Tarea para eliminar"}, headers=headers)

    # Eliminar la tarea
    respuesta = cliente.delete("/tareas/1", headers=headers)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["mensaje"] == "Tarea eliminada correctamente"
