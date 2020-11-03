from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    full_name = db.Column(db.String(120), unique=False, nullable=False)
    phone = db.Column(db.Integer, unique=False, nullable=False)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)
    #Claves ajenas:
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), unique=False, nullable=False)
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
            "phone": self.phone
        }

class Order(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    description = db.Column(db.String(120), unique=False, nullable=False)   
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

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return '<Order %r>' % self.id

    def serialize(self):
        return {
            "id": self.id,
            "helper_id": self.helper_id,
            "helper": self.helper.serialize(),
            "status": self.status.serialize(),
            "description": self.description
        }

class Status(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(80), unique=False, nullable=False)
    # Relaciones bidireccionales:
    orders = db.relationship("Order", back_populates="status", lazy=True)

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
    users = db.relationship("User", back_populates="role", lazy=True)

    def __repr__(self):
        return '<Role %r>' % self.name

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name        
        }   

class Document(db.Model): 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(20), unique=False, nullable=False) 
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
            "name": self.name        
        }

    def save(self):
        db.session.add(self)
        db.session.commit()

class Address(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(120), unique=False, nullable=False)
    city = db.Column(db.String(120), unique=False, nullable=False)
    country = db.Column(db.String(120), unique=False, nullable=False)
    cp = db.Column(db.Integer, unique=False, nullable=False)  
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
            "name": self.address        
        }   

#
#class Order(Base): #one
#    lineitems = relationship("Lineitem", back_populates="order")
#
#class Lineitem(Base): #many
#    order_id = Column(Integer, ForeignKey('order.id'))
#    order = relationship("Order", back_populates="lineitems")