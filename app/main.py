from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
# from app.whatsapp.webhook import router as whatsapp_router

app = FastAPI(title="ICMR STW WhatsApp Demo")

# app.include_router(whatsapp_router, prefix="/whatsapp")
verify: str = "icmr-stw-demo"

@app.get("/")
def root():
    return {"status": "ok", "service": "icmr-stw-whatsapp-demo"}

@app.get("/webhook-whatsapp")
def root(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == verify:
        return PlainTextResponse(content=hub_challenge, status_code=200)
    
    raise HTTPException(status_code=403, detail="Verification_Failed")    

@app.post("/webhook-whatsapp")
async def recieve_message(request: Request):
    print("POST /webhook-whatsapp CALLED")
    message = await request.json()
    print("Received message:", message)
    return {"status": "received", "message": message}