from typing import List, Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from injector import Injector, Module, inject, provider, singleton

from arbeitszeit_flask import create_app
from arbeitszeit_flask.dependency_injection import FlaskModule, ViewsModule
from arbeitszeit_flask.extensions import db
from tests.dependency_injection import TestingModule


class FlaskConfiguration(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            if key.isupper():
                setattr(self, key, value)

    def _get_template_folder(self) -> Optional[str]:
        return self.get("template_folder")

    def _set_template_folder(self, template_folder: Optional[str]) -> None:
        self["template_folder"] = template_folder

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if key.isupper():
            setattr(self, key, value)

    def __delitem__(self, key):
        super().__delitem__(key)
        if key.isupper():
            delattr(self, key)

    # Allows you to control where flask loads templates from.
    template_folder = property(_get_template_folder, _set_template_folder)


FLASK_TESTING_CONFIGURATION = FlaskConfiguration(
    {
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "dev secret key",
        "WTF_CSRF_ENABLED": False,
        "SERVER_NAME": "test.name",
        "ENV": "development",
        "DEBUG_DETAILS": False,
        "SECURITY_PASSWORD_SALT": "dev password salt",
        "TESTING": True,
        "MAIL_DEFAULT_SENDER": "test_sender@cp.org",
        "MAIL_BACKEND": "flask_mail",
        "LANGUAGES": {"en": "English", "de": "Deutsch"},
    }
)


class SqliteModule(Module):
    @provider
    @singleton
    def provide_sqlalchemy(self, app: Flask) -> SQLAlchemy:
        app.app_context().push()
        db.create_all()
        return db

    @provider
    @singleton
    def provide_app(self, config: FlaskConfiguration) -> Flask:
        return create_app(config=config, db=db, template_folder=config.template_folder)

    @provider
    def provide_flask_configuration(self) -> FlaskConfiguration:
        return FLASK_TESTING_CONFIGURATION


def get_dependency_injector(additional_modules: Optional[List[Module]] = None):
    modules: List[Module] = [
        FlaskModule(),
        ViewsModule(),
        TestingModule(),
        SqliteModule(),
    ]
    if additional_modules is not None:
        modules.extend(additional_modules)
    return Injector(modules)


def injection_test(original_test):
    injector = get_dependency_injector()

    def wrapper(*args, **kwargs):
        return injector.call_with_injection(
            inject(original_test), args=args, kwargs=kwargs
        )

    return wrapper
