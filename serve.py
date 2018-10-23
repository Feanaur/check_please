import hug
import trio
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from reciept_recog import fns_process_files, fns_check


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
    trio.run(fns_process_files, drive)
    return "success"


@hug.get('/get_data_from_fns')
def get_data_from_fns(qr_code: str):
    return fns_check(qr_code)
