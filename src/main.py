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
from models import db, User, Order, Document
from amazonawss3 import upload_file_to_s3
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)


#from models import Person

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


@app.route('/upload-file', methods=['POST'])
def upload_file():
    file = request.files["document"]
    description = request.form.get('description')
    helper_id = request.form.get('helper_id')

    if file:
        url_document = upload_file_to_s3(file, os.environ.get('S3_BUCKET_NAME'))

        order = Order(description=description, helper_id=helper_id, status_id=1)
        order.save()

        document = Document(name=file.filename,url=url_document, order_id=order.id, user_id=1)
        document.save()

        return url_document, 200

    else:
        return "ko"


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
    return jsonify({"status": 'ok', "access_token": access_token}), 200

#====================================================================================

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
