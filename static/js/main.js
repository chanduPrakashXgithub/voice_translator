let recordBtn = document.getElementById('recordBtn');
let stopBtn = document.getElementById('stopBtn');
let sendBtn = document.getElementById('sendBtn');
let recognizedDiv = document.getElementById('recognized');
let translatedDiv = document.getElementById('translated');
let player = document.getElementById('player');
let srcLang = document.getElementById('srcLang');
let tgtLang = document.getElementById('tgtLang');

let mediaRecorder; let audioChunks = [];

recordBtn.addEventListener('click', async ()=>{
  audioChunks = [];
  recognizedDiv.textContent = 'Listening...';
  try{
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => {
      if(e.data && e.data.size>0) audioChunks.push(e.data);
    };
    mediaRecorder.onstop = () => {
      sendBtn.disabled = false;
    };
    mediaRecorder.start();
    recordBtn.disabled = true;
    stopBtn.disabled = false;
  }catch(e){
    recognizedDiv.textContent = 'Mic error: ' + e.message;
  }
});

stopBtn.addEventListener('click', ()=>{
  if(mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    recordBtn.disabled = false;
    stopBtn.disabled = true;
    recognizedDiv.textContent = 'Recording stopped. Click Translate.';
  }
});

sendBtn.addEventListener('click', async ()=>{
  sendBtn.disabled = true;
  recognizedDiv.textContent = 'Uploading...';
  translatedDiv.textContent = '—';
  if(audioChunks.length === 0){
    recognizedDiv.textContent = 'No audio recorded.';
    sendBtn.disabled = false;
    return;
  }
  const blob = new Blob(audioChunks, {type: 'audio/webm'});
  const fd = new FormData();
  fd.append('file', blob, 'speech.webm');
  fd.append('srcLang', srcLang.value);
  fd.append('tgtLang', tgtLang.value);
  try{
    const resp = await fetch('/translate', {method:'POST', body: fd});
    const data = await resp.json();
    if(data.error){
      recognizedDiv.textContent = 'Error: ' + (data.detail || data.error);
      sendBtn.disabled = false;
      return;
    }
    recognizedDiv.textContent = data.recognized_text || '—';
    translatedDiv.textContent = data.translated_text || '—';
    if(data.tts_url){
      player.src = data.tts_url;
      player.style.display = 'block';
      try { await player.play(); } catch(e){}
    } else {
      player.style.display = 'none';
    }
  }catch(e){
    recognizedDiv.textContent = 'Network error: ' + e.message;
  }finally{
    sendBtn.disabled = false;
  }
});
