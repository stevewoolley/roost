#!env/bin/python

"""Create a new admin user able to view the /reports endpoint."""
from getpass import getpass
import sys
from flask.ext.bcrypt import Bcrypt
from flask import current_app
from app import app
from app.models import User, db


def main():
    """Main entry point for script."""
    bcrypt = Bcrypt(app)
    with app.app_context():
        db.metadata.create_all(db.engine)
        if User.query.all():
            print 'A user already exists! Create another? (y/n):',
            create = raw_input()
            if create == 'n':
                return

        print 'Enter email address: ',
        email = raw_input()
        password = getpass()
        assert password == getpass('Password (again):')

        user = User(email=email, password=bcrypt.generate_password_hash(password), active=True, admin=True)
        db.session.add(user)
        db.session.commit()
        print 'User added.'


if __name__ == '__main__':
    sys.exit(main())