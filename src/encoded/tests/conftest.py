'''py.test fixtures for Pyramid.

http://pyramid.readthedocs.org/en/latest/narr/testing.html
'''
from pytest import fixture

engine_settings = {
'sqlalchemy.url': 'sqlite://',
}

app_settings = {
    'persona.secret': 'GLIDING LIKE A WHALE',
    'persona.audiences': 'http://localhost:6543',
    'persona.siteName': 'ENCODE DCC Submission',
    'load_test_only': True,
    'load_sample_data': False,
}

import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


@fixture
def config(request):
    from pyramid.testing import setUp, tearDown
    request.addfinalizer(tearDown)
    return setUp()


@fixture
def dummy_request():
    from pyramid.testing import DummyRequest
    return DummyRequest()


@fixture(scope='session')
def testapp_setup(request, connection, check_constraints):
    '''WSGI application level functional testing.
    '''
    from encoded import main
    from webtest import TestApp
    app = main({}, **app_settings)

    return TestApp(app)


@fixture
def collection_test():
    return {
        'awards': 37,
        'labs': 42,
        'users': 80,
        'sources': 50,
        'targets': 21,
        'antibody-lots': 18,
        'validations': 21,
        'antibodies': 20,
    }


@fixture
def testapp(request, testapp_setup, external_tx):
    return testapp_setup


# http://docs.sqlalchemy.org/en/rel_0_8/orm/session.html#joining-a-session-into-an-external-transaction
# By binding the SQLAlchemy Session to an external transaction multiple testapp
# requests can be rolled back at the end of the test.

@fixture(scope='session')
def connection(request):
    from encoded import configure_engine
    from encoded.storage import DBSession

    engine = configure_engine(engine_settings)
    connection = engine.connect()
    DBSession.configure(bind=connection)

    @request.addfinalizer
    def close():
        connection.close()

    return connection


@fixture
def external_tx(request, connection):
    tx = connection.begin()
    request.addfinalizer(tx.rollback)
    ## The database should be empty at this point
    # from encoded.storage import Base
    # for table in Base.metadata.sorted_tables:
    #     assert connection.execute(table.count()).scalar() == 0
    return tx


@fixture
def transaction(request, external_tx):
    import transaction
    request.addfinalizer(transaction.abort)
    return transaction


@fixture
def session(transaction):
    from encoded.storage import DBSession
    return DBSession()


@fixture(scope='session')
def check_constraints(request, connection):
    '''Check deffered constraints on zope transaction commit.

    Deferred foreign key constraints are only checked at the outer transaction
    boundary, not at a savepoint. With the Pyramid transaction bound to a
    subtransaction check them manually.

    Sadly SQLite does not support manual constraint checking.
    '''
    from transaction.interfaces import ISynchronizer
    from zope.interface import implementer

    @implementer(ISynchronizer)
    class CheckConstraints(object):
        def __init__(self, connection):
            self.connection = connection
            self.enabled = self.connection.engine.url.drivername != 'sqlite'

        def beforeCompletion(self, transaction):
            if self.enabled:
                self.connection.execute('SET CONSTRAINTS ALL IMMEDIATE')

        def afterCompletion(self, transaction):
            if self.enabled:
                self.connection.execute('SET CONSTRAINTS ALL DEFERRED')

        def newTransaction(self, transaction):
            pass

    constraint_checker = CheckConstraints(connection)

    import transaction
    transaction.manager.registerSynch(constraint_checker)

    @request.addfinalizer
    def unregister():
        transaction.manager.unregisterSynch(constraint_checker)
