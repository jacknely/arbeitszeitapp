from flask import Flask, session
from flask_table import Col, Table  # noqa: Do not delete
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

import project.extensions
from project.extensions import login_manager


def create_app(config=None, db=None, migrate=None, template_folder=None):
    if template_folder is None:
        template_folder = "templates"
    app = Flask(
        __name__, instance_relative_config=False, template_folder=template_folder
    )

    if config:
        app.config.update(**config)
    else:
        app.config.from_envvar("ARBEITSZEIT_APP_CONFIGURATION")

    if db is None:
        db = project.extensions.db

    if migrate is None:
        migrate = project.extensions.migrate

    # Where to redirect the user when he attempts to access a login_required
    # view without being logged in.
    login_manager.login_view = "auth.start"

    # Init Flask-Talisman
    if app.config["ENV"] == "production":
        csp = {"default-src": ["'self'", "'unsafe-inline'", "*.fontawesome.com"]}
        Talisman(app, content_security_policy=csp)

    # init flask extensions
    CSRFProtect(app)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from project.commands import update_and_payout

        app.cli.command("payout")(update_and_payout)

        from .models import Company, Member

        @login_manager.user_loader
        def load_user(user_id):
            """
            This callback is used to reload the user object from the user ID
            stored in the session.
            """
            if "user_type" in session:
                user_type = session["user_type"]
                if user_type == "member":
                    return Member.query.get(user_id)
                elif user_type == "company":
                    return Company.query.get(user_id)

        # register blueprints
        from . import company, member
        from .auth import routes as auth_routes

        app.register_blueprint(auth_routes.auth)
        app.register_blueprint(company.blueprint.main_company)
        app.register_blueprint(member.blueprint.main_member)

        return app
