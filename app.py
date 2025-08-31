from flask import Flask, render_template, request, redirect, url_for
import os
import uuid
import pickle
import numpy as np
from gtts import gTTS
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Import sketch blueprint
from sketch import sketch_bp  
from chatbot_app import chatbot_bp
from cartoonify import cartoon_bp 

app = Flask(__name__)

# Register pencil sketch blueprint
app.register_blueprint(sketch_bp, url_prefix="/sketch")
app.register_blueprint(chatbot_bp,url_prefix="/chatbot_app")
app.register_blueprint(cartoon_bp,url_prefix="/cartoonify")
# ----------- Config ----------
MODEL_PATH = "models/model.keras"
TOKENIZER_PATH = "models/tokenizer1.pkl"
FEATURE_EXTRACTOR_PATH = "models/feature_extractor1.keras"
UPLOAD_FOLDER = "static/uploads"
AUDIO_FOLDER = "static/audio"
MAX_LENGTH = 34
IMG_SIZE = 224

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# ----------- Load Models ----------
caption_model = load_model(MODEL_PATH)
feature_extractor = load_model(FEATURE_EXTRACTOR_PATH)
with open(TOKENIZER_PATH, "rb") as f:
    tokenizer = pickle.load(f)


# ----------- Caption Generator ----------
def generate_caption(image_path):
    img = load_img(image_path, target_size=(IMG_SIZE, IMG_SIZE))
    img = img_to_array(img) / 255.0
    img = np.expand_dims(img, axis=0)
    image_features = feature_extractor.predict(img, verbose=0)

    in_text = "startseq"
    for _ in range(MAX_LENGTH):
        sequence = tokenizer.texts_to_sequences([in_text])[0]
        sequence = pad_sequences([sequence], maxlen=MAX_LENGTH)
        yhat = caption_model.predict([image_features, sequence], verbose=0)
        yhat_index = np.argmax(yhat)
        word = tokenizer.index_word.get(yhat_index, None)
        if word is None:
            break
        in_text += " " + word
        if word == "endseq":
            break
    return in_text.replace("startseq", "").replace("endseq", "").strip()


# ----------- Routes ----------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/caption", methods=["GET", "POST"])
def caption():
    uploaded_image = None
    caption = None
    audio_file = None

    if request.method == "POST":
        file = request.files.get("image")
        if file and file.filename != "":
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            uploaded_image = file.filename
            caption = generate_caption(filepath)

            # Generate speech
            tts = gTTS(text=caption, lang="en")
            audio_filename = f"{uuid.uuid4().hex}.mp3"
            audio_path = os.path.join(AUDIO_FOLDER, audio_filename)
            tts.save(audio_path)
            audio_file = audio_filename

    return render_template("caption.html",
                           uploaded_image=uploaded_image,
                           caption=caption,
                           audio_file=audio_file)


if __name__ == "__main__":
    app.run(debug=True)
