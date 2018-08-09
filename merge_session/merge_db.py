import logging
import collections

from django.contrib.sessions.backends.db import SessionStore as DBStore
from django.contrib.sessions.base_session import AbstractBaseSession
from django.db import models
from django.contrib.sessions.backends.base import (
    CreateError, UpdateError,
)
from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from django.db import DatabaseError, IntegrityError, router, transaction
from daphne_brain.session_lock import session_lock


# from https://stackoverflow.com/questions/39997469/how-to-deep-merge-dicts
def combine_dict(map1: dict, map2: dict):
    def update(d: dict, u: dict):
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                r = update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d
    _result = {}
    update(_result, map1)
    update(_result, map2)
    return _result


class MergeSession(AbstractBaseSession):
    version = models.IntegerField()

    @classmethod
    def get_session_store_class(cls):
        return SessionStore

    class Meta(AbstractBaseSession.Meta):
        db_table = 'django_session'



class SessionStore(DBStore):
    def __init__(self, session_key=None):
        super().__init__(session_key)
        self._version = 0

    @classmethod
    def get_model_class(cls):
        return MergeSession

    def load(self):
        try:
            s = self.model.objects.get(
                session_key=self.session_key,
                expire_date__gt=timezone.now()
            )
            self._version = s.version
            return self.decode(s.session_data)
        except (self.model.DoesNotExist, SuspiciousOperation) as e:
            if isinstance(e, SuspiciousOperation):
                logger = logging.getLogger('django.security.%s' % e.__class__.__name__)
                logger.warning(str(e))
            self._session_key = None
            self._version = 0
            return {}

    def load_or_default(self):
        try:
            s = self.model.objects.get(
                session_key=self.session_key,
                expire_date__gt=timezone.now()
            )
            return self.decode(s.session_data), s.version
        except (self.model.DoesNotExist, SuspiciousOperation) as e:
            return {}, -1

    def create_model_instance(self, data):
        obj = super().create_model_instance(data)
        obj.version = self._version
        return obj

    def save(self, must_create=False):
        """
        Save the current session data to the database. If 'must_create' is
        True, raise a database error if the saving operation doesn't create a
        new entry (as opposed to possibly updating an existing entry).
        """
        if self.session_key is None:
            return self.create()
        data = self._get_session(no_load=must_create)
        obj = self.create_model_instance(data)
        using = router.db_for_write(self.model, instance=obj)
        try:
            with session_lock:
                with transaction.atomic(using=using):
                    # Load model from database to compare the version values
                    db_data, db_version = self.load_or_default()
                    if db_version == obj.version:
                        obj.version += 1
                        obj.save(force_insert=must_create, force_update=not must_create, using=using)
                    else:
                        # dictionary merge
                        obj.session_data = self.encode(combine_dict(db_data, data))
                        # Increment version value to max + 1
                        obj.version = max(obj.version, db_version) + 1
                        obj.save(force_insert=must_create, force_update=not must_create, using=using)
        except IntegrityError:
            if must_create:
                raise CreateError
            raise
        except DatabaseError:
            if not must_create:
                raise UpdateError
            raise
