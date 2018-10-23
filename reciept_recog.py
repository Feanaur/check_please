import os
import cv2
import re
import pytesseract
import requests
import trio
import pyzbar.pyzbar as pyzbar
from PIL import Image


def get_file_list(drive):
    parent = drive.ListFile({'q': "title = 'Чеки'"}).GetList()
    file_list = None
    if parent:
        parent = parent[0]
        file_list = drive.ListFile({'q': "'{}' in parents and trashed=false and starred=false and mimeType != 'text/plain'".format(parent.get("id"))}).GetList()
    return parent, file_list


def process_file(drive):
    parent, file_list = get_file_list(drive)
    original_file_name = file.get("title")
    file.GetContentFile(original_file_name)
    image = cv2.imread(original_file_name)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 1)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    filename = "{}.png".format(os.getpid())
    cv2.imwrite(filename, gray)

    text = pytesseract.image_to_string(Image.open(filename), lang="eng+rus")
    text_filename = "{}.txt".format(original_file_name.split(".jpg")[0])
    text_file = drive.CreateFile(
        {
            'title': text_filename,
            'parents': [
                parent
            ],
            'mimeType': 'text/plain'
        }
    )
    text_file.SetContentString(text)
    text_file.Upload()

    os.remove(original_file_name)
    os.remove(filename)
    file["labels"] = {'starred': True, 'hidden': False, 'trashed': False, 'restricted': False, 'viewed': True}
    file.Upload()


async def create_text_file(drive, parent, file, original_file_name, text):
    text_filename = "{}.txt".format(original_file_name.split(".jpg")[0])
    text_file = drive.CreateFile(
        {
            'title': text_filename,
            'parents': [
                parent
            ],
            'mimeType': 'text/plain'
        }
    )
    text_file.SetContentString(text)
    text_file.Upload()
    os.remove(original_file_name)
    file["labels"] = {'starred': True, 'hidden': False, 'trashed': False, 'restricted': False, 'viewed': True}
    file.Upload()


async def fns_process_file(file, drive, parent):
    original_file_name = file.get("title")
    file.GetContentFile(original_file_name)
    image = cv2.imread(original_file_name)
    lines = await zbar(image)
    await create_text_file(drive, parent, file, original_file_name, lines)
    return True


async def fns_process_files(drive):
    parent, file_list = get_file_list(drive)
    async with trio.open_nursery() as nursery:
        for file in file_list:
            nursery.start_soon(fns_process_file, file, drive, parent)


def signup(email, name, phone):
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    r = requests.post(
        'https://proverkacheka.nalog.ru:9999/v1/mobile/users/signup',
        headers=headers
    )
    return r.json()


async def fns_check(qr_string, password="254263", phone="+79522323764"):
    qr_pattern = re.compile("&fn=(\d+)&i=(\d+)&fp=(\d+)")
    qr_match = qr_pattern.search(qr_string)
    fn = qr_match.group(1)
    fd = qr_match.group(2)
    fdp = qr_match.group(3)
    headers = {
        'Device-Id': 'curl',
        'Device-OS': 'linux',
        'Content-Type': 'application/json; charset=utf-8',
        'Date': 'Tue, 09 Oct 2018 08:45:58 GMT'
    }
    r = requests.get(
        "https://proverkacheka.nalog.ru:9999/v1/inns/*/kkts/*/fss/{}/tickets/{}?fiscalSign={}&sendToEmail=no".format(
            fn, fd, fdp
        ),
        auth=(phone, password),
        headers=headers,
    )
    return r.json()


def capitalize_if_upper(word):
    if word.isupper():
        return word.capitalize()
    return word


def remove_all_caps(line):
    return " ".join([capitalize_if_upper(word) for word in line.split(" ")])


async def zbar(image):
    decodedObjects = pyzbar.decode(image)
    lines = []
    for code in decodedObjects:
        if code.type == "QRCODE":
            json_data = await fns_check(code.data.decode("UTF-8"))
            result = json_data["document"]["receipt"]["items"]

            for item in result:
                lines.append("{} Цена: {} руб.".format(remove_all_caps(item["name"]), item["sum"] / 100))
    return "\n".join(lines)
