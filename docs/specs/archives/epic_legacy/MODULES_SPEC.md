# ZVT Module Specifications (v0.13.3)

This document maps major packages under `src/zvt` to their responsibilities and primary extension points.

## Core Contracts (`zvt.contract`)

- `schema.py`: Base ORM mixins and domain schema contracts (e.g., `Mixin`, `TradableEntity`).
- `api.py`: DB/session helpers, query/record interfaces, provider/schema registry.
- `reader.py`: `DataReader` with windowed, multi-indexed data loading.
- `recorder.py`: Recording framework (ingestion), provider registration and lifecycle.
- `factor.py`: Factor engine primitives (`Transformer`, `Accumulator`, `Factor`) and factor state persistence.
- `register.py`: Registration utilities for schema, provider, recorder, factor.
- `zvt_info.py`: State schemas (e.g., `FactorState`).
- `drawer.py`: Plot/visualization helpers used by UI.
- `data_type.py`, `model.py`, `utils.py`: Types, common model helpers, shared utilities.

Extension points:
- Add new providers by implementing recorders and registering in `provider_map_recorder`.
- Implement custom `Transformer`/`Accumulator`/`Factor` classes; registered via `FactorMeta`.

## Domain Schemas (`zvt.domain`)

- Market-specific entity/event models for CN/HK/US markets.
- Meta entities (stocks, indices, ETFs, funds) and event schemas (quotes, kdata, finance, actors, dividends, etc.).
- Uniform query/record API: each schema exposes `record_data` and `query_data`.

## Recorders (`zvt.recorders`)

- Data ingestion from third-party providers: EastMoney, EM API, JoinQuant, QMT, Exchange.
- One recorder per data type/provider; adheres to recorder lifecycle.
- Scheduling examples in `examples/data_runner` and under `src/zvt/tasks`.

## Factors (`zvt.factors`)

- Built-in technical and fundamental factors, transformers, and services.
- `factor_models.py`: Pydantic models for factor requests/responses.
- `factor_service.py`: Factor query APIs used by REST.

## Trading (`zvt.trader`, `zvt.trading`)

- `zvt.trader`: Strategy framework, base trader, signal types, backtesting mechanics.
- `zvt.trading`: REST-facing service layer for quotes, kdata, plans; Pydantic models and SQL-backed schemas.

## Tagging (`zvt.tag`)

- Tag schemas and services for main/sub/hidden tag systems, stock pools, and relations.
- Supports workflows for manual and automated tagging and activation.

## UI (`zvt.ui` and Dash app)

- Dash application (`zvt.main`) providing research/backtest UI.
- `ui/apps/factor_app.py` and helpers render factor and trading visualizations.

## REST (`zvt.rest`)

- FastAPI routers for data (`data.py`), factor (`factor.py`), trading (`trading.py`), and work/tag (`work.py`).
- Server entrypoint `zvt_server.py` runs at port `8090` with CORS, ORJSON, and pagination.

## Common/Utils (`zvt.common`, `zvt.utils`)

- Shared query models, trading types, helper utilities: time, pandas, strings, logging.

## Miscellaneous

- `plugin.py`: CLI tooling to generate plugin templates and export API surface (`zvt_export`).
- `fill_project.py`: Project bootstrapping helpers.
- `tasks/`: Runners to initialize tag system, stock pools, and QMT data ingestion.

## Console Commands

- `zvt`: Launch Dash UI on `0.0.0.0:8050`.
- `zvt_server`: Launch REST API server on `0.0.0.0:8090`.
- `zvt_export`: Generate export files (autocode support).

