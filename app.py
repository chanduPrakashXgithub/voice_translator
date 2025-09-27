import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from pydub import AudioSegment
import speech_recognition as sr
from gtts import gTTS
from deep_translator import GoogleTranslator

UPLOAD_FOLDER = os.path.join('static', 'media')
ALLOWED_EXTENSIONS = {'webm', 'wav', 'ogg', 'mp3', 'm4a'}
MAX_CONTENT = 24 * 1024 * 1024

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    if 'file' not in request.files:
        return jsonify({'error': 'no file'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'empty filename'}), 400
    src = request.form.get('srcLang', 'auto')
    tgt = request.form.get('tgtLang', 'en')
    if f and allowed_file(f.filename):
        filename = secure_filename(str(uuid.uuid4()) + '_' + f.filename)
        saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(saved_path)
        base, ext = os.path.splitext(saved_path)
        wav_path = base + '.wav'
        try:
            audio = AudioSegment.from_file(saved_path)
            audio.export(wav_path, format='wav')
        except Exception as e:
            return jsonify({'error': 'audio conversion failed', 'detail': str(e)}), 500
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
        try:
            recognized = r.recognize_google(audio_data, language=None if src=='auto' else src)
        except Exception as e:
            recognized = ''
        try:
            translated = GoogleTranslator(source='auto' if src=='auto' else src, target=tgt).translate(recognized)
        except Exception as e:
            translated = ''
        tts_url = ''
        if translated:
            try:
                tts = gTTS(text=translated, lang=tgt)
                tts_filename = secure_filename(str(uuid.uuid4()) + '_tts.mp3')
                tts_path = os.path.join(app.config['UPLOAD_FOLDER'], tts_filename)
                tts.save(tts_path)
                tts_url = '/' + tts_path.replace('\\','/')
            except Exception as e:
                tts_url = ''
        return jsonify({'recognized_text': recognized, 'translated_text': translated, 'tts_url': tts_url})
    else:
        return jsonify({'error': 'file not allowed'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
