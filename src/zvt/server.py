# -*- coding: utf-8 -*-
import uvicorn
from fastapi import FastAPI

from zvt.rest.data import data_router
from zvt.rest.work import work_router

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(data_router)
app.include_router(work_router)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", reload=True, port=8080)
