# ZVT REST API Specification (v0.13.3)

Base URL: `http://localhost:8090`

Authentication: None (CORS enabled; add auth upstream if required)

Content Type: JSON

Note: Response models reference Pydantic classes in the codebase; field names/types follow those models exactly.

## Data APIs (`/api/data`)

- GET `/api/data/providers`
  - Description: List configured data providers.
  - Response: `string[]`

- GET `/api/data/schemas?provider={provider}`
  - Description: List schema class names for a provider.
  - Response: `string[]`

- GET `/api/data/query_data?provider={provider}&schema={ClassName}`
  - Description: Return up to 100 rows for a schema from a provider.
  - Response: Array of objects (serialized ORM domain instances)

## Factor APIs (`/api/factor`)

- GET `/api/factor/get_factors`
  - Description: List registered factor class names.
  - Response: `string[]`

- POST `/api/factor/query_factor_result`
  - Description: Query factor-generated trading signals.
  - Request Body: `FactorRequestModel`
    - `factor_name`: string
    - `entity_ids?`: string[]
    - `data_provider`: string (default `em`)
    - `start_timestamp`: datetime (default: 1 year ago)
    - `level`: `IntervalLevel` (default `1d`)
  - Response: `TradingSignalModel[]`

## Trading APIs (`/api/trading`)

- POST `/api/trading/query_kdata`
  - Description: Query OHLCV data grouped by entity.
  - Request Body: `KdataRequestModel`
    - `entity_ids`: string[]
    - `data_provider`: string (default `em`)
    - `start_timestamp`: datetime (default ~500 days ago)
    - `end_timestamp?`: datetime
    - `level`: `IntervalLevel` (default `1d`)
    - `adjust_type`: `AdjustType` (default `qfq`)
  - Response: `KdataModel[]` (per entity: `code`, `name`, `level`, `datas` time-series rows)

- POST `/api/trading/query_ts`
  - Description: Query recent 1m tick series for entities (QMT provider).
  - Request Body: `TSRequestModel` (`entity_ids`, `data_provider`, `days_count`)
  - Response: `TSModel[]`

- GET `/api/trading/get_quote_stats`
  - Description: Market-wide intraday quote summary (A-shares).
  - Response: `QuoteStatsModel`

- GET `/api/trading/get_query_stock_quote_setting`
  - Description: Get stored admin query settings for stock quotes.
  - Response: `QueryStockQuoteSettingModel | null`

- POST `/api/trading/build_query_stock_quote_setting`
  - Description: Upsert admin query settings.
  - Request Body: `BuildQueryStockQuoteSettingModel`
  - Response: `QueryStockQuoteSettingModel`

- POST `/api/trading/query_tag_quotes`
  - Description: Aggregate quote stats by `main_tag` within a stock pool.
  - Request Body: `QueryTagQuoteModel`
  - Response: `TagQuoteStatsModel[]` (sorted by `turnover`/`total_count`)

- POST `/api/trading/query_stock_quotes`
  - Description: Quote list and summary for a pool or explicit entities; supports CN/US/HK.
  - Request Body: `QueryStockQuoteModel`
  - Response: `StockQuoteStatsModel | null` (includes `quotes` list)

- POST `/api/trading/build_trading_plan`
  - Description: Create or update a trading plan item.
  - Request Body: `BuildTradingPlanModel`
  - Response: `TradingPlanModel`

- POST `/api/trading/query_trading_plan`
  - Description: Paginated query of trading plans by time range.
  - Request Body: `QueryTradingPlanModel`
  - Response: `Page<TradingPlanModel>`

- GET `/api/trading/get_current_trading_plan`
  - Description: Plans with status `pending` ordered by date.
  - Response: `TradingPlanModel[]`

- GET `/api/trading/get_future_trading_plan`
  - Description: Plans with status `init` ordered by date.
  - Response: `TradingPlanModel[]`

- POST `/api/trading/buy`
  - Description: Place a buy order via QMT (Windows-only).
  - Request Body: `BuyParameter` (see `zvt.common.trading_models`)
  - Response: `TradingResult` or 500 error on non-Windows

- POST `/api/trading/sell`
  - Description: Place a sell order via QMT (Windows-only).
  - Request Body: `SellParameter`
  - Response: `TradingResult` or 500 error on non-Windows

## Work/Tag APIs (`/api/work`)

- POST `/api/work/create_stock_pool_info` → `StockPoolInfoModel`
- GET `/api/work/get_stock_pool_info` → `StockPoolInfoModel[]`
- POST `/api/work/create_stock_pools` → `StockPoolsModel`
- DELETE `/api/work/delete_stock_pool?stock_pool_name={name}` → `string`
- GET `/api/work/get_stock_pools?stock_pool_name={name}` → `StockPoolsModel | null`
- GET `/api/work/get_main_tag_info` → `TagInfoModel[]`
- GET `/api/work/get_sub_tag_info` → `TagInfoModel[]`
- GET `/api/work/get_main_tag_sub_tag_relation?main_tag={tag}` → `MainTagSubTagRelation`
- GET `/api/work/get_industry_info` → `IndustryInfoModel[]`
- GET `/api/work/get_main_tag_industry_relation?main_tag={tag}` → `MainTagIndustryRelation`
- GET `/api/work/get_hidden_tag_info` → `TagInfoModel[]`
- POST `/api/work/create_main_tag_info` → `TagInfoModel`
- DELETE `/api/work/delete_main_tag?tag={tag}` → `string`
- POST `/api/work/create_sub_tag_info` → `TagInfoModel`
- DELETE `/api/work/delete_sub_tag?tag={tag}` → `string`
- POST `/api/work/create_hidden_tag_info` → `TagInfoModel`
- DELETE `/api/work/delete_hidden_tag?tag={tag}` → `string`
- POST `/api/work/query_stock_tags` → `StockTagsModel[]`
- POST `/api/work/query_simple_stock_tags` → `SimpleStockTagsModel[]`
- GET `/api/work/get_stock_tag_options?entity_id={id}` → `StockTagOptions`
- POST `/api/work/set_stock_tags` → `StockTagsModel`
- POST `/api/work/build_stock_tags` → `StockTagsModel[]`
- POST `/api/work/query_stock_tag_stats` → `StockTagStatsModel[]`
- GET `/api/work/get_main_tags_in_stock_pool?stock_pool_name={name}` → `string[]`
- POST `/api/work/activate_sub_tags` → `ActivateSubTagsResultModel`
- POST `/api/work/batch_set_stock_tags` → `StockTagsModel[]`
- POST `/api/work/build_main_tag_industry_relation` → `string`
- POST `/api/work/build_main_tag_sub_tag_relation` → `string`
- POST `/api/work/change_main_tag` → `StockTagsModel[]`

## Operational Notes

- Pagination: `/api/trading/query_trading_plan` uses `fastapi-pagination` Page response.
- Time fields: many responses include `timestamp` as UNIX seconds or datetime strings depending on endpoint.
- Error handling: HTTP 4xx for validation (Pydantic) and 5xx for runtime issues; trading endpoints enforce OS checks.

