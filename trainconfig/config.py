import os
import atexit
import yaml

from dotdict import dotdict

from .changelog import Changelog
from .utils import parse_config, assemble_config
from .buffer import SQLiteBuffer, CHANGELOG_BUFFER_FILE, EDITOR_BUFFER_FILE, TMP_DIR


class ConfigProto:

    editable = True
    _config = dotdict()
    _changelog = None
    _schema = {}
    _changelog_buffer = None
    _editor_buffer = None
    
    @classmethod
    def init(cls, config_file: str, changelog_file: str, initial_step: int = 0, editable: bool = True):
        """
        Config setup method. Call it before usage.

        Parameters:
        :param config_file: path to the initial config YAML file.
        :param changelog_file: path to the changelog file, which stores all the manual config edits,
            done with the control panel
        :param initial_step: fast-forwards config values through the changelog to the given step
            Default: 0
        :param editable: if False, ignores all the manual changes and uses changelog only.
            Use it to prevent unwanted edits of the changelog. Default: True
        """
        assert initial_step >= 0, "Initial step must be >= 0"
        if not os.path.exists(TMP_DIR):
            os.mkdir(TMP_DIR)

        cls.editable = editable

        with open(config_file, 'r') as file:
            config = yaml.full_load(file)
            state, schema = parse_config(config)

        if not os.path.exists(changelog_file):
            open(changelog_file, 'w').close()

        cls._changelog = Changelog(changelog_file, init_config=state)
        if initial_step > 0:
            cls._changelog.rewind(initial_step)
            state = cls._changelog.state
            config = assemble_config(state, schema)

        cls._changelog_buffer = SQLiteBuffer(name="changelog", file=CHANGELOG_BUFFER_FILE).put(config, editable)
        cls._editor_buffer = SQLiteBuffer(name="editor", file=EDITOR_BUFFER_FILE).put(config, editable)
        cls._schema = schema
        cls._config = dotdict(state)

        atexit.register(cls.close)

    @classmethod
    def update(cls):
        """
        Refreshes config values: checks for the next step update from the changelog or
        from the control panel.
        """
        assert cls._changelog_buffer is not None, "Config is not set up. Run Config.init(...) first"
        changelog_state, is_updated_from_changelog = cls._changelog.get_next()
        if is_updated_from_changelog:
            changelog_config = assemble_config(changelog_state, cls._schema)
            cls._editor_buffer.put(changelog_config, cls.editable)
            cls._changelog_buffer.put(changelog_config, cls.editable)
        elif cls.editable:
            manual_config, _ = cls._changelog_buffer.get()
            manual_state, _ = parse_config(manual_config)        
            is_updated_manually = cls._changelog.probe(manual_state)
            if is_updated_manually:
                cls._editor_buffer.put(manual_config, cls.editable)
                cls._changelog_buffer.put(manual_config, cls.editable)
                cls._changelog.update(manual_state)
                # cls._changelog.commit()
        cls._config = dotdict(cls._changelog.state)

    @classmethod
    def close(cls):
        os.remove(CHANGELOG_BUFFER_FILE)
        os.remove(EDITOR_BUFFER_FILE)
            
    @classmethod
    def __getattr__(cls, key: str):
        return cls._config[key]

    @classmethod
    def __repr__(cls):
        return str(cls._config.to_dict())


Config = ConfigProto()
