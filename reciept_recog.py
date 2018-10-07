import os
import cv2
import pytesseract
from PIL import Image


def process_files(drive):
    parent = drive.ListFile({'q': "title = 'receipt_folder'"}).GetList()
    if parent:
        parent = parent[0]
        file_list = drive.ListFile({'q': "'{}' in parents and trashed=false and starred=false and mimeType != 'text/plain'".format(parent.get("id"))}).GetList()
        for file in file_list:
            original_file_name = file.get("title")
            file.GetContentFile(original_file_name)
            image = cv2.imread(original_file_name)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 1)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            filename = "{}.png".format(os.getpid())
            cv2.imwrite(filename, gray)

            text = pytesseract.image_to_string(Image.open(filename), lang="eng+rus")
            text_filename = "{}.txt".format(original_file_name.split(".")[0])
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
