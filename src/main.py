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
from models import db, User, Order, Document, Role, DBManager, User, Status, Address
from amazonawss3 import upload_file_to_s3
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
from mailer import new_order_mail, order_acceptance_mail, order_rejection_mail, order_status_update_mail

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')  # Change this!
jwt = JWTManager(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.cli.command("create-roles")
def create_roles():
    if not Role.query.get(Role.ADMIN_ROLE_ID):
        role = Role(id=Role.ADMIN_ROLE_ID, name="Admin")
        role.save()
    if not Role.query.get(Role.MANAGER_ROLE_ID):
        role = Role(id=Role.MANAGER_ROLE_ID, name="Manager")
        role.save()
    if not Role.query.get(Role.HELPER_ROLE_ID):
        role = Role(id=Role.HELPER_ROLE_ID, name="Helper")
        role.save()
    DBManager.commitSession()
    return

@app.cli.command("create-statuses")
def create_statuses():
    if not Status.query.get(Status.PENDING_STATUS_ID):
        status = Status(id=Status.PENDING_STATUS_ID, name="Pending")
        status.save()
    if not Status.query.get(Status.REJECTED_STATUS_ID):
        status = Status(id=Status.REJECTED_STATUS_ID, name="Rejected")
        status.save()
    if not Status.query.get(Status.PROCESSING_STATUS_ID):
        status = Status(id=Status.PROCESSING_STATUS_ID, name="Processing")
        status.save()
    if not Status.query.get(Status.READY_STATUS_ID):
        status = Status(id=Status.READY_STATUS_ID, name="Ready")
        status.save()
    if not Status.query.get(5):
        status = Status(id=5, name="Complete")
        status.save()
    DBManager.commitSession()
    return

# generate sitemap with all your endpoints
# @app.route('/')
# def sitemap():
#     return generate_sitemap(app)

#========================================================================
@app.route('/users', methods=['GET'])
def users():
    users = User.query.all()
    usersJson = list(map(lambda user: user.serialize(), users))
    return jsonify(usersJson), 200

@app.route('/orders', methods=['GET'])
@jwt_required
def orders():
    user_authenticated_id = get_jwt_identity()
    user = User.query.get(user_authenticated_id)
    if user.role_id == Role.HELPER_ROLE_ID:
        orders = Order.query.filter(Order.helper_id == user_authenticated_id, Order.status_id != Status.REJECTED_STATUS_ID)
    else:
        orders = Order.query.all()
    ordersJson = list(map(lambda order: order.serialize(), orders))
    return jsonify(ordersJson), 200

@app.route('/orders/<int:id>', methods=['GET'])
@jwt_required
def get_order(id):
    order = Order.query.get(id)   
    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>/accept', methods=['POST'])
@jwt_required
def accept_order(id):
    order = Order.query.get(id)
    order.status_id = Status.PROCESSING_STATUS_ID
    order.save()
    order_acceptance_mail(order)
    DBManager.commitSession()

    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>/reject', methods=['POST'])
@jwt_required
def reject_order(id):
    order = Order.query.get(id)
    order.status_id = Status.REJECTED_STATUS_ID
    order.save()
    response = DBManager.commitSession()
    order_rejection_mail(order)

    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>/set-ready', methods=['POST'])
@jwt_required
def set_order_ready(id):
    order = Order.query.get(id)
    order.status_id = Status.READY_STATUS_ID
    order.save()
    DBManager.commitSession()
    order_status_update_mail(order)
    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>/save-video', methods=['POST'])
@jwt_required
def save_video(id):
    user_authenticated_id = get_jwt_identity()
    video = request.json.get('video', None)
    order = Order.query.get(id)
    
    document = Document(name="Video", url=video, order=order, user_id=user_authenticated_id)
    document.save()

    DBManager.commitSession()
    order_new_data_mail(order)

    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>/addresses/save', methods=['POST'])
@jwt_required
def save_order_addresses(id):
    user_authenticated_id = get_jwt_identity()
    
    pickup_address = Address(address=request.json.get('pickup').get('address'), city=request.json.get('pickup').get('city'), country=request.json.get('pickup').get('country'), cp=request.json.get('pickup').get('CP'),user_id=user_authenticated_id)
    pickup_address.save()
    
    delivery_address = Address(address=request.json.get('delivery').get('address'), city=request.json.get('delivery').get('city'), country=request.json.get('delivery').get('country'), cp=request.json.get('delivery').get('CP'),user_id=user_authenticated_id)
    delivery_address.save()
    
    order = Order.query.get(id)
    
    order.address_delivery = delivery_address
    order.address_pickup = pickup_address

    order.save()

    DBManager.commitSession()
    order_new_data_mail(order)

    return jsonify(order.serializeForEditView()), 200

@app.route('/documents/<int:id>/delete', methods=['DELETE'])
@jwt_required
def delete_document(id):
    document = Document.query.get(id)
    document.delete()
    DBManager.commitSession()
    return jsonify(document.serialize()), 200

@app.route('/helpers', methods=['GET'])
@jwt_required
def helpers():
    helpers = User.query.filter_by(role_id=Role.HELPER_ROLE_ID).all()
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

    if os.environ.get('S3_ID'):
        files = request.files
        for key in files:
            file = files[key]
            if file:
                url_document = upload_file_to_s3(file, os.environ.get('S3_BUCKET_NAME'))
                if url_document:
                    document = Document(name=file.filename, url=url_document, order=order, user_id=user_authenticated_id)
                    document.save()
    else:
        print("Faltan las credenciales de AWS")

    DBManager.commitSession()

    orderSerialized = order.serialize()

    if orderSerialized:
        new_order_mail(order.helper,order)
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
