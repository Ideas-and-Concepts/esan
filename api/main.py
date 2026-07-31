from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Esan ERP API is running"}