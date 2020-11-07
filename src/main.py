"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Order, Document, Role, DBManager, User
from amazonawss3 import upload_file_to_s3
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
jwt = JWTManager(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.cli.command("create-roles")
def create_roles():
    if not Role.query.get(1):
        role = Role(id=1, name="Admin")
        role.save()
    if not Role.query.get(2):
        role = Role(id=2, name="Manager")
        role.save()
    if not Role.query.get(3):
        role = Role(id=3, name="Helper")
        role.save()
    DBManager.commitSession()
    return

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

#========================================================================
@app.route('/user', methods=['GET'])
def users():
    users = User.query.all()
    usersJson = list(map(lambda user: user.serialize(), users))
    return jsonify(usersJson), 200

@app.route('/orders', methods=['GET'])
@jwt_required
def orders():
    orders = Order.query.all()
    ordersJson = list(map(lambda order: order.serialize(), orders))
    return jsonify(ordersJson), 200

@app.route('/orders/<int:id>', methods=['GET'])
@jwt_required
def get_order(id):
    order = Order.query.get(id)
    return jsonify(order.serialize()), 200

@app.route('/helpers', methods=['GET'])
@jwt_required
def helpers():
    helpers = User.query.filter_by(role_id=3).all()
    helpersJson = list(map(lambda helper: helper.serialize(), helpers))
    return jsonify(helpersJson), 200

@app.route('/orders/create', methods=['POST'])
@jwt_required
def create_order():
    user_authenticated_id = get_jwt_identity()
    helper_id = request.form.get('helper_id')
    description = request.form.get('description')
    
    order = Order(description=description, helper_id=helper_id, status_id=1)
    order.save()

    print(request.files)
    files = request.files
    for key in files:
        print(key)
        file = files[key]
        print(file)
        if file:
            url_document = upload_file_to_s3(file, os.environ.get('S3_BUCKET_NAME'))
            print(url_document)
            document = Document(name=file.filename, url=url_document, order=order, user_id=user_authenticated_id)
            document.save()

    DBManager.commitSession()

    orderSerialized = order.serialize()
    #Añadir los documentos al objeto
    orderSerialized["documents"] = list(map(lambda document: document.serialize(), order.documents))
    return jsonify({"status": "ok", "order": orderSerialized})

@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    if not email:
        return jsonify({"msg": "Missing email parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400
    user = User.query.filter_by(email=email).filter_by(password=password).filter_by(is_active=True).one_or_none()
    if not user:
        return jsonify({"status": 'ko', "msg": "Bad username or password"}), 401
    access_token = create_access_token(identity=user.id)
    return jsonify({"status": 'ok', "access_token": access_token, "user": user.serialize()}), 200

@app.route('/get-user-authenticated', methods=["GET"])
@jwt_required
def get_user_authenticated():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify(user=user.serialize()), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
