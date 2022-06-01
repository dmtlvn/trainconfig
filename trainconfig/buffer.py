import os
import uuid
import yaml
import sqlite3


TMP_DIR = os.path.expanduser("~/.train_config/")

CHANGELOG_BUFFER_FILE = os.path.join(TMP_DIR, "changelog.db")
EDITOR_BUFFER_FILE = os.path.join(TMP_DIR, "editor.db")


def salt():
    return uuid.uuid4().hex
   
    
class SQLiteBuffer:
    
    create_query = "CREATE TABLE {buffer} (item_id INT, yaml TEXT, editable INT, salt TEXT)"
    insert_query = "INSERT INTO {buffer} VALUES (0, '{yaml}', '{editable}', '{salt}')"
    delete_query = "DELETE FROM {buffer} WHERE item_id = 0"
    update_query = "UPDATE {buffer} SET yaml = '{yaml}', editable = '{editable}', salt = '{salt}' WHERE item_id = 0"
    select_query = "SELECT yaml, editable FROM {buffer} WHERE item_id = 0"
    
    def __init__(self, name, file):
        self.file = file
        self.name = name
        with SQLiteTransaction(self.file) as cursor:
            try:
                cursor.execute(self.create_query.format(buffer = self.name))
                cursor.execute(self.insert_query.format(buffer = self.name, yaml = '', editable = True, salt = self._salt))
            except sqlite3.OperationalError:
                if not cursor.execute(self.select_query.format(buffer = self.name)).fetchone():
                    cursor.execute(self.insert_query.format(buffer = self.name, yaml = '', salt = self._salt))
        
    def put(self, item, editable: bool):
        yaml_str = self._escape(yaml.safe_dump(item))
        with SQLiteTransaction(self.file) as cursor:
            cursor.execute(self.update_query.format(
                buffer = self.name, 
                yaml = yaml_str,
                editable = int(editable),
                salt = self._salt
            ))
        return self
            
    def get(self):
        with SQLiteTransaction(self.file) as cursor:
            record = cursor.execute(self.select_query.format(buffer = self.name)).fetchone()
        if record is not None:
            yaml_str, editable = record
            return yaml.safe_load(yaml_str), bool(editable)
        else:
            return None, False

    @staticmethod
    def _escape(s):
        return s.replace("'", "''")
    
    @property
    def _salt(self):
        return uuid.uuid4().hex
        
        
class SQLiteTransaction:

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.conn = sqlite3.connect(self.path, isolation_level = "EXCLUSIVE", timeout = 999999)
        self.conn.execute('BEGIN EXCLUSIVE')
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.commit()
        self.conn.close()
