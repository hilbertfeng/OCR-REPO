import requests
import json


class Webrequests:

    def get(self, url, para, headers):
        try:
            r = requests.get(url, params=para, headers=headers)
            print("获取返回的状态码", r.status_code)
            json_r = r.json()
            print("json类型转化成python数据类型", json_r)
        except BaseException as e:
            print("请求失败！",str(e))

    def post(self, url, para, headers):
        try:
            r = requests.post(url, data=para, headers=headers)
            print("获取返回的状态码", r.status_code)
            json_r = r.json()
            print("json类型转化成python数据类型",json_r)
        except BaseException as e:
            print("请求失败！", str(e))

    def post_json(self, url, para, headers):
        try:
            data = para
            data = json.dumps(data)   # python数据类型转化为json数据类型
            r = requests.post(url, data=data, headers=headers)
            print("获取返回的状态码", r.status_code)
            json_r = r.json()
            print("json类型转化成python数据类型", json_r)
        except BaseException as e:
            print("请求失败！", str(e))

'''

url = "http://v.juhe.cn/laohuangli/d"
para = {"key":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeee","date":"2017-3-22"}
headers ={}

q = Webrequests()

q.get(url,para,headers)
q.post(url,para,headers)
q.post_json(url,para,headers)

'''