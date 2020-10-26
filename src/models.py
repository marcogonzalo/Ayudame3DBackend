from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    full_name = db.Column(db.String(120), unique=False, nullable=False)
    phone = db.Column(db.Integer, unique=False, nullable=False)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)
    # Claves Foráneas:
    role_id = db.Column(db.String(20), db.ForeingKey('user.id'), unique=False, nullable=False)
    # Relacion bidireccional :
    orders = db.relationship("Order", back_populates="user", lazy=True)
    document = db.relationship("Document", back_populates="user", lazy=True)
    role = db.relationship("Role", back_populates="user", lazy=True)
    address = db.relationship("Address", back_populates="user", lazy=True)
    
    def __repr__(self):
        return '<User %r>' % self.full_name

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email
           
        }


class Order(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    description = db.Column(db.String(120), unique=False, nullable=False)   
    # Claves Foráneas:
    helper_id = db.Column(db.String(80), db.ForeingKey('helper.id'), unique=False, nullable=False)
    status_id = db.Column(db.String(20), db.ForeingKey('status.id'), unique=False, nullable=False)
    address_delivery_id = db.Column(db.String(80), db.ForeingKey('address_delivery.id'), unique=False, nullable=False)
    address_pickup_id = db.Column(db.String(80), db.ForeingKey('address_pickup.id'), unique=False, nullable=False)
    # Relaciones bidireccionales:
    user = db.relationship("User", back_populates="order", lazy=True)
    document = db.relationship("Document", back_populates="order", lazy=True)
    status = db.relationship("Status", back_populates="order", lazy=True)
    address = db.relationship("Address", back_populates="order", lazy=True)


    def __repr__(self):
        return '<Order %r>' % self.id

    def serialize(self):
        return {
            "id": self.id,
            "status": self.status        
        }


class Status(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(80), unique=False, nullable=False)
    # Relaciones bidireccionales:
    order = db.relationship("Order", back_populates="status", lazy=True)

    def __repr__(self):
        return '<Status %r>' % self.id

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name        
        }   


class Role(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(20), unique=False, nullable=False) 
    # Relaciones bidireccionales:
    user = db.relationship("User", back_populates="role", lazy=True)

    def __repr__(self):
        return '<Role %r>' % self.id

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name        
        }   


class Document(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(20), unique=False, nullable=False) 
    # Claves Foráneas:
    order_id = db.Column(db.String(20), db.ForeingKey('order.id'), unique=False, nullable=False)
    user_id = db.Column(db.String(20), db.ForeingKey('user.id'), unique=False, nullable=False)
    # Relaciones bidireccionales:
    user = db.relationship("User", back_populates="document", lazy=True)
    order = db.relationship("Order", back_populates="document", lazy=True)

    def __repr__(self):
        return '<Document %r>' % self.id

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name        
        }   


class Address(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(120), unique=False, nullable=False)
    city = db.Column(db.String(120), unique=False, nullable=False)
    country = db.Column(db.String(120), unique=False, nullable=False)
    cp = db.Column(db.Integer, unique=False, nullable=False)  
    # Claves Foráneas:
    user_id = db.Column(db.String(20), db.ForeingKey('user.id'), unique=False, nullable=False)
    # Relaciones bidireccionales:
    user = db.relationship("User", back_populates="address", lazy=True)
    order = db.relationship("Order", back_populates="address", lazy=True)

    def __repr__(self):
        return '<Address %r>' % self.id

    def serialize(self):
        return {
            "id": self.id,
            "name": self.address        
        }   

