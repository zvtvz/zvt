# -*- coding: utf-8 -*-
import uvicorn
from fastapi import FastAPI
from fastapi_pagination import add_pagination

from zvt.rest.data import data_router
from zvt.rest.factor import factor_router
from zvt.rest.trading import trading_router
from zvt.rest.work import work_router
from fastapi.middleware.cors import CORSMiddleware

from zvt.sched.sched import zvt_scheduler

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(data_router)
app.include_router(factor_router)
app.include_router(work_router)
app.include_router(trading_router)

add_pagination(app)


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", reload=True, port=8090)
