import os
from getpass import getpass

import click
from flask import Flask
from flask.cli import with_appcontext
from sqlalchemy import create_engine, Table
from werkzeug.security import generate_password_hash, check_password_hash

from models import User, Role, DBManager


@click.command()
@with_appcontext
def create_admin():
    full_name = None
    while full_name is None:
        full_name = input('Full name: ') or None

    email = None
    while email is None:
        email = input('email: ') or None

    password = None
    while password is None:
        password = getpass('Password: ') or None

    phone = None
    while phone is None:
        phone = input('Phone: ') or None

    hashed_password = generate_password_hash(password, method='sha256')

    new_user = User(
        email=email,
        password=hashed_password,
        full_name=full_name,
        phone=phone,
        role_id=Role.ADMIN_ROLE_ID,
        is_active= True,
    )

    new_user.save()
    DBManager.commitSession()


@click.command()
@with_appcontext
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

@click.command()
@with_appcontext
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
