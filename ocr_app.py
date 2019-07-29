import dlocr
from flask import Flask
from flask import request, jsonify, make_response, render_template, Response
import os
import cv2
from werkzeug.utils import secure_filename
import regex_str as reo
from web_request import Webrequests
import time
import datetime
import json
import redis
import core.utils.mysql_utils as bet
# from hash_ring import *
import logging
from config import dev_status
import numpy as np


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024

# 设置允许的文件格式
# ALLOWED_EXTENSIONS = set(['png', 'jpg', 'JPG', 'PNG', 'bmp'])
ALLOWED_EXTENSIONS = set(['png'])
number = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']
numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
alphabet = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', ',']
tables = ['C1', 'C2', 'C3', 'C5', 'C6', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'D51', 'D52', 'D53', 'D54']
match_3_numbers = ["888", "444", "86.", "98.", "33.", "66.", "88.", "54.", "41.", "56.", "18."]
match_4_numbers = ["700.", "915.", "118.", "138.", "129.", "8689", "2729", "2569"]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['POST'])
@app.route("/ocr_interface/", methods=['POST'])
def ocr_interface():
    '''

    :return: response
    根据移动端传来的图片进行分析识别，把识别结果返回给移动端
    根据分析的结果，识别金额，房间号，用户id发给后台服务端
    '''
    try:
        start = time.time()
        ocr = dlocr.get_or_create()
        if request.method == 'POST':
            f = request.files['file']
            if not (f and allowed_file(f.filename)):
                return jsonify({"error": 1001, "msg": "请检查上传的文件"})
            #basepath = os.path.dirname(__file__)  # 当前文件所在路径
            filename = f.filename
            accept_time = str(datetime.datetime.now()).split('.')[0]
            user_id = filename.split('_')[0]



            upload_path = os.path.join('/home/vision/upload',
                                       secure_filename(f.filename))  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
            upload_path = os.path.join('/home/vision/upload', 'test.png')  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
            f.save(upload_path)

            # 使用Opencv转换一下图片格式和名称
            img = cv2.imread(upload_path)
            file_prefix = str(time.time()).split('.')[0]
            file_prefix = file_prefix + "_" + user_id
            cv2.imwrite(os.path.join('/home/vision/train_img', file_prefix + 'ocr.png'), img)
            #img = cv2.imread('static/images/test.png')
            sp = img.shape
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cont = contours[len(contours) - 1]
            ystart = cont[0][0][1]
            if sp[0] > 250 or sp[1] >= 600:
                img = cv2.resize(img, (round(sp[1] / 1.5), round(sp[0] / 1.5)))
                if ystart > 20:
                    img = img[ystart:round(sp[0] / 4 + 70), 0:round(sp[1] / 2.6)]
                else:
                    img = img[ystart:round(sp[0] / 4 + 70), 0:round(sp[1] / 2.6)]

            else:
                if ystart > 20:
                    img = img[ystart:round(sp[0] / 2 + 70), 0:round(sp[1] / 1.6)]
                else:
                    img = img[ystart:round(sp[0] / 2 + 70), 0:round(sp[1] / 1.6)]

            cv2.imwrite(os.path.join('/home/vision/upload', 'ocr.png'), img)
            bboxes, texts = ocr.detect("/home/vision/upload/ocr.png")
            texts = '\n'.join(texts)
            texts = texts.replace('o', '0')
            texts = texts.replace('O', '0')
            video_status = False
            if texts.count("视") > 0:
                print("oooo---------------")
                video_status = True
            house = reo.find_room(texts)
            tableNo = reo.find_table(texts)
            # 进入截取定位金额字段，获取金额，发送给服务端
            if tableNo in tables:
                house = "AG"
            if tableNo == " " or house == " ":
                s = {"code": 0, "house": "", "tableNo": "", "message": ""}
            else:
                s = {"code": 0, "house": house, "tableNo": tableNo, "message": ""}
            s = json.dumps(s)


            # image_data = open(upload_path, "rb").read()
            response = make_response(s)
            response.headers['Content-Type'] = 'application/json '
            # os.system('rm -rf ' + upload_path)
            # return s
            # app.logger.info(user_id+" - "+house+" - "+tableNo)
            if dev_status == True:
                print("file :", filename)
                print("oral text： ", texts)
                print("return json: ", s)
                print(f"cost: {(time.time() - start) * 1000}ms")
                if tableNo in tables and house != " ":
                    res = check_money(upload_path=upload_path, response=response, user_id=user_id, house=house,
                                      tableNo=tableNo, accept_time=accept_time, ocr=ocr, video_status=video_status)
                    if res != None:
                        return res
                    if res == None:
                        return "{}"

            return response
    except Exception as e:
        app.logger.warning(e)
        return jsonify({"code": 1, "message": "请检查上传的数据"})
        print(e)


@app.route('/ocr_post', methods=['POST', 'GET'])
def ocr_post():

    return "200 success"


# ་检测金额是否与变化，如果有变化再传送到服务器端进行结算
def check_money(upload_path=None, user_id=None, response=None, house=None,tableNo=None, accept_time=None, ocr=None, video_status=None):
    start = time.time()
    img = cv2.imread(upload_path)
    # img = cv2.imread('static/images/test.png')
    sp = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cont = contours[len(contours) - 1]
    cont = cont.flatten()
    cdata = []
    for i in range(len(cont)):
        if i % 2 == 1:
            cdata.append(cont[i])
    if len(cdata) == 2 and cdata[0] == cdata[1]:
        ystart = int(cdata[0] * 4)
        yend = int(cdata[0] * 8)
    else:
        ymin = int(min(cdata))
        ystart = int(max(cdata))
        if ymin < 30:
            ystart = int(ystart * 2 - ystart/4)
        if int(max(cdata)) < 20:
            yend = int(ystart * 8)
        else:
            yend = int(ystart * 4)

    if sp[0] > 250 or sp[1] >= 600:
        if ystart > 20:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        else:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        # img = cv2.resize(img, (round(sp[1] / 1.5), round(sp[0] / 1.5)))
    elif sp[0] > 200 and sp[0] <= 250:
        if ystart > 20:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        else:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        # img = cv2.resize(img, (round(sp[1] / 1.5), round(sp[0] / 1.5)))
    else:
        if ystart > 20:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        else:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        # img = cv2.resize(img, (round(sp[1] / 1.5), round(sp[0] / 1.5)))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((1, 1), np.uint8)
    gray = cv2.dilate(gray, kernel, iterations=1)
    gray = cv2.erode(gray, kernel, iterations=1)
    ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    gray = cv2.bitwise_not(thresh)
    if video_status == False:
        cv2.imwrite(os.path.join('/home/vision/upload', user_id + '_money.png'), img)
    if video_status == True:
        cv2.imwrite(os.path.join('/home/vision/upload', user_id + '_money.png'), img)

    bboxe, texts = ocr.detect("/home/vision/upload/" + user_id + "_money.png")
    print("texts: ", texts)

    texts = "\n".join(texts)
    texts = texts.replace('o', '0')
    texts = texts.replace('O', '0')
    if texts.count("庄") > 0 or texts.count("闲") or texts.count("和"):
        return
    if texts.count("%") > 0:
        return
    text = texts.splitlines()
    application = 'GLM'
    if len(text) > 0:
        appli = reo.find_application(texts)
        if appli != " ":
            application = appli
    if tableNo == 'C5' and int(texts.count("频")) < 1:
        return

    flag = False
    for i in text:
        if len(i) > 2:
            for j in i:
                if j in numbers:
                    text = i

                    if text[0:2] == '频3' or text[0] in numbers:
                        return
                    if text[0:2] == '.频' or text[0] == '3':
                       # if text[0] in numbers:
                       #    return
                        text = text[1:len(text)]
                    text = reo.match_money(text)
                    if len(text) > 0:
                        if text[0:1] == "3" or text[0:1] == "8":
                            return
                    if len(text) >= 3:
                        if text[0:3] in match_3_numbers:
                            return
                    if len(text) >= 4:
                        if text[0:4] in match_4_numbers:
                            return
                    for k in text:
                        if k not in alphabet:
                            return
                    text = reo.match_sec(text)
                    if text == None:
                        return
                    text = reo.match_money(text)
                    if text == None:
                        return
                    flag = True
                    break
        if flag == True:
            break

    # text = text[0]


    money = ""
    # if text[0] in number:
    #   text = text[1:len(text)]
    for i in text:
        if i in number:
            money += i
    if len(money) == 2 or len(money) <= 3:
        for j in money:
            if money[0] == '.':
                money = '0' + money
            if j == '.':
                if len(money) == 2 or len(money) <= 3 or money[0] == '0':
                    if money[0] == '.':
                        money = '0' + money
                    prefix = money.split('.')[0]
                    postfix = money.split('.')[1]
                    if len(postfix) > 2:
                        postfix = postfix[0:2]
                    money = prefix + '.' + postfix

    if (len(money) == 2 or len(money) == 3) and money[0] == '0':
        sec = money.split('.')
        money = sec[0] + '.' + sec[1]

    bsend = False
    for m in money:
        if m not in number:
            bsend = True
            break
    if len(money) > 3 and money[0] == '.':
        money = money[1:len(money)]

    money = reo.match_postfix(money)
    if money == None:
        return
    if dev_status == True:
        print("ystart: ", ystart, yend, sp[1], cdata)
        print(ystart, yend)
        print("oral text: ", texts)
        print("cut text: ", text)

    if len(money) >= 1 and money[0] != '.' and bsend == False:
        user_app = user_id + application
        if money.count('.') > 0:
            sec = money.split(".")
            money = ""
            for i in range(len(sec)):
                if i == len(sec) - 1:
                    if len(sec[i]) != 3:
                        money = money + "." + sec[i]
                    else:
                        money = money + sec[i]
                else:
                    money += sec[i]
            if len(sec) == 2 and len(sec[1]) > 2:
                money = sec[0]+sec[1]

        r = redis.Redis("127.0.0.1", 6379, db=0)
        re_money = r.get(user_app)

        if re_money != None:
            re_money = re_money.decode()
            if re_money == money:
                return response
        money = reo.match_redis_data(re_money, money)
        # app.logger.info(user_id+" - "+house+" - "+tableNo+" - "+money+" - "+re_money)
        if re_money != money and house != " " and money != None:
            if dev_status == True:
                print("application: ", application, money, re_money)
                bet.save_tmp_data(user_app=user_app, user_id=user_id, application=application, house=house,
                              accept_time=accept_time, money=money)
                print(f"cost: {(time.time() - start) * 1000}ms")
            else:
                url = "http://192.168.1.222/asf/fd/settlement/bill/bet/origin/submit"
                # url = "http://127.0.0.1:8888/ocr_post"
                #save_tmp_data(user_app=user_app, user_id=user_id, application=application, house=house,
                #              accept_time=accept_time, money=money)
                para = {"userOid": user_id, "application": application, "venus": house, "dataTime": accept_time,
                        "balanceBet": money, "accrualBet": "0"}
                headers = {"Content-Type": "application/json"}
                q = Webrequests()
                q.post_json(url, para, headers)
                print("send data: ", url, para, headers)
                r.set(user_app, money)

        m = r.get(user_app)
        if m == None:
            r.set(user_app, money)


@app.route('/recognition_account', methods=['POST'])
def recognition_account():
    '''

       :return: response
       根据移动端传来的图片进行分析识别，把识别结果返回给移动端
       根据分析的结果，识别金额，房间号，用户id发给后台服务端
       '''
    try:
        start = time.time()
        ocr = dlocr.get_or_create()
        if request.method == 'POST':
            f = request.files['file']
            if not (f and allowed_file(f.filename)):
                return jsonify({"error": 1001, "msg": "请检查上传的文件"})
            # basepath = os.path.dirname(__file__)  # 当前文件所在路径
            filename = f.filename
            accept_time = str(datetime.datetime.now()).split('.')[0]
            user_id = filename.split('_')[0]


            upload_path = os.path.join('/home/vision/upload',
                                       secure_filename(f.filename))  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
            upload_path = os.path.join('/home/vision/upload', 'test.png')  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
            f.save(upload_path)

            # res = check_money(upload_path=upload_path, user_id=user_id, ocr=ocr)
            # if res == None:
            #    return '''{}'''

            # 使用Opencv转换一下图片格式和名称
            img = cv2.imread(upload_path)
            file_prefix = str(time.time()).split('.')[0]
            file_prefix = file_prefix + "_" + user_id
            cv2.imwrite(os.path.join('/home/vision/train_img', file_prefix + 'ocr.png'), img)

            # img = cv2.imread('static/images/test.png')
            sp = img.shape
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cont = contours[len(contours) - 1]
            ystart = cont[0][0][1]
            if sp[0] > 250 or sp[1] >= 600:
                img = cv2.resize(img, (round(sp[1] / 1.5), round(sp[0] / 1.5)))
                if ystart > 20:
                    img = img[ystart:round(sp[0] / 4 + 70), 0:round(sp[1] / 2.6)]
                else:
                    img = img[ystart:round(sp[0] / 4 + 70), 0:round(sp[1] / 2.6)]

            else:
                if ystart > 20:
                    img = img[ystart:round(sp[0] / 2 + 70), 0:round(sp[1] / 1.6)]
                else:
                    img = img[ystart:round(sp[0] / 2 + 70), 0:round(sp[1] / 1.6)]

            cv2.imwrite(os.path.join('/home/vision/upload', 'ocr.png'), img)
            bboxes, texts = ocr.detect("/home/vision/upload/ocr.png")
            texts = '\n'.join(texts)
            texts = texts.replace('o', '0')
            texts = texts.replace('O', '0')
            video_status = False
            if texts.count("视") > 0:
                video_status = True
            house = reo.find_room(texts)
            tableNo = reo.find_table(texts)
            # 进入截取定位金额字段，获取金额，发送给服务端
            if tableNo in tables:
                house = "AG"
            if tableNo == " " or house == " ":
                s = {"code": 0, "house": "", "tableNo": "", "message": ""}
            else:
                s = {"code": 0, "house": house, "tableNo": tableNo, "message": ""}
            s = json.dumps(s)

            # image_data = open(upload_path, "rb").read()
            response = make_response(s)
            response.headers['Content-Type'] = 'application/json '
            # os.system('rm -rf ' + upload_path)
            # return s
            if dev_status == True:
                print("texts: ", texts)

            if tableNo in tables and house != " ":
                res = check_money(upload_path=upload_path, response=response, user_id=user_id, house=house,
                                  tableNo=tableNo, accept_time=accept_time, ocr=ocr, video_status=video_status)
                if res != None:
                    return res
                if res == None:
                    return "{}"
            return response
    except Exception as e:
        app.logger.warning(e)
        return jsonify({"code": 1, "message": "请检查上传的数据"})
        print(e)


if __name__ == '__main__':

    app.run(host='0.0.0.0', port="8888")
