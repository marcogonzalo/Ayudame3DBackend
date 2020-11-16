import os
from flask_admin import Admin
from models import db, User, Order, Status, Document, Address, Role
from flask_admin.contrib.sqla import ModelView

#https://flask-admin.readthedocs.io/en/latest/introduction/#customizing-builtin-views
class OnlyViewModelView(ModelView):
    column_display_pk = True
    can_delete = False  # disable model deletion
    can_create = False
    can_edit = False

def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

    # Add your models here, for example this is how we add a the User model to the admin
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Order, db.session))
    admin.add_view(ModelView(Document, db.session))
    admin.add_view(ModelView(Address, db.session))

    admin.add_view(OnlyViewModelView(Status, db.session))
    admin.add_view(OnlyViewModelView(Role, db.session))

    # You can duplicate that line to add mew models
    # admin.add_view(ModelView(YourModelName, db.session))