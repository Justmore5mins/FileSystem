from flask import Flask, Response, send_from_directory, redirect, request, flash
from pathlib import Path
from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv
from os import environ
from pyotp import TOTP
import jwt
from jwt.exceptions import ExpiredSignatureError
from datetime import datetime, timedelta, UTC
from platform import platform
from huggingface_hub import HfApi,CommitOperationAdd
from typing import Final
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import requests

load_dotenv(override=True)

BasePath: Final[Path] = Path(__file__).resolve().parent.parent

app = Flask(__name__, static_folder=None)
db = MongoClient(environ['Database'], server_api=ServerApi('1'))['data']['data']
fs = HfApi(token=environ["HFToken"])
RepoURL = f"https://huggingface.co/datasets/{environ['HFRepo']}/"
app.secret_key = environ['JWTSecret']

@app.before_request
def doSomething():
    if 'api' in request.url and 'auth' not in request.url:
        token = request.cookies.get("Authorization")
        if not token:
            return Response(status=401)
        try:
            jwt.decode(token, environ['JWTSecret'], algorithms="HS256")
        except ExpiredSignatureError:
            return Response(status=401)
    else:
        return

@app.after_request
def addSecurity(res: Response):
    res.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; " 
        "style-src 'self' https://fonts.googleapis.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'self'; "
        "form-action 'self'; "
    )

    return res

@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400

@app.route("/")
def main():
    return send_from_directory(BasePath/"public", "index.html");

@app.route("/static/style.css")
def style():
    return send_from_directory(BasePath / "public", "style.css")

@app.route("/static/script.js")
def script():
    return send_from_directory(BasePath / "public", "script.js")

@app.route("/<path:name>", methods=['GET'])
def getFile(name):
    result = db.find_one({"name":name})
    if not result:
        return Response(status=404)

    match(result["type"]):
        case "file":
            r = requests.get(f"https://huggingface.co/datasets/{environ['HFRepo']}/resolve/main/{result['content']}",headers={"Authorization": f"Bearer {environ['HFToken']}"})
            r.raise_for_status()
            return Response(
                r.iter_content(chunk_size= 4 * 1024 * 1024), # n MB
                content_type=r.headers.get("Content-Type", "application/octet-stream"),
                headers={
                    "Content-Length": r.headers.get("Content-Length", "")
                },
            )
        case "url":
            return redirect(result['content'])
        case _:
            return Response(status=404)

@app.route('/api/upload', methods=["POST"])
def uploadURL():
    name = request.form['name']
    if not db.find_one({"name":name}):
        try:
            content = request.form['content']
        except:
            try:
                print(request.files['content'])
                content = request.files['content']
            except:
                return Response(status=406)
        if isinstance(content, FileStorage):
            cmt = CommitOperationAdd(f"{"/".join(name.split("/")[:-1])}/{content.filename}",content.stream.read()) # type: ignore

            inf = fs.create_commit(repo_id=environ["HFRepo"],
            repo_type="dataset",
            operations=[cmt],
            commit_message=f"Upload {content.filename}",
)
            db.insert_one({"name":name, "type":"file", "content":f"{"/".join(name.split("/")[:-1])}/{content.filename}"})
            return redirect("/") if inf else Response(status=500)
        elif isinstance(content, str):
            db.insert_one({"name":name, "type":"url", "content":content})
            return redirect('/')
        return redirect("/")
    else:
        return Response(status=206)

@app.route("/api/delete", methods=["POST"])
def deleteFile():
    res = db.find_one({"name":request.form['name']})
    if not res:
        return "File not found", 404
    if res['type'] == "file":
        fs.delete_file(res['content'],repo_id=environ["HFRepo"],repo_type="dataset")
    db.delete_one({"name":request.form['name']})
    return redirect("/")

@app.route('/api/auth', methods=["POST"])
def auth():

    if not TOTP( environ["OTPSecret"]).verify(request.form['code']):
        return Response(status=401)
    res = redirect("/")
    data = jwt.encode({
        "exp": (datetime.now()+timedelta(minutes=10)).astimezone(UTC)
    }, key=environ["JWTSecret"], algorithm="HS256") 
    res.set_cookie("Authorization", data, httponly=True, secure="macOS" in platform())
    return res

@app.route('/api/getAll', methods=['GET'])
def getAll():
    return [{"name":k['name'], "type":k['type'], "content": k['content']} for k in db.find()]

if __name__ == "__main__":
    app.run("0.0.0.0", 80, debug=True)