import hug
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from reciept_recog import process_files


@hug.get('/to_google')
def to_google():
    gauth = GoogleAuth()
    gauth.GetFlow()
    gauth.flow.redirect_uri = "http://localhost:8000/launch/"
    auth_url = gauth.GetAuthUrl()
    hug.redirect.to(auth_url)


@hug.get('/launch')
def launch(code: str):
    gauth = GoogleAuth()
    gauth.GetFlow()
    gauth.flow.redirect_uri = "http://localhost:8000/launch/"
    gauth.Auth(code)
    drive = GoogleDrive(gauth)
    process_files(drive)
    return "success"
