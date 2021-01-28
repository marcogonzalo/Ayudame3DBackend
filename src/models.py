from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

class DBManager():

    @staticmethod
    def commitSession():
        db.session.commit()

class ModelHelper():

    def save(self):
        db.session.add(self)

    def delete(self):
        db.session.delete(self)

class User(db.Model, ModelHelper):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    full_name = db.Column(db.String(120), unique=False, nullable=False)
    phone = db.Column(db.String(20), unique=False, nullable=False)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)
    # Claves ajenas:
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), unique=False, nullable=True)
    # One 
    role = db.relationship("Role", back_populates="users", lazy=True)
    # Many Relacion bidireccional :
    orders = db.relationship("Order", back_populates="helper", lazy=True)
    documents = db.relationship("Document", back_populates="user", lazy=True)
    addresses = db.relationship("Address", back_populates="user", lazy=True)
    
    def __repr__(self):
        return '<User %r>' % self.full_name

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role_id": self.role_id,
            "role": self.role.serialize()
        }

class Order(db.Model, ModelHelper): 
    id = db.Column(db.Integer, primary_key=True) 
    description = db.Column(db.String(120), unique=False, nullable=False)
    active = db.Column(db.Boolean, unique=False, default=True)  
    created_at = db.Column(db.DateTime, server_default=func.now()) 
    # Claves Foráneas:
    helper_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), unique=False, nullable=False)
    address_delivery_id = db.Column(db.Integer, db.ForeignKey('address.id'), unique=False)
    address_pickup_id = db.Column(db.Integer, db.ForeignKey('address.id'), unique=False)
    # Relaciones bidireccionales:
    #one
    helper = db.relationship("User", back_populates="orders", lazy=True)
    status = db.relationship("Status", back_populates="orders", lazy=True)
    address_delivery = db.relationship("Address", foreign_keys=[address_delivery_id])
    address_pickup = db.relationship("Address", foreign_keys=[address_pickup_id])
    #many
    documents = db.relationship("Document", back_populates="order", lazy=True)

    def __repr__(self):
        return '<Order %r>' % self.id

    def serialize(self):
        return {
            "id": self.id,
            "helper_id": self.helper_id,
            "helper": self.helper.serialize(),
            "status": self.status.serialize(),
            "status_id": self.status_id,
            "description": self.description,
            "created_at": self.created_at
        }

    def serializeForEditView(self):
        order = self.serialize()
        order["documents"] = list(map(lambda document: document.serialize(), self.documents))
        if self.address_delivery:
            order["address_delivery"] = self.address_delivery.serialize()
        if self.address_pickup:
            order["address_pickup"] = self.address_pickup.serialize()
        return order

class Status(db.Model, ModelHelper): 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(80), unique=False, nullable=False)
    # Relaciones bidireccionales:
    orders = db.relationship("Order", back_populates="status", lazy=True)

    PENDING_STATUS_ID = 1
    REJECTED_STATUS_ID = 2
    PROCESSING_STATUS_ID = 3
    READY_STATUS_ID = 4

    def __repr__(self):
        return '<Status %s>' % self.name

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name        
        }   

class Role(db.Model, ModelHelper): 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(20), unique=False, nullable=False) 
    # Relaciones bidireccionales:
    users = db.relationship("User", back_populates="role", lazy=True)

    ADMIN_ROLE_ID = 1
    MANAGER_ROLE_ID = 2
    HELPER_ROLE_ID = 3

    def __repr__(self):
        return '<Role %r>' % self.name

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name        
        }

class Document(db.Model, ModelHelper): 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(250), unique=False, nullable=False) 
    url = db.Column(db.String(255), unique=False, nullable=False) 
    # Claves Foráneas:
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False)
    # Relaciones bidireccionales:
    user = db.relationship("User", back_populates="documents", lazy=True)
    order = db.relationship("Order", back_populates="documents", lazy=True)

    def __repr__(self):
        return '<Document %r>' % self.id

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "user_id": self.user_id
        }

class Address(db.Model, ModelHelper): 
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(120), unique=False, nullable=False)
    city = db.Column(db.String(120), unique=False, nullable=False)
    country = db.Column(db.String(120), unique=False, nullable=False)
    cp = db.Column(db.String(6), unique=False, nullable=False)
    # Claves Foráneas:
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=False, nullable=False)
    # Relaciones bidireccionales:
    user = db.relationship("User", back_populates="addresses", lazy=True)
    #delivery_orders = db.relationship("Order", foreign_keys=[address_pickup_id])
    #pickup_orders = db.relationship("Order", back_populates="address_pickup", lazy=True)

    def __repr__(self):
        return '<Address %r>' % self.id

    def serialize(self):
        return {
            "id": self.id,
            "address": self.address,
            "city": self.city,
            "country": self.country,
            "cp": self.cp,
        }   
