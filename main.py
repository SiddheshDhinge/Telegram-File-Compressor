import os
import zipfile

#set-up secret.py with required variables.
from secret import API_BOT_TOKEN, API_HASH, API_ID, basket_files, cnf_files

from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from zipfile import ZipFile
import zlib


space_used = 0
users = [944435106, 320864005]
total_files = 0
server_limit = 2621440000


def zip_files(paths):
    name = f'Total Files {len(paths)}.zip'
    name = os.path.join("downloads", name)
    with ZipFile(name, 'w') as zip:
        # writing each file one by one
        for file in paths:
            fnm = os.path.split(file)
            zip.write(file, fnm[1], compress_type=zipfile.ZIP_DEFLATED)
    return name

def upload_handler(app, chat_id, zip_path, comment):
    app.send_document(chat_id, caption=comment, document=zip_path, force_document=True)

def clean_download(paths, zip_path):
    for x in paths:
        os.remove(x)
    os.remove(zip_path)


def inc_total(size):
    global total_files, space_used
    size = size / 1024 / 1000
    space_used += size
    total_files += 1


def verify_user(usr_id, cht_id, app):
    ver = False
    for x in users:
        if x == usr_id:
            ver = True
            break
    if not ver:
        app.send_message(cht_id, "Sorry you are not a verified user")
        return False
    return True


def download_handler(app, message):
    if message.document is None:
        # file a video
        nm = message.video.file_name
        size = message.video.file_size
        file_id = message.video.file_id
    else:
        # file a document
        nm = message.document.file_name
        size = message.document.file_size
        file_id = message.document.file_id

    chat_id = message.chat.id
    edit_txt_id = app.send_message(chat_id, "Starting download... 0% Done.").message_id
    path = app.download_media(file_id, progress=progress, progress_args=(size, app, chat_id, edit_txt_id))
    inc_total(size)
    path_head = os.path.split(path)
    rpath = os.path.join(path_head[0],nm)
    os.rename(path, rpath)
    path = rpath
    print(path, path_head)
    return path


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    if n == 0:
        return lst
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
    return lst


def progress(current, total, *args):
    perc = current * 100 / args[0]

    if(perc > 100):
        perc = 100

    args[1].edit_message_text(args[2], args[3], f"Download Started... {perc:.3f} Done.")


def getFileSize(msg):
    if msg.document is None:
        return msg.video.file_size
    return msg.document.file_size


def mklist(flst, clst1, clst2, tlst):
    size = 0
    for x in tlst:
        size += getFileSize(x)

    a, b = 0, 0
    if len(clst1) > 0:
        a = getFileSize(clst1[0])
        a_a = clst1[0]

        if size + a < server_limit:
            tlst.append(a_a)
            a = 0
            del (clst1[0])
    if len(clst2) > 0:
        b = getFileSize(clst2[0])
        b_b = clst2[0]

        if size + b < server_limit:
            tlst.append(b_b)
            b = 0
            del (clst2[0])

    if (size + a > server_limit and size + b > server_limit) or (len(clst1) == 0 or len(clst2) == 0):
        flst.append(tlst)
        tlst = []

    if len(clst1) > 0 or len(clst2) > 0:
        mklist(flst, clst1, clst2, tlst)


def view(app, user_id, chat_id):
    lst = basket_files.get(user_id)
    str_lst_nm = ""
    for index, value in enumerate(lst):
        nm = ""
        if value.document is None:
            nm = value.video.file_name
        else:
            nm = value.document.file_name

        str_lst_nm += f"{index} | {nm}\n"
    app.send_message(chat_id, str_lst_nm)

def remove(app, user_id, chat_id):
    lst = basket_files.get(user_id)
    warning_str = "Select files you wanna remove\n"
    lst = basket_files.get(user_id)
    str_lst_nm = ""
    for index, value in enumerate(lst):
        nm = ""
        if value.document is None:
            nm = value.video.file_name
        else:
            nm = value.document.file_name

        str_lst_nm += f"{index} | {nm}\n"

    str_lst_nm = warning_str + str_lst_nm

    ln = len(lst)
    if ln >= 3:
        keylst = chunks(["-" + str(x) for x in range(ln)], ln // 3)
        keylst = [x for x in keylst]
    else:
        keylst = [["-" + str(x)] for x in range(ln)]
    if not keylst:
        str_lst_nm = "Your bucket is empty!"
        app.send_message(chat_id, str_lst_nm, reply_markup=ReplyKeyboardRemove())
    else:
        app.send_message(chat_id, str_lst_nm, reply_markup=ReplyKeyboardMarkup(keylst, resize_keyboard=True))


def sort_via_size(arr):
    n = len(arr)

    # Traverse through all array elements
    for i in range(n):

        # Last i elements are already in place
        for j in range(0, n - i - 1):

            # traverse the array from 0 to n-i-1
            # Swap if the element found is greater
            # than the next element
            if arr[j].document is None:
                a = arr[j].video.file_size
            else:
                a = arr[j].document.file_size
            if arr[j+1].document is None:
                a_1 = arr[j + 1].video.file_size
            else:
                a_1 = arr[j + 1].document.file_size

            if a > a_1:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]

def getFile(msg):
    if msg.document is None:
        return msg.video
    return msg.document

def main():
    # Create a new Client instance
    app = Client("telefileserverbot", api_id=API_ID, api_hash=API_HASH, bot_token=API_BOT_TOKEN)

    @app.on_message(filters.text & filters.private)
    def echo(client, message):
        user_id = message.from_user.id
        if not verify_user(message.from_user.id, message.chat.id, app):
            return
        chat_id = message.chat.id
        text = str(message.text).lower()

        if text == "view":
            view(app, user_id, chat_id)
        elif text == "remove":
            remove(app, user_id, chat_id)
        elif "-" in text:
            lst = basket_files.get(user_id)
            print(len(lst))
            msg = lst[int(text[1:len(text)])]
            lst.remove(msg)  # lst[int(text[1:len(text)])] = None
            remove(app, user_id, chat_id)
        #elif text == "all":
        elif text == "start download":
            lst = basket_files.get(user_id)
            clst = cnf_files.get(user_id)
            clst.extend(lst)
            lst.clear() #Added all basket files to confirm files
            print(len(basket_files.get(user_id)), len(cnf_files.get(user_id)))

            flst = []
            sort_via_size(clst)
            clst.reverse()

            clst1 = clst[:len(clst) // 2]
            clst2 = clst[len(clst) // 2:]
            clst2.reverse()

            mklist(flst, clst1, clst2, [])# sorted all files for optimum repackaging

            print(flst)
            for x in flst:
                size = 0
                paths = []
                str_nm = ""
                for y in x:
                    print(getFile(y).file_name)
                    str_nm += f"{getFile(y).file_name}\n"
                    size += getFileSize(y)
                    path = download_handler(app,y)
                    paths.append(path)
                zip_path = zip_files(paths)
                upload_handler(app, chat_id, zip_path, str_nm)
                #clean_download(paths, zip_path)
                print("size : ", size/1024/1000)

            #  download_handler(app, x)
        elif text == "status":
            size = 0
            names = ""

            # assign folder path
            Folderpath = 'downloads'

            # get size
            for ele in os.scandir(Folderpath):
                size += os.path.getsize(ele)
                names += f"{ele.name}\n"
            # display size
            print(f"Files : {names}\nFolder size : {size / 1024 / 1000:.4f}MB")
        else:
            message.reply_text(message.text)

    @app.on_message((filters.video | filters.document) & filters.private)  # receive video and document
    def document_receive(client, message):
        user_id = message.from_user.id
        if not verify_user(user_id, message.chat.id, app):
            return

        lst = basket_files.get(user_id)
        lst.append(message)
        app.send_message(message.chat.id, f"Added to Basket, no : {len(lst)}")

    app.run()  # Automatically start() and idle()


if __name__ == '__main__':
    print('Bot Started')
    main()
