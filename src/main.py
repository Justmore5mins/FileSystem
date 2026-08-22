from flask import Flask, Response, send_from_directory, redirect, g, request
from pathlib import Path
from werkzeug.datastructures.file_storage import FileStorage
from dotenv import load_dotenv
from os import environ
from pyotp import TOTP
import jwt
from jwt.exceptions import ExpiredSignatureError
from datetime import datetime, timedelta,UTC
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from platform import platform
from vercel.blob import BlobClient

if "macOS" in platform():
    load_dotenv(override=True)

BasePath: Path = Path(__file__).resolve().parent.parent

app = Flask(__name__, static_folder=None)
db = MongoClient(environ.get("Database"), server_api=ServerApi('1'))['data']['data']

@app.before_request
def doSomething():
    if 'api' in request.url and 'auth' not in request.url:
        token = request.cookies.get("Authorization")
        if not token:
            return Response(status=401)
        try:
            jwt.decode(token,environ.get("JWTSecret"), algorithms="HS256")
        except ExpiredSignatureError :
            return Response(status=401)
    else:
        return

@app.teardown_appcontext
def closeDatabase(exception=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


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

@app.route("/")
def main():
    return send_from_directory(BasePath / "public", "index.html")

@app.route("/style.css")
def style():
    return send_from_directory(BasePath / "public", "style.css")

@app.route("/script.js")
def script():
    return send_from_directory(BasePath / "public", "script.js")

@app.route("/<name>", methods=['GET'])
def getFile(name):
    result = db.find_one({"name":name})
    if not result:
        return Response(status=404)
    resType, content = result['type'], result['content']
    match(resType):
        case "blob":
            return redirect(content)
        case "url":
            return redirect(content)
        case _:
            return Response(status=404)
    

@app.route("/api/upload", methods=["POST"])
def uploadURL():
    name = request.form['name']
    if not db.find_one({"name":name}):
        try:
            content = request.form['content']
        except:
            try:
                content = request.files.get('content')
            except:
                return Response(status=206)
        if isinstance(content, FileStorage):
            filename = content.filename  or "upload"
            blob = BlobClient().put("files/{}".format(filename), content.stream.read(), access="public", content_type= content.mimetype or "application/octet-stream", add_random_suffix=True, overwrite=True)
            db.insert_one({"name":name, "type":"blob", "content":blob.url})
        elif isinstance(content, str):
            db.insert_one({"name":name, "type":"url","content":content})
        return redirect("/")
    else:
        return Response(status=406)
    
@app.route("/api/delete", methods=["POST"])
def deleteFile():
    res = db.find_one({"name":request.form['name']})
    if not res:
        return "File not found", 404
    contentType, content = res['type'], res['content']
    if contentType == "blob":
        BlobClient().delete(content)
    db.delete_one({"name":request.form['name']})
    return redirect("/")


@app.route("/api/auth", methods=["POST"])
def auth():
    code = request.form['code']
    sec = environ.get('OTPSecret')
    sec = sec if sec else ""
    if TOTP(sec).verify(code):
        res = redirect("/")
        data = jwt.encode({
            "exp": (datetime.now()+timedelta(minutes=10)).astimezone(tz=UTC)
        },key=environ.get("JWTSecret"),algorithm="HS256")
        res.set_cookie("Authorization",data)
        return res
    else:
        return Response(status=401)

@app.route("/api/getAll", methods=['GET'])
def getAll():
    return [{"name":k['name'], "type":k['type'], "content": k['content']} for k in db.find()]

if __name__ == "__main__":
    app.run("0.0.0.0", 80)
