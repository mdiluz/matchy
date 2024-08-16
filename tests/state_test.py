"""
    Test functions for the state module
"""
import matchy.state as state
import tempfile
import os


def test_basic_state():
    """Simple validate basic state load"""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'tmp.json')
        state.load_from_file(path)


def test_simple_load_reload():
    """Test a basic load, save, reload"""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'tmp.json')
        st = state.load_from_file(path)
        state._save(st._file, st._dict)
        state._save(st._file, st._dict)

        st = state.load_from_file(path)
        state._save(st._file, st._dict)
        st = state.load_from_file(path)


def test_authscope():
    """Test setting and getting an auth scope"""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'tmp.json')
        st = state.load_from_file(path)
        state._save(st._file, st._dict)

        assert not st.get_user_has_scope(1, state.AuthScope.MATCHER)

        st = state.load_from_file(path)
        st.set_user_scope(1, state.AuthScope.MATCHER)
        state._save(st._file, st._dict)

        st = state.load_from_file(path)
        assert st.get_user_has_scope(1, state.AuthScope.MATCHER)

        st.set_user_scope(1, state.AuthScope.MATCHER, False)
        assert not st.get_user_has_scope(1, state.AuthScope.MATCHER)


def test_channeljoin():
    """Test setting and getting an active channel"""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'tmp.json')
        st = state.load_from_file(path)
        state._save(st._file, st._dict)

        assert not st.get_user_active_in_channel(1, "2")

        st = state.load_from_file(path)
        st.set_user_active_in_channel(1, "2", True)
        state._save(st._file, st._dict)

        st = state.load_from_file(path)
        assert st.get_user_active_in_channel(1, "2")

        st.set_user_active_in_channel(1, "2", False)
        assert not st.get_user_active_in_channel(1, "2")
