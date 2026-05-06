from flask import Flask
from routes.main_routes import main_bp

# Crear la aplicacion de Flask
app = Flask(__name__)

# Esta clave es necesaria para guardar datos en la sesion del usuario
app.secret_key = "miclavekmeans2024"

# Registrar las rutas que definimos en main_routes.py
app.register_blueprint(main_bp)

# Iniciar el servidor cuando se ejecuta este archivo directamente
if __name__ == "__main__":
    app.run(debug=True)

