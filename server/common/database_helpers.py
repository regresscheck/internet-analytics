from common.models.base import Base
from common.database import SessionLocal, engine
from sqlalchemy.sql import ClauseElement


def create_db():
    Base.metadata.create_all(bind=engine)


session = SessionLocal()


def create_or_update(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        return _do_update(session, instance, defaults), False
    else:
        params = {k: v for k, v in kwargs.items(
        ) if not isinstance(v, ClauseElement)}
        params.update(defaults or {})
        instance = model(**params)
        try:
            session.add(instance)
            session.commit()
        except Exception:  # The actual exception depends on the specific database so we catch all exceptions. This is similar to the official documentation: https://docs.sqlalchemy.org/en/latest/orm/session_transaction.html
            session.rollback()
            instance = session.query(model).filter_by(**kwargs).one()
            return _do_update(session, instance, defaults), False
        else:
            return instance, True


def _do_update(session, instance, new_values):
    for key, value in new_values.items():
        setattr(instance, key, value)
    session.commit()
    return instance
