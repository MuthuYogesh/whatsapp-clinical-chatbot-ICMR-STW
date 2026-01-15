from fastapi import FastAPI
from app.whatsapp.webhook import router as whatsapp_router
import socket

app = FastAPI(title="ICMR STW WhatsApp Demo")

# Register routers (like app.use() in Express)
app.include_router(whatsapp_router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "icmr-stw-whatsapp-demo"
    }

@app.get("/debug-dns")
def check_dns():
    try:
        # Tries to find the 'address' for the Facebook API
        return {"ip": socket.gethostbyname("graph.facebook.com")}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/debug-dns1")
def check_dns():
    try:
        # Tries to find the 'address' for the Facebook API
        return {"ip": socket.gethostbyname("google.com")}
    except Exception as e:
        return {"error": str(e)}