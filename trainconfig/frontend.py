import os
import ast
import copy

import streamlit as st
try:
    from streamlit.script_run_context import get_script_run_ctx
except ModuleNotFoundError:
    from streamlit.report_thread import get_report_ctx as get_script_run_ctx
    
from trainconfig.buffer import SQLiteBuffer, CHANGELOG_BUFFER_FILE, EDITOR_BUFFER_FILE


CSS = """
.stTextInput>label {
    font-size: 0px;
    min-height: 0px;
    margin-bottom: 0px
}
input[class] { 
    padding-bottom: 0px;
    padding-top: 0px;
    padding-left: 8px;
    padding-right: 8px;
}
div[data-baseweb="input"] {
    border-bottom-width: 0px;
    border-top-width: 0px;
    border-left-width: 0px;
    border-right-width: 0px;
}
div[data-testid="stVerticalBlock"] {
    row-gap: 2px;
    width: fit-content;
}
div[data-testid="stMarkdownContainer"] {
    word-wrap: break-word;
    width: fit-content
}
"""


def cast(s):
    try:
        return ast.literal_eval(str(s))
    except:
        return s


def install_watcher(file):
    ctx = get_script_run_ctx()
    session_id = ctx.session_id
    server = st.server.server.Server.get_current()
    session_info = server._session_info_by_id.get(session_id)
    session = session_info.session
    session._local_sources_watcher._register_watcher(os.path.abspath(file), f'tmp:{file}')
    
    
def init():
    install_watcher(EDITOR_BUFFER_FILE)
    st.markdown(f'<style>{CSS}</style>', unsafe_allow_html = True)
    st.session_state.setdefault('changelog_buffer', SQLiteBuffer(name = 'changelog', file = CHANGELOG_BUFFER_FILE))
    st.session_state.setdefault('editor_buffer', SQLiteBuffer(name = 'editor', file = EDITOR_BUFFER_FILE))
    
    
def build_key_map(config):
    
    def _crawl(sub_config, path):
        item_iter = sub_config.items() if isinstance(sub_config, dict) else enumerate(sub_config)
        for k, v in item_iter:
            path_update = path + [k]
            if isinstance(v, dict) or isinstance(v, list) or isinstance(v, tuple):
                sub_config[k] = {
                    "_type": type(v).__name__, 
                    "_value": _crawl(v, path_update), 
                    "_path": path_update
                }
            else:
                sub_config[k] = {
                    "_type": "item", 
                    "_value": v, 
                    "_path": path_update
                }
        return sub_config
       
    return {
        "_type": "dict",
        "_value": _crawl(config, []),
        "_path": []
    }


def unroll_key_map(key_map):
    output = {}
    
    def _crawl(sub_item):
        sub_type = sub_item['_type']
        if sub_type == 'item':
            key = '_'.join(map(str, sub_item['_path']))
            output[key] = (sub_item['_value'], sub_item['_path'])
        else:
            sub_value = sub_item['_value']
            item_iter = sub_value.items() if sub_type == 'dict' else enumerate(sub_value)
            for k, v in item_iter:
                _crawl(v)
    
    _crawl(key_map)
    return output


def auto_component(parent, value, key, disabled):
    if isinstance(value, bool):
        parent.checkbox(label = "", value = value, key = key, disabled = disabled)
    else:
        parent.text_input(label = "", value = value, key = key, disabled = disabled)
    
    
def build_layout(key_map, editable):
    
    def sort_key(x):
        return 1 if x[1]['_type'] == 'dict' else \
               2 if x[1]['_type'] in {'list', 'tuple'} else \
               0
    
    def _crawl(sub_item, readonly):
        sub_t, sub_v, sub_p = sub_item['_type'], sub_item['_value'], sub_item['_path']
        if sub_t == 'dict':
            item_iter = sorted(sub_v.items(), key = sort_key)
        elif sub_t in {'list', 'tuple'}:
            item_iter = enumerate(sub_v)
        else:
            raise TypeError(f"Attempting to unroll a integral type `{sub_t}`")

        depth = len(sub_p)
        for key, item in item_iter:
            if isinstance(key, str) and key.endswith('!'):
                disabled = True
                key = key[:-1]
            else:
                disabled = readonly
                
            label, field = st.columns([1,2])
            tab = "".join(["&nbsp;"]*(8*depth))
            if item['_type'] == 'item':
                label.markdown(f"{tab}{key}&nbsp;:")
                field_key = '_'.join(map(str, item['_path']))
                auto_component(parent = field, value = item['_value'], key = field_key, disabled = disabled)
            else:
                label.markdown(f"{tab}**+&nbsp;{key}&nbsp;:**")
                _crawl(item, disabled)

    return _crawl(key_map, not editable)


def get_sub_item(config, path):
    sub_item = config
    for k in path:
        sub_item = sub_item[k]
    return sub_item


def main():
    try:
        init()
    except FileNotFoundError:
        st.write("No connection to the config manager. Run Config.init() in your app and reload this page.")
        return

    input_cfg, editable = st.session_state.editor_buffer.get()
    if input_cfg is None:
        input_cfg = {}

    key_map = build_key_map(copy.deepcopy(input_cfg))
    unrolled_key_map = unroll_key_map(key_map)

    build_layout(key_map, editable)

    output_cfg = copy.deepcopy(input_cfg)
    for key, (value, path) in unrolled_key_map.items():
        if key not in st.session_state:
            continue
        sub_cfg = get_sub_item(output_cfg, path[:-1])
        sub_cfg[path[-1]] = cast(st.session_state[key])

    st.session_state.changelog_buffer.put(output_cfg, editable)


if __name__ == "__main__":
    main()
