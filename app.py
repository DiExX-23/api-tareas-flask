# ------------------------
# IMPORTACIONES NECESARIAS
# ------------------------
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_restx import Api, Resource, fields
from werkzeug.security import generate_password_hash, check_password_hash
import os

# ------------------------
# INICIALIZACIÓN DE FLASK Y CONFIGURACIONES
# ------------------------
app = Flask(__name__)
api = Api(app, title="API de Tareas", version="1.0", description="API REST con JWT, SQLite y Swagger")

# Configuración de clave JWT y ruta de la base de datos SQLite
app.config['JWT_SECRET_KEY'] = 'super-secreto'  # Clave secreta para generar tokens JWT
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desactiva seguimiento de cambios (mejor rendimiento)

# ------------------------
# INICIALIZACIÓN DE EXTENSIONES
# ------------------------
jwt = JWTManager(app)
db = SQLAlchemy(app)

# ------------------------
# CREACIÓN DE TABLAS AL INICIO (IMPORTANTE PARA RENDER)
# ------------------------
with app.app_context():
    db.create_all()

# ------------------------
# MODELOS DE BASE DE DATOS
# ------------------------

# Modelo para las tareas
class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    completado = db.Column(db.Boolean, default=False)

# Modelo para los usuarios
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# ------------------------
# ESQUEMAS DE SWAGGER (FLASK-RESTX)
# ------------------------
tarea_model = api.model('Tarea', {
    'id': fields.Integer(readonly=True),
    'titulo': fields.String(required=True, description="Título de la tarea"),
    'completado': fields.Boolean(default=False, description="Estado de la tarea")
})

usuario_model = api.model('Usuario', {
    'username': fields.String(required=True, description="Nombre de usuario"),
    'password': fields.String(required=True, description="Contraseña")
})

# ------------------------
# RUTAS Y ENDPOINTS
# ------------------------

# Ruta raíz - mensaje informativo
@api.route("/")
class Inicio(Resource):
    def get(self):
        return {"mensaje": "API de Tareas con Flask, SQLite, JWT y Swagger"}

# Registro de usuario
@api.route("/register")
class Registro(Resource):
    @api.expect(usuario_model)
    def post(self):
        data = request.get_json()

        if not data or "username" not in data or "password" not in data:
            return {"error": "Faltan campos requeridos"}, 400

        if Usuario.query.filter_by(username=data["username"]).first():
            return {"error": "Usuario ya existe"}, 400

        try:
            hashed = generate_password_hash(data["password"])
            nuevo = Usuario(username=data["username"], password=hashed)
            db.session.add(nuevo)
            db.session.commit()
            return {"mensaje": "Usuario registrado"}, 201
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error interno: {str(e)}"}, 500

# Login de usuario y generación de token JWT
@api.route("/login")
class Login(Resource):
    @api.expect(usuario_model)
    def post(self):
        data = request.get_json()
        usuario = Usuario.query.filter_by(username=data["username"]).first()
        if not usuario or not check_password_hash(usuario.password, data["password"]):
            return {"error": "Credenciales inválidas"}, 401
        token = create_access_token(identity=usuario.username)
        return {"access_token": token}

# Obtener lista de tareas o crear una nueva
@api.route("/tareas")
class ListaTareas(Resource):
    @api.marshal_list_with(tarea_model)
    @jwt_required()
    def get(self):
        return Tarea.query.all()

    @api.expect(tarea_model)
    @jwt_required()
    def post(self):
        data = request.get_json()
        nueva = Tarea(titulo=data["titulo"], completado=data.get("completado", False))
        db.session.add(nueva)
        db.session.commit()
        return {"id": nueva.id, "titulo": nueva.titulo, "completado": nueva.completado}, 201

# Obtener, actualizar o eliminar una tarea por su ID
@api.route("/tareas/<int:id>")
class UnaTarea(Resource):
    @jwt_required()
    def get(self, id):
        tarea = Tarea.query.get(id)
        if not tarea:
            return {"error": "Tarea no encontrada"}, 404
        return {"id": tarea.id, "titulo": tarea.titulo, "completado": tarea.completado}

    @api.expect(tarea_model)
    @jwt_required()
    def put(self, id):
        tarea = Tarea.query.get(id)
        if not tarea:
            return {"error": "Tarea no encontrada"}, 404
        data = request.get_json()
        tarea.titulo = data.get("titulo", tarea.titulo)
        tarea.completado = data.get("completado", tarea.completado)
        db.session.commit()
        return {"id": tarea.id, "titulo": tarea.titulo, "completado": tarea.completado}

    @jwt_required()
    def delete(self, id):
        tarea = Tarea.query.get(id)
        if not tarea:
            return {"error": "Tarea no encontrada"}, 404
        db.session.delete(tarea)
        db.session.commit()
        return {"mensaje": "Tarea eliminada correctamente"}

# ------------------------
# MANEJO PERSONALIZADO DE ERRORES
# ------------------------
@app.errorhandler(404)
def error_404(e):
    return {"error": "Ruta no encontrada"}, 404

@app.errorhandler(500)
def error_500(e):
    return {"error": "Error interno del servidor"}, 500

# ------------------------
# EJECUCIÓN LOCAL (SOLO DESARROLLO)
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)