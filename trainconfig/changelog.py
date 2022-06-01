import yaml
import logging
from copy import deepcopy

from .utils import dict_diff, deep_update

logger = logging.getLogger(__name__)


class Changelog:
    
    def __init__(self, path, init_config = None):
        self.counter = 0
        self.path = path
        
        with open(self.path) as file:
            self.history = yaml.safe_load(file)
            
        if not self.history:
            self.history = {self.counter: deepcopy(init_config)}
            self.state = deepcopy(init_config)
        else:
            self.state = deepcopy(self.history[0])
            
    def get_next(self):
        self.counter += 1
        if self.counter in self.history:
            updated = True
            diff = self.history[self.counter]
            self.state = deep_update(self.state, diff)
            logger.info(f"Config - Update: {diff}")
        else:
            updated = False
        return deepcopy(self.state), updated
    
    def rewind(self, step = 0):
        self.counter = 0
        self.state = deepcopy(self.history[self.counter])
        [self.get_next() for _ in range(step)]
    
    def probe(self, state):
        return bool(dict_diff(self.state, state))
        
    def update(self, state, step = None):
        step = self.counter if step is None else step
        diff = dict_diff(self.state, state)
        if diff:
            self.history[step] = diff
            logger.info(f"Config - Changelog update: {diff}")
            self.state = deepcopy(state)
            self._trim()
        return deepcopy(self.state), diff
        
    def commit(self):
        with open(self.path, 'w') as file:
            yaml.safe_dump(self.history, file)
            
    def _trim(self):
        warn = False
        for k in list(self.history.keys()):
            if k > self.counter:
                warn = True
                del self.history[k]
        if warn:
            logger.warning(f"Config history was overwritten after step {self.counter}")
