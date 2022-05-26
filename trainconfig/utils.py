import re
from copy import deepcopy


def is_composite(val):
    return (isinstance(val, dict) or isinstance(val, list) or isinstance(val, tuple))


def dictify(val):
    if isinstance(val, list) or isinstance(val, tuple):
        val = dict(enumerate(val))
    return val


def dict_diff(lval, rval):
    
    def _crawl(prev, new, output):
        prev = dictify(prev)
        new = dictify(new)
        for k in new:
            if k in prev:
                if is_composite(prev[k]) and is_composite(new[k]):
                    d = _crawl(prev[k], new[k], {})
                    if d:
                        output[k] = d
                elif prev[k] != new[k]:
                    output[k] = new[k]
            else:
                output[k] = new[k]
        return output
            
    return _crawl(lval, rval, {})


def deep_update(state, update):
    output = deepcopy(state)
    
    def _crawl(d, upd):
        upd = dictify(upd)
        for k, v in upd.items():
            if k in d and is_composite(d[k]):
                _crawl(d[k], v)
            else:
                d[k] = v
                
    _crawl(output, update)
    return output


def parse_config(cfg):
    
    def _crawl(sub, state_sub, schema_sub):
        if isinstance(sub, dict):
            for k, v in sub.items():
                key = re.findall("\w+", k)[0]
                dtype = re.findall('\[.+\]\!*|\!', k)
                dtype = dtype[0] if dtype else ''
                if isinstance(v, dict):
                    state_sub[key] = {}
                    schema_sub[key] = (dtype, {})
                    _crawl(v, state_sub[key], schema_sub[key][1])
                elif isinstance(v, list):
                    state_sub[key] = []
                    schema_sub[key] = (dtype, [])
                    _crawl(v, state_sub[key], schema_sub[key][1])
                else:
                    state_sub[key] = v
                    schema_sub[key] = (dtype, None)
        else:
            for v in sub:
                if isinstance(v, dict):
                    state_sub.append({})
                    schema_sub.append({})
                    _crawl(v, state_sub[-1], schema_sub[-1])
                elif isinstance(v, list):
                    state_sub.append([])
                    schema_sub.append([])
                    _crawl(v, state_sub[-1], schema_sub[-1])
                else:
                    state_sub.append(v)
                    schema_sub.append(None)
    
    state = {}
    schema = {}
    _crawl(cfg, state, schema)
    return state, schema


def assemble_config(state, schema):
    
    def _crawl(state_sub, schema_sub, sub):
        if isinstance(sub, dict):
            for k in state_sub:
                key = k + schema_sub[k][0]
                if isinstance(state_sub[k], dict):
                    sub[key] = {}
                    _crawl(state_sub[k], schema_sub[k][1], sub[key])
                elif isinstance(state_sub[k], list):
                    sub[key] = []
                    _crawl(state_sub[k], schema_sub[k][1], sub[key])
                else:
                    sub[key] = state_sub[k]
        else:
            for v, s in zip(state_sub, schema_sub):
                if isinstance(v, dict):
                    sub.append({})
                    _crawl(v, s, sub[-1])
                elif isinstance(v, list):
                    sub.append([])
                    _crawl(v, s, sub[-1])
                else:
                    sub.append(v)
    
    cfg = {}
    _crawl(state, schema, cfg)
    return cfg

