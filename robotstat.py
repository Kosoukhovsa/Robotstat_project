import os
import click
from flask_migrate import Migrate
from flask_mail import Message
from app import create_app, db, mail
from app.models import Clinics, Patients, Users, UserRoles, Roles
from dotenv import load_dotenv

# Загрузка переменных окружения
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Clinics=Clinics, Patients=Patients, Users=Users, mail=mail,
                UserRoles=UserRoles, Roles=Roles)

@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

#if __name__ == '__main__':
#    app.run(debug=True)
