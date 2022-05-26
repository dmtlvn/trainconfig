import os
import uuid
import yaml
import sqlite3


TMP_DIR = os.path.join(os.path.expanduser("~"), ".train_config/")

HISTORY_BUFFER_FILE = os.path.join(TMP_DIR, "history.db")
FORM_BUFFER_FILE = os.path.join(TMP_DIR, "form.db")


def salt():
    return uuid.uuid4().hex
   
    
class SQLiteBuffer:
    
    create_query = "CREATE TABLE {buffer} (item_id, yaml, salt)"
    insert_query = "INSERT INTO {buffer} VALUES (0, '{yaml}', '{salt}')"
    delete_query = "DELETE FROM {buffer} WHERE item_id = 0"
    update_query = "UPDATE {buffer} SET yaml = '{yaml}', salt = '{salt}' WHERE item_id = 0"
    select_query = "SELECT yaml FROM {buffer} WHERE item_id = 0"
    
    def __init__(self, name, file = 'buffer.db'):
        self.file = file
        self.name = name
        with SQLiteTransaction(self.file) as cursor:
            try:
                cursor.execute(self.create_query.format(buffer = self.name))
                cursor.execute(self.insert_query.format(buffer = self.name, yaml = '', salt = self._salt))
            except sqlite3.OperationalError:
                if not cursor.execute(self.select_query.format(buffer = self.name)).fetchone():
                    cursor.execute(self.insert_query.format(buffer = self.name, yaml = '', salt = self._salt))
        
    def put(self, item):
        yaml_str = self._escape(yaml.safe_dump(item))
        with SQLiteTransaction(self.file) as cursor:
            cursor.execute(self.update_query.format(
                buffer = self.name, 
                yaml = yaml_str, 
                salt = self._salt
            ))
            
    def get(self):
        with SQLiteTransaction(self.file) as cursor:
            yaml_str = cursor.execute(self.select_query.format(buffer = self.name)).fetchone()
            yaml_str = yaml_str[0] if yaml_str is not None else None
        item = yaml.safe_load(yaml_str) if yaml_str is not None else None
        return item
    
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