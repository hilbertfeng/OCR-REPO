import pymysql.cursors
import uuid
import redis
import datetime


def save_tmp_data(user_app=None,user_id=None, application=None, house=None, accept_time=None, money=None):
    try:
        # 连接数据库
        conn = pymysql.connect(host='192.168.1.222',
                               user='ocr_user1',
                               password='FDpassword',
                               db='app_fd',
                               charset='utf8')

        # 创建一个游标
        cursor = conn.cursor()
        oid = uuid.uuid1()

        # 插入数据
        # 数据直接写在sql后面
        sql = "insert into t_fd_settlement_bet_origin_tmp" \
              "(OID, USER_OID, APPLICATION, VENUS, BALANCE_BET, DATA_TIME, HASH, STATUS, VERSION) " \
              "values(%s, %s, %s, %s, %s, %s, %s, %s, %s)"  # 注意是%s,不是s%
        cursor.execute(sql, [str(oid), user_id, application, house, money, accept_time, '0', '1', '0'])  # 列表格式数据

        conn.commit()  # 提交，不然无法保存插入或者修改的数据(这个一定不要忘记加上)
        cursor.close()  # 关闭游标
        conn.close()  # 关闭连接
        r = redis.Redis("127.0.0.1", 6379, db=0)
        r.set(user_app, money)
        print("写入成功！")
    except Exception as e:
        print("写入失败！")
        cursor.close()  # 关闭游标
        conn.close()  # 关闭连接
    finally:
        cursor.close()  # 关闭游标
        conn.close()  # 关闭连接


