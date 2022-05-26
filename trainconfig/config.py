import os
import atexit
import yaml

from dotdict import dotdict

from .history import History
from .utils import parse_config, assemble_config
from .buffer import SQLiteBuffer, HISTORY_BUFFER_FILE, FORM_BUFFER_FILE


class Config:
    
    config = dotdict()
    _schema = {}
    
    @classmethod
    def init(cls, config_file, changelog_file, manual = False):
        cls.manual = manual
        cls.config_file = config_file
        cls.changelog_file = changelog_file
        
        with open(config_file, 'r') as file:
            config = yaml.full_load(file)
            state, schema = parse_config(config)
            
        if not os.path.exists(cls.changelog_file):
            open(cls.changelog_file, 'w').close()
            
        cls._tmp_dir = os.path.join(os.path.expanduser("~"), ".train_config/")
        if not os.path.exists(cls._tmp_dir):
            os.mkdir(cls._tmp_dir)
        
        cls.history = History(cls.changelog_file, init_config = state)

        cls._history_buffer = SQLiteBuffer(name = "history", file = HISTORY_BUFFER_FILE)
        cls._history_buffer.put(config)
        
        cls._form_buffer = SQLiteBuffer(name = "form", file = FORM_BUFFER_FILE)
        cls._form_buffer.put(config)
        
        cls.config = dotdict(state)
        cls._schema = schema

        atexit.register(_cleanup, cls._form_buffer, cls._history_buffer)

    @classmethod
    def update(cls):
        historic_state, is_updated_from_history = cls.history.get_next()
        if is_updated_from_history:
            historic_config = assemble_config(historic_state, cls._schema)
            cls._form_buffer.put(historic_config)
            cls._history_buffer.put(historic_config)
        elif cls.manual:
            manual_config = cls._history_buffer.get()
            manual_state, _ = parse_config(manual_config)        
            is_updated_manually = cls.history.probe(manual_state)
            if is_updated_manually:
                cls._form_buffer.put(manual_config)
                cls._history_buffer.put(manual_config)
                cls.history.update(manual_state)
                cls.history.commit()
        cls.config = dotdict(cls.history.state)
            
    @classmethod
    def __getattr__(cls, key):
        return cls.config[key]

    @classmethod
    def __setattr__(cls, key, value):
        cls.config[key] = value
        
    @classmethod
    def __repr__(cls):
        return str(cls.config.to_dict())


def _cleanup(fb, hb):
    fb.put({})
    hb.put({})
