from flask import Flask, request, jsonify
import requests, threading

app = Flask(__name__)

BASE_URL = "https://mgmt-cdn.letseduvate.com/media/prod/ebook/39/20/2"

progress = {"current": 0, "total": 1, "status": "Idle"}
last_download = ""

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Eduvate Downloader</title>
<style>
body { font-family: Arial; background:#0f172a; color:white; padding:20px; }
.container { max-width:500px; margin:auto; background:#1e293b; padding:20px; border-radius:12px; }
input, select { width:100%; padding:10px; margin:8px 0; border-radius:6px; border:none; }
button { width:100%; padding:10px; background:#22c55e; border:none; color:white; border-radius:6px; }
#bar { background:#334155; height:20px; border-radius:10px; margin-top:10px; }
#progress { height:100%; width:0%; background:#22c55e; border-radius:10px; }
a { color:#38bdf8; display:block; margin-top:10px; }
</style>
</head>
<body>

<div class="container">
<h2>📚 Eduvate Downloader</h2>

<select id="class">
<option>G1</option>
</select>

<select id="subject">
<option value="Eng">English</option>
</select>

<input id="start" value="7163">
<input id="end" value="7166">

<button onclick="start()">Start</button>

<div id="bar"><div id="progress"></div></div>
<p id="status"></p>

<h3>Result</h3>
<div id="downloads"></div>

</div>

<script>
function start(){
    document.getElementById("downloads").innerHTML = "";

    fetch("/start", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
            start:document.getElementById("start").value,
            end:document.getElementById("end").value,
            class:document.getElementById("class").value,
            subject:document.getElementById("subject").value
        })
    });

    update();
}

function update(){
    fetch("/progress")
    .then(res=>res.json())
    .then(data=>{
        let percent = (data.current/data.total)*100;
        document.getElementById("progress").style.width = percent + "%";
        document.getElementById("status").innerText = data.status;

        if(percent < 100){
            setTimeout(update, 1000);
        } else {
            loadDownload();
        }
    });
}

function loadDownload(){
    fetch("/latest")
    .then(res=>res.json())
    .then(data=>{
        if(data.file){
            document.getElementById("downloads").innerHTML =
            `<a href="${data.file}" target="_blank">📄 Open Book</a>`;
        } else {
            document.getElementById("downloads").innerHTML =
            "❌ No book found";
        }
    });
}
</script>

</body>
</html>
"""

def is_valid(url):
    try:
        r = requests.get(url, timeout=3)
        return r.status_code == 200
    except:
        return False

def download_book(book_id, pattern):
    # return first working page link
    return f"{BASE_URL}/{book_id}/ebook_img/{pattern}_{book_id}_1.png"

def run_task(start_id, end_id, cls, subject):
    global progress, last_download

    patterns = [
        f"Textbook_{subject}_{cls}_T1_25-26",
        f"Workbook_{subject}_{cls}_V1_25-26"
    ]

    total = (end_id - start_id + 1) * len(patterns)
    progress["total"] = total
    progress["current"] = 0
    last_download = ""

    for book_id in range(start_id, end_id + 1):
        for pattern in patterns:
            test_url = f"{BASE_URL}/{book_id}/ebook_img/{pattern}_{book_id}_1.png"

            if is_valid(test_url):
                progress["status"] = f"✅ Found: {pattern} ({book_id})"
                last_download = download_book(book_id, pattern)
                progress["current"] = progress["total"]
                return

            progress["current"] += 1

    progress["status"] = "❌ No book found"

@app.route("/")
def home():
    return HTML

@app.route("/start", methods=["POST"])
def start():
    data = request.json

    threading.Thread(
        target=run_task,
        args=(int(data["start"]), int(data["end"]), data["class"], data["subject"])
    ).start()

    return jsonify({"status": "started"})

@app.route("/progress")
def prog():
    return jsonify(progress)

@app.route("/latest")
def latest():
    return jsonify({"file": last_download})

if __name__ == "__main__":
    app.run(debug=True)
