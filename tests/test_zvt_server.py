import importlib.util
import sys
import types
from pathlib import Path
from unittest import mock


def test_main_uses_package_qualified_app_path():
    calls = []

    uvicorn = types.ModuleType("uvicorn")
    uvicorn.run = lambda *args, **kwargs: calls.append((args, kwargs))

    fastapi = types.ModuleType("fastapi")

    class FakeFastAPI:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def add_middleware(self, *args, **kwargs):
            return None

        def include_router(self, *args, **kwargs):
            return None

        def get(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    fastapi.FastAPI = FakeFastAPI

    cors_module = types.ModuleType("fastapi.middleware.cors")
    cors_module.CORSMiddleware = object

    responses_module = types.ModuleType("fastapi.responses")
    responses_module.ORJSONResponse = object

    pagination_module = types.ModuleType("fastapi_pagination")
    pagination_module.add_pagination = lambda app: None

    zvt_module = types.ModuleType("zvt")
    zvt_module.zvt_env = {"resource_path": "/tmp/resources"}

    data_module = types.ModuleType("zvt.rest.data")
    data_module.data_router = object()
    factor_module = types.ModuleType("zvt.rest.factor")
    factor_module.factor_router = object()
    misc_module = types.ModuleType("zvt.rest.misc")
    misc_module.misc_router = object()
    trading_module = types.ModuleType("zvt.rest.trading")
    trading_module.trading_router = object()
    work_module = types.ModuleType("zvt.rest.work")
    work_module.work_router = object()

    fake_modules = {
        "uvicorn": uvicorn,
        "fastapi": fastapi,
        "fastapi.middleware": types.ModuleType("fastapi.middleware"),
        "fastapi.middleware.cors": cors_module,
        "fastapi.responses": responses_module,
        "fastapi_pagination": pagination_module,
        "zvt": zvt_module,
        "zvt.rest": types.ModuleType("zvt.rest"),
        "zvt.rest.data": data_module,
        "zvt.rest.factor": factor_module,
        "zvt.rest.misc": misc_module,
        "zvt.rest.trading": trading_module,
        "zvt.rest.work": work_module,
    }

    module_path = Path(__file__).resolve().parents[1] / "src" / "zvt" / "zvt_server.py"
    spec = importlib.util.spec_from_file_location("zvt_server_under_test", module_path)
    module = importlib.util.module_from_spec(spec)

    with mock.patch.dict(sys.modules, fake_modules):
        assert spec.loader is not None
        spec.loader.exec_module(module)
        module.main()

    assert calls
    args, kwargs = calls[0]
    assert args[0] == "zvt.zvt_server:app"
    assert kwargs["reload"] is True
