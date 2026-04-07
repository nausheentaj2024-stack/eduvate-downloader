from flask import Flask, request, jsonify
import requests, threading

app = Flask(__name__)

BASE_URL = "https://mgmt-cdn.letseduvate.com/media/prod/ebook/39/20/2"

progress = {"current": 0, "total": 1, "status": "Idle"}
found_books = []

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Eduvate Multi Book Finder</title>
<style>
body { font-family: Arial; background:#0f172a; color:white; padding:20px; }
.container { max-width:600px; margin:auto; background:#1e293b; padding:20px; border-radius:12px; }
input, select { width:100%; padding:10px; margin:8px 0; border-radius:6px; border:none; }
button { width:100%; padding:10px; background:#22c55e; border:none; color:white; border-radius:6px; }
#bar { background:#334155; height:20px; border-radius:10px; margin-top:10px; }
#progress { height:100%; width:0%; background:#22c55e; border-radius:10px; }
a { color:#38bdf8; display:block; margin-top:10px; }
</style>
</head>
<body>

<div class="container">
<h2>📚 Eduvate Book Finder</h2>

<label>Subject</label>
<select id="subject">
<option value="Eng">English</option>
<option value="Math">Math</option>
<option value="EVS">EVS</option>
</select>

<input id="start" value="7160" placeholder="Start ID">
<input id="end" value="7200" placeholder="End ID">

<button onclick="start()">Find Books</button>

<div id="bar"><div id="progress"></div></div>
<p id="status"></p>

<h3>Books Found</h3>
<div id="results"></div>

</div>

<script>
function start(){
    document.getElementById("results").innerHTML = "";

    fetch("/start", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
            start:document.getElementById("start").value,
            end:document.getElementById("end").value,
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
            loadResults();
        }
    });
}

function loadResults(){
    fetch("/results")
    .then(res=>res.json())
    .then(data=>{
        let html = "";
        data.forEach(link=>{
            html += `<a href="${link}" target="_blank">📄 Open Book</a>`;
        });

        if(html === ""){
            html = "❌ No books found";
        }

        document.getElementById("results").innerHTML = html;
    });
}
</script>

</body>
</html>
"""

def is_valid(url):
    try:
        return requests.get(url, timeout=3).status_code == 200
    except:
        return False

def run_task(start_id, end_id, subject):
    global progress, found_books

    found_books = []

    patterns = [
        f"Textbook_{subject}_G1_T1_25-26",
        f"Textbook_{subject}_G1_T2_25-26",
        f"Workbook_{subject}_G1_V1_25-26",
        f"Workbook_{subject}_G1_V2_25-26"
    ]

    total = (end_id - start_id + 1) * len(patterns)
    progress["total"] = total
    progress["current"] = 0

    for book_id in range(start_id, end_id + 1):
        for pattern in patterns:
            url = f"{BASE_URL}/{book_id}/ebook_img/{pattern}_{book_id}_1.png"

            if is_valid(url):
                found_books.append(url)
                progress["status"] = f"Found: {pattern} ({book_id})"

            progress["current"] += 1

    progress["status"] = "✅ Done"

@app.route("/")
def home():
    return HTML

@app.route("/start", methods=["POST"])
def start():
    data = request.json

    threading.Thread(
        target=run_task,
        args=(int(data["start"]), int(data["end"]), data["subject"])
    ).start()

    return jsonify({"status": "started"})

@app.route("/progress")
def prog():
    return jsonify(progress)

@app.route("/results")
def results():
    return jsonify(found_books)

if __name__ == "__main__":
    app.run(debug=True)
