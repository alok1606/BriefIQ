import json

from scripts import start_free_gateway as gateway


def test_gateway_requires_key(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gateway, "__file__", str(tmp_path / "scripts/start_free_gateway.py"))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert gateway.main() == 2
    assert "Save your Google" in capsys.readouterr().out
    assert not (tmp_path / ".bifrost-free").exists()


def test_gateway_keeps_key_out_of_files_and_arguments(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gateway, "__file__", str(tmp_path / "scripts/start_free_gateway.py"))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    secret = "test-key-never-write-to-config"
    (tmp_path / ".env").write_text("GEMINI_API_KEY=" + secret)
    monkeypatch.setattr(gateway.shutil, "which", lambda name: "npx.cmd")
    monkeypatch.setattr(gateway, "available_port", lambda preferred: 8787)
    calls = []
    def launch(command, **kwargs):
        calls.append((command, kwargs))
        return 0
    monkeypatch.setattr(gateway.subprocess, "call", launch)
    assert gateway.main() == 0
    command, kwargs = calls[0]
    assert kwargs["env"]["GEMINI_API_KEY"] == secret
    assert secret not in str(command)
    config_text = (tmp_path / ".bifrost-free/config.json").read_text()
    assert secret not in config_text and secret not in capsys.readouterr().out
    config = json.loads(config_text)
    assert list(config["providers"]) == ["gemini"]
    assert config["providers"]["gemini"]["keys"][0]["models"] == ["gemini-3.5-flash-lite"]
    assert command[command.index("-host") + 1] == "127.0.0.1"
    assert command[command.index("-port") + 1] == "8787"
    assert config["config_store"]["enabled"] is True
    virtual_key = kwargs["env"]["BIFROST_VIRTUAL_KEY"]
    assert virtual_key.startswith("sk-bf-")
    assert virtual_key not in config_text and virtual_key not in str(command)
    assert config["client"]["enforce_auth_on_inference"] is True
    assert config["governance"]["virtual_keys"][0]["provider_configs"][0]["allowed_models"] == ["gemini-3.5-flash-lite"]
    assert "http://127.0.0.1:8787" in (tmp_path / ".env").read_text()


def test_reserved_port_falls_back(monkeypatch):
    tried = []
    class Listener:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def setsockopt(self, *args):
            pass
        def bind(self, address):
            tried.append(address)
            if address[1] == 8080:
                raise PermissionError("Windows reserved port")
    monkeypatch.setattr(gateway.socket, "socket", lambda *args: Listener())
    assert gateway.available_port(8080) == 8787
    assert tried == [("127.0.0.1", 8080), ("127.0.0.1", 8787)]
