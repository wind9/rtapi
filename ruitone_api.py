from yaml import safe_load
import threading
import logging
import time
import random
import hashlib
import pyDes
from pyDes import *
import base64
import requests
import json


def get_log():
    log = logging.getLogger("充值api")
    log.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('ruitone.log', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s|%(name)s|%(levelname)s|%(message)s')
    file_handler.setFormatter(formatter)
    #file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    return log


def des_encrypt(key, text):
    cipherX = pyDes.des('        ', pad=None, padmode=PAD_PKCS5)
    cipherX.setKey(key)
    encryptStr = cipherX.encrypt(text)
    return bytes.decode(base64.b64encode(encryptStr))


def md5(text):
    m = hashlib.md5()
    m.update(text)
    return m.hexdigest()


def get_phone_list():
    phone_file = 'phone.txt'
    phone_list = []
    with open(phone_file, 'r') as f:
        for line in f.readlines():
            charge_info = {}
            charge_info['phone'] = line.strip().split()[0]
            charge_info['face'] = line.strip().split()[1]
            phone_list.append(charge_info)
    return phone_list


def charge(phone, face):
    params = {
        "reqStreamId" : "rt{}{}".format(round(time.time()*1000), random.randint(100, 1000)),
        "agtPhone" : str(charge_args.get('agtPhone')),
        "businessCode" : charge_args.get('businessCode'),
        "chargeAddr" : phone,
        "chargeMoney" : face,
        "data" : "",
        "tradePwd" : md5(str(charge_args.get('tradePwd')).encode()),
        "nofityUrl" : ""
    }
    headers = {
        'Content-Type': 'application/json'
    }
    encryptStr = des_encrypt(charge_args.get('appKey'), json.dumps(params))
    post_data = {
        "appId": charge_args.get('appId'),
        "param": encryptStr
    }
    r = requests.post(charge_args.get('charge_url'), data=json.dumps(post_data), headers=headers)
    resp = r.content.decode('utf-8')
    return resp


def run(thread_id, thread_num, phone_list):
    i = 0
    for charge_info in phone_list:
        phone = charge_info['phone']
        face = charge_info['face']
        if i % thread_num == thread_id:
            resp = charge(phone, face)
            log.info("线程{}执行任务{},号码{}面值{},响应{}".format(thread_id, i, phone, face, resp))
        i = i + 1


config_file = 'config.yaml'
with open(config_file, 'r') as f:
    content = f.read()
charge_args = safe_load(content)
log = get_log()

if __name__ == '__main__':
    thread_num = charge_args.get('thread_num')
    thread_list = []
    phone_list = get_phone_list()
    for i in range(thread_num):
        t = threading.Thread(target=run, args=(i, thread_num, phone_list))
        thread_list.append(t)
    for t in thread_list:
        t.setDaemon(True)
        t.start()
    for t in thread_list:
        t.join()
