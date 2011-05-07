import logging
import sqlite3
import time

from linesman.backends.base import Backend


try:
    # Python 2.7+
    from collections import OrderedDict
except ImportError:
    # Python 2.4+
    from ordereddict import OrderedDict

try:
    import cPickle as pickle
except ImportError:
    import pickle


sqlite3.register_converter("pickle", pickle.loads)
log = logging.getLogger(__name__)


class SqliteBackend(Backend):
    """
    Stores sessions in a SQLite database.
    """

    def __init__(self, filename="sessions.db"):
        """
        Opens up a connection to a sqlite3 database.

        ``filename``:
            filename of the sqlite database.  If this file does not exist, it
            will be created automatically.

            This can also be set to `:memory:` to store the database in
            memory; however, this will not persist across runs.
        """
        self.filename = filename

    @property
    def conn(self):
        return sqlite3.connect(self.filename, isolation_level=None,
            detect_types=(sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES))

    def setup(self):
        """
        Creates table for Linesman, if it doesn't already exist.
        """
        query = """
            CREATE TABLE sessions (
                uuid PRIMARY KEY,
                timestamp FLOAT,
                session PICKLE
            );
        """
        try:
            c = self.conn.cursor()
            c.execute(query)
        except sqlite3.OperationalError:
            log.debug("Table already exists.")

    def add(self, session):
        """
        Insert a new session into the database.
        """
        uuid = session.uuid
        timestamp = time.mktime(session.timestamp.timetuple())
        pickled_session = sqlite3.Binary(pickle.dumps(session, -1))

        query = "INSERT INTO sessions VALUES (?, ?, ?);"
        params = (uuid, timestamp, pickled_session)

        c = self.conn.cursor()
        c.execute(query, params)

    def clear(self):
        """
        Truncate the database.
        """
        query = "DELETE FROM sessions;"

        c = self.conn.cursor()
        c.execute(query)

    def get(self, session_uuid):
        """
        Retrieves the session from the database.
        """
        query = "SELECT session FROM sessions WHERE uuid = ?;"
        params = (session_uuid,)

        c = self.conn.cursor()
        c.execute(query, params)

        return c.fetchone()[0] if c.rowcount else None

    def get_all(self):
        """
        Generates a dictionary of the data based on the contents of the DB.
        """
        query = "SELECT uuid, session FROM sessions ORDER BY timestamp;"

        c = self.conn.cursor()
        c.execute(query)

        return OrderedDict(c.fetchall())