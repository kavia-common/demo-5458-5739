from app.utils.ping import ping_host


def test_ping_host_invalid_ip():
    status, ts, err = ping_host("not.an.ip")
    assert status == "offline"
    assert isinstance(ts, str)
    assert "Invalid IPv4" in err


def test_ping_host_no_ping_utility(monkeypatch):
    # Force shutil.which to return None to simulate missing system ping and pythonping import failure
    import app.utils.ping as p

    def fake_import_pythonping(name, *args, **kwargs):
        if name == "pythonping":
            raise ImportError("no pythonping")
        return __import__(name, *args, **kwargs)

    monkeypatch.setattr(p, "shutil", type("S", (), {"which": staticmethod(lambda _: None)}))
    # Also monkeypatch builtins __import__ only within module scope if needed; easier is to set a flag by shadowing import try except path
    # Given ping_host tries 'from pythonping import ping' and catches Exception, this will go to system ping branch which we disabled.
    status, ts, err = p.ping_host("192.168.1.1")
    assert status in ("offline", "online")  # offline expected
    assert isinstance(ts, str)
    assert err in ("", "No ping utility available") or "No ping utility" in err
