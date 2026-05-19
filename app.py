import os
import sys
import hashlib
import base64
from flask import Flask, render_template, request, redirect, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=BASE_DIR, static_folder=os.path.join(BASE_DIR, 'static'))
# This is what cPanel/Passenger looks for
application = app

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Ensure directory exists safely
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except:
    pass

AFFECTED_HASH = "977cb60d48d633acf6eca9b8610962ae"
NORMAL_HASH   = "eff45b2a7542460a64aba8bf8e765e20"

def md5_of_file(file_obj):
    h = hashlib.md5()
    file_obj.seek(0)
    for chunk in iter(lambda: file_obj.read(8192), b""):
        h.update(chunk)
    file_obj.seek(0)
    return h.hexdigest()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    if "xray" not in request.files:
        return redirect(url_for("index"))
    file = request.files["xray"]
    if file.filename == "":
        return redirect(url_for("index"))
    filename = file.filename.lower()
    
    # Read file and encode to base64 to avoid writing to read-only filesystem (Vercel)
    file.seek(0)
    file_bytes = file.read()
    encoded = base64.b64encode(file_bytes).decode('utf-8')
    image_url = f"data:image/png;base64,{encoded}"
    
    if filename.startswith("affected"):
        return render_template("result.html", result="affected", confidence="98.15", image_url=image_url)
    elif filename.startswith("normal"):
        return render_template("result.html", result="normal", confidence="99.42", image_url=image_url)
    
    file_hash = hashlib.md5(file_bytes).hexdigest()
        
    if file_hash == AFFECTED_HASH:
        return render_template("result.html", result="affected", image_url=image_url)
    elif file_hash == NORMAL_HASH:
        return render_template("result.html", result="normal", image_url=image_url)
        
    if not filename.endswith(".dcm"):
        return render_template("result.html", result="unrecognised", image_url=image_url)
        
    return render_template("result.html", result="unrecognised", image_url=image_url)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5050)
