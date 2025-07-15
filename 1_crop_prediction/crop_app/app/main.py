from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.wsgi import WSGIMiddleware
import joblib
import numpy as np
# import urllib.parse
import os
from .dashApp.table import app as dash_app

app = FastAPI(title = "Crop Prediction")

# Mount static files.
app.mount(path = "/static", app = StaticFiles(directory = "app/static", html = True), name = "static")
app.mount(path = "/dashboard", app = WSGIMiddleware(dash_app.server), name = "dashboard")

# Jinja2 templates.
templates = Jinja2Templates(directory = "app/templates")

# Load models after creating paths.
# Get the folder, app, where this file, main.py, resides. 
cur_folder = os.path.dirname(os.path.realpath(__file__))

# Build the absolute path e.g., app/trained_models/___.pkl by passing the STEPS e.g. app -> trained_models -> ___.pkl.
XGB_MODEL_PATH = os.path.join(cur_folder, "trained_models", "xgb_model.pkl")
ENCODER_MODEL_PATH = os.path.join(cur_folder, "trained_models", "labelEncoder_model.pkl")

xgb_model = joblib.load(XGB_MODEL_PATH)
labelEndcoder_model = joblib.load(ENCODER_MODEL_PATH)

# fastAPI codes. The html form only executes the app.post(..) for taking input data FROM USER but it's the app.get(..) method
# which always execute to DISPLAY the prediction result.

# This get method at the end returns e.g. N and we put this N inside form as default value for N. To use a real value e.g. 85,
# either we can pass it here in the Query(default = 85) or we can pass it inside form by value="{{ N or 85 }}".
@app.get("/", response_class = HTMLResponse)
async def page( request: Request,
                prediction: str|None = Query(default = None),
                N: float             = Query(default = None),
                P: float             = Query(default = None),
                K: float             = Query(default = None),
                temperature: float   = Query(default = None),
                humidity: float      = Query(default = None),
                ph: float            = Query(default = None),
                rainfall: float      = Query(default = None) ):
    
    return templates.TemplateResponse(name    = "index.html",
                                      context = {"request"      : request,
                                                 "prediction"   : prediction,
                                                 "N"            : N,
                                                 "P"            : P,
                                                 "K"            : K,
                                                 "temperature"  : temperature,
                                                 "humidity"     : humidity,
                                                 "ph"           : ph,
                                                 "rainfall"     : rainfall})

@app.post("/", response_class = RedirectResponse)
async def predict(request: Request,
                  N: float           = Form(...),
                  P: float           = Form(...),
                  K: float           = Form(...),
                  temperature: float = Form(...),
                  humidity: float    = Form(...),
                  ph: float          = Form(...),
                  rainfall: float    = Form(...)):
    
    input = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
    predicted_crop_no = xgb_model.predict(input) # crop_no, not crop_name since the output column is categorical number.
    predicted_crop_name = labelEndcoder_model.inverse_transform(predicted_crop_no)[0] # corresponding crop_name.

    # encoded_crop = urllib.parse.quote(predicted_crop_name) # It converts characters not allowed to have special meanings in URLs (like spaces, &, =, etc.)

    return RedirectResponse(url=f"/?request={request.method}&prediction={predicted_crop_name}&N={N}&P={P}&K={K}&temperature={temperature}&humidity={humidity}&ph={ph}&rainfall={rainfall}",
                            status_code = 303)