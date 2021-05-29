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
from models import db, User, Order, Document, Role, DBManager, Status, Address
from amazonawss3 import upload_file_to_s3
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
from mailer import (
    new_order_mail, order_acceptance_mail, order_rejection_mail, 
    order_status_update_mail, order_new_data_mail
)
from commands import create_admin, create_roles, create_statuses

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.url_map.strict_slashes = False
# database condiguration
if os.environ.get("DATABASE_URL") is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')  # Change this!
jwt = JWTManager(app)

app.cli.add_command(create_admin)
app.cli.add_command(create_roles)
app.cli.add_command(create_statuses)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


# generate sitemap with all your endpoints
# @app.route('/')
# def sitemap():
#     return generate_sitemap(app)

#========================================================================
@app.route('/users', methods=['GET'])
@jwt_required()
def users():
    users = User.query.filter(User.is_active == True).all()
    usersJson = list(map(lambda user: user.serialize(), users))
    return jsonify(usersJson), 200

@app.route('/users/<int:id>', methods=['GET'])
@jwt_required()
def edit_user(id):
    user = User.query.get(id)
    return jsonify(user.serialize()), 200

@app.route('/users/create', methods=['POST'])
@jwt_required()
def create_user():
    user_authenticated_id = get_jwt_identity()

    form = request.form.to_dict()
    form['password_user'] = generate_password_hash(form['password_user'], method='sha256')

    new_user = User(email=str(form["email_address"]),password=form['password_user'],full_name=str(form["full_name"]),phone=str(form["phone_number"]), is_active= True)
    new_user.role_id = form["role_id"]

    new_user.save()
    DBManager.commitSession()

    return jsonify("User created"), 201

@app.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
def save_user(id):
    userData = request.json.get('user', None)
    user = User.query.get(id)
    
    user.email = userData["email"]
    user.full_name = userData["full_name"]
    user.phone = userData["phone"]
    user.role_id = userData["role_id"]

    user.save()
    DBManager.commitSession()

    return jsonify(user.serialize()), 200

@app.route('/users/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    user = User.query.get(id)  
    if user is None:
        raise APIException('User not found', status_code=404)
    user.is_active = False
    DBManager.commitSession()
    
    return jsonify(user.serialize()), 200

@app.route('/roles', methods=['GET'])
@jwt_required()
def roles():
    roles = Role.query.all()
    rolesJson = list(map(lambda role: role.serialize(), roles))
    return jsonify(rolesJson), 200

@app.route('/status', methods=['GET'])
@jwt_required()
def status():
    statuses = Status.query.all()
    statusesJson = list(map(lambda status: status.serialize(), statuses))
    return jsonify(statusesJson), 200

@app.route('/orders', methods=['GET'])
@jwt_required()
def orders():
    user_authenticated_id = get_jwt_identity()
    user = User.query.get(user_authenticated_id)
    if user.role_id == Role.HELPER_ROLE_ID:
        orders = Order.query.filter(Order.helper_id == user_authenticated_id, Order.status_id != Status.REJECTED_STATUS_ID, Order.active == True).order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.filter(Order.active == True).order_by(Order.created_at.desc()).all()

    ordersJson = list(map(lambda order: order.serialize(), orders))

    return jsonify(ordersJson), 200

@app.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    user_authenticated_id = get_jwt_identity()
    helper_id = request.form.get('helper_id')
    description = request.form.get('description')
    long_description = request.form.get('long_description')
  
    order = Order(description=description, long_description=long_description, helper_id=helper_id, status_id=1)
    order.save()

    documentURL = request.form.get('files')
    if documentURL:
        filename='Documents URL'
        document = Document(name=filename, url=documentURL, order=order, user_id=user_authenticated_id)
        document.save()
 

    DBManager.commitSession()

    orderSerialized = order.serialize()
    if orderSerialized:
        new_order_mail(order.helper,order)
    # Añadir los documentos al objeto
    orderSerialized["documents"] = list(map(lambda document: document.serialize(), order.documents))
    return jsonify({"status": "ok", "order": orderSerialized})


@app.route('/orders/<int:id>', methods=['GET'])
@jwt_required()
def get_order(id):
    order = Order.query.get(id)   
    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_order(id):
    order = Order.query.get(id)  
    if order is None:
        raise APIException('Order not found', status_code=404)
    order.active = False
    print("ORDER ACTIVE",order.active)
    DBManager.commitSession()
    
    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>', methods=['PUT'])
@jwt_required()
def update_order(id):
    order = Order.query.get(id)
    if request.form.get('helper_id') and (int(request.form.get('helper_id')) != order.helper_id or order.status_id == Status.REJECTED_STATUS_ID):
        order.status_id = Status.PENDING_STATUS_ID
        order.helper_id = request.form.get('helper_id')
        order.save()
        new_order_mail(order.helper,order)
    if not request.form.get('description') is None:
        order.description = request.form.get('description')
        order.long_description = request.form.get('long_description')
        order.save()

    DBManager.commitSession()

    orderSerialized = order.serializeForEditView()
        
    return jsonify(orderSerialized), 200

@app.route('/orders/<int:id>/accept', methods=['POST'])
@jwt_required()
def accept_order(id):
    order = Order.query.get(id)
    order.status_id = Status.PROCESSING_STATUS_ID
    order.save()
    order_acceptance_mail(order)
    DBManager.commitSession()

    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>/reject', methods=['POST'])
@jwt_required()
def reject_order(id):
    order = Order.query.get(id)
    order.status_id = Status.REJECTED_STATUS_ID
    order.save()
    response = DBManager.commitSession()
    order_rejection_mail(order)

    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>/set-ready', methods=['POST'])
@jwt_required()
def set_order_ready(id):
    order = Order.query.get(id)
    order.status_id = Status.READY_STATUS_ID
    order.save()
    DBManager.commitSession()
    order_status_update_mail(order)
    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>/set-approved', methods=['POST'])
@jwt_required()
def set_order_approved(id):
    order = Order.query.get(id)
    order.status_id = Status.APPROVED_STATUS_ID
    order.save()
    DBManager.commitSession()
    order_status_update_mail(order)
    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>/save-video', methods=['POST'])
@jwt_required()
def save_video(id):
    user_authenticated_id = get_jwt_identity()
    order = Order.query.get(id)

    if os.environ.get('AWS_S3_BUCKET_NAME'):
        files = request.files
        print("files", files)
        for key in files:

            file = files[key]

            if file:
                url_document = upload_file_to_s3(file, os.environ.get('AWS_S3_BUCKET_NAME'))

                if url_document:
                    document = Document(name=file.filename, url=url_document, order=order, user_id=user_authenticated_id)
                    document.save()
    else:
        print("Faltan las credenciales de AWS")


    DBManager.commitSession()
    order_new_data_mail(order)

    return jsonify(order.serializeForEditView()), 200

@app.route('/orders/<int:id>/save-files', methods=['POST'])
@jwt_required()
def save_order_files(id):
    user_authenticated_id = get_jwt_identity()
    order = Order.query.get(id)
    body = request.get_json()

    filename='Order #'+str(order.id)+' files'
    document = Document(name=filename, url=body['files'], order=order, user_id=user_authenticated_id)
    
    document.save()    
    DBManager.commitSession()

    order_new_data_mail(order)

    return jsonify(order.serializeForEditView()), 201

@app.route('/orders/<int:id>/addresses/save', methods=['POST'])
@jwt_required()
def save_order_addresses(id):
    user_authenticated_id = get_jwt_identity()
    
    # pickup_address = Address(address=request.json.get('pickup').get('address'), city=request.json.get('pickup').get('city'), country=request.json.get('pickup').get('country'), cp=request.json.get('pickup').get('CP'),user_id=user_authenticated_id)
    # pickup_address.save()
    
    # delivery_address = Address(address=request.json.get('delivery').get('address'), city=request.json.get('delivery').get('city'), country=request.json.get('delivery').get('country'), cp=request.json.get('delivery').get('CP'),user_id=user_authenticated_id)
    # delivery_address.save()
    
    order = Order.query.get(id)
    # order.address_delivery = delivery_address
    # order.address_pickup = pickup_address

    # order.save()

    order.status_id = Status.COMPLETED_STATUS_ID
    order.save()
    response = DBManager.commitSession()
    order_rejection_mail(order)
    

    order_new_data_mail(order)

    return jsonify(order.serializeForEditView()), 200

@app.route('/documents/<int:id>/delete', methods=['DELETE'])
@jwt_required()
def delete_document(id):
    document = Document.query.get(id)
    document.delete()
    DBManager.commitSession()
    return jsonify(document.serialize()), 200

@app.route('/helpers', methods=['GET'])
@jwt_required()
def helpers():
    helpers = User.query.filter_by(role_id=Role.HELPER_ROLE_ID).all()
    helpersJson = list(map(lambda helper: helper.serialize(), helpers))
    return jsonify(helpersJson), 200

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

    user = User.query.filter_by(email=email).filter_by(is_active=True).one_or_none()
    if not user:
        return jsonify({"status": 'ko', "msg": "Bad username or password"}), 401

    # access_token = create_access_token(identity=user.id)

    if check_password_hash(user.password, password): 
        access_token = create_access_token(identity=user.id)
    else:
        return jsonify({"status": 'ko', "msg": "Bad username or password"}), 401

    return jsonify({"status": 'ok', "access_token": access_token, "user": user.serialize()}), 200

@app.route('/get-user-authenticated', methods=["GET"])
@jwt_required()
def get_user_authenticated():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify(user=user.serialize()), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
