import importlib.util
import pathlib
import sys
import types


class _FakeFastAPI:
    def __init__(self, *args, **kwargs):
        self.routes = []
        self.routers = []

    def add_middleware(self, *args, **kwargs):
        return None

    def get(self, route):
        def decorator(func):
            self.routes.append((route, func))
            return func

        return decorator

    def include_router(self, router):
        self.routers.append(router)


def _load_module(monkeypatch):
    fake_uvicorn = types.SimpleNamespace(run=lambda *args, **kwargs: None)
    fake_fastapi = types.ModuleType("fastapi")
    fake_fastapi.FastAPI = _FakeFastAPI
    fake_cors = types.ModuleType("fastapi.middleware.cors")
    fake_cors.CORSMiddleware = object
    fake_responses = types.ModuleType("fastapi.responses")
    fake_responses.ORJSONResponse = object
    fake_pagination = types.ModuleType("fastapi_pagination")
    fake_pagination.add_pagination = lambda app: None

    fake_zvt = types.ModuleType("zvt")
    fake_zvt.zvt_env = {"resource_path": "/tmp/resources"}
    fake_rest = types.ModuleType("zvt.rest")
    fake_data = types.ModuleType("zvt.rest.data")
    fake_data.data_router = object()
    fake_factor = types.ModuleType("zvt.rest.factor")
    fake_factor.factor_router = object()
    fake_misc = types.ModuleType("zvt.rest.misc")
    fake_misc.misc_router = object()
    fake_trading = types.ModuleType("zvt.rest.trading")
    fake_trading.trading_router = object()
    fake_work = types.ModuleType("zvt.rest.work")
    fake_work.work_router = object()

    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)
    monkeypatch.setitem(sys.modules, "fastapi", fake_fastapi)
    monkeypatch.setitem(sys.modules, "fastapi.middleware.cors", fake_cors)
    monkeypatch.setitem(sys.modules, "fastapi.responses", fake_responses)
    monkeypatch.setitem(sys.modules, "fastapi_pagination", fake_pagination)
    monkeypatch.setitem(sys.modules, "zvt", fake_zvt)
    monkeypatch.setitem(sys.modules, "zvt.rest", fake_rest)
    monkeypatch.setitem(sys.modules, "zvt.rest.data", fake_data)
    monkeypatch.setitem(sys.modules, "zvt.rest.factor", fake_factor)
    monkeypatch.setitem(sys.modules, "zvt.rest.misc", fake_misc)
    monkeypatch.setitem(sys.modules, "zvt.rest.trading", fake_trading)
    monkeypatch.setitem(sys.modules, "zvt.rest.work", fake_work)

    module_path = pathlib.Path(__file__).resolve().parents[1] / "src" / "zvt" / "zvt_server.py"
    spec = importlib.util.spec_from_file_location("zvt.zvt_server", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, fake_uvicorn


def test_main_uses_package_qualified_app_path(monkeypatch):
    module, fake_uvicorn = _load_module(monkeypatch)
    recorded = {}

    def fake_run(app_path, **kwargs):
        recorded["app_path"] = app_path
        recorded["kwargs"] = kwargs

    fake_uvicorn.run = fake_run

    module.main()

    assert recorded["app_path"] == "zvt.zvt_server:app"
    assert recorded["kwargs"]["reload"] is True
