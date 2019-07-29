import re
roomNo = ['AG', 'IM']
tableNo = ['C1', 'C2', 'C3', 'C5', 'C6', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'D51', 'D52', 'D53', 'D54']

texts = "AG国际馆\n*\n●10311一\n(百家乐d54\n局号:GDO5419607148\n限红:2-5K\n d54 （7万后刚是防寺对方"

#regex = "\●\d{2,10}+(\.)"
#for i in texts:
#money = re.findall(regex, texts)
#for i in texts:
#print("money: ", money)

#print(texts[0:round(len(texts)/2)])

#print(texts)


# 匹配在那个房间
def find_room(texts):
    texts = texts[0:round(len(texts) / 2)]
    texts = texts.upper()
    regex = "(AG|IM)"
    #for i in range(len(roomNo)):
    result = re.search(regex, texts)
        #if result != None:
            #break
    if result != None:
        result = result[0]
    elif result == None:
        result = " "
    return result


# 匹配在那个桌子
def find_table(texts):
    texts = texts[0:round(len(texts))]
    texts = texts.upper()
    regex = "(B1|B2|B3|B4|B5|GBO05|GB005|B6|C1|C2|C3|C5|C6|D51|D52|D53|D54|CI|GC001}GCO01|GCD01|GCOO1" \
            "|GD051|GC006|GCO06|GC002|GCO02|GC003|GCO03|GCOO3|GCD03|GB001|GBO01|G006|GCO05|GC005)"
    # for i in range(len(tableNo)):
    result = re.search(regex, texts)
    # if result != None:
    # break
    if result != None:
        result = result[0]
        if result == 'CI' or result == 'GC001' or result == 'GCO01' or result == 'GCD01' or result == 'GCOO1':
            result = 'C1'
        if result == 'GD051':
            result = 'D51'
        if result == 'GC006' or result == 'GCO06' or result == 'G006':
            result = 'C6'
        if result == 'GC002' or result == 'GCO02':
            result = 'C2'
        if result == 'GC003' or result == 'GCO03' or result == 'GCOO3' or result == 'GCD03':
            result = 'C3'
        if result == 'GB001' or result == 'GBO01':
            result = 'B1'
        if result == 'GCO05' or result =='GC005':
            result ='C5'
        if result == 'GB005' or result =='GBO05':
            result = 'B5'
    elif result == None:
        result = " "
    return result


# 匹配用户在那个APP应用玩游戏
def find_application(texts):
    regex = "(AG国际厅|国际厅|际厅|厅|斤)"
    result = re.search(regex, texts)
    # if result != None:
    # break
    if result != None:
        result = result[0]
        result = "K8"
    elif result == None:
        result = " "
    return result


# 匹配用户是否在视频状态
def find_video(texts):
    regex = "(|视频|频|:频|.频)"
    # print("search: ", texts)
    result = re.search(regex, texts)
    # if result != None:
    # break
    # print("result: ", result)
    if result != None:
        result = result[0]
        if result == '频' or result == ":频" or result == '.频':
            result = "V"
    elif result == None:
        result = " "
    return result


def match_redis_data(re_data, data):
    if re_data != None:
        if len(data) >= 3:
            if re_data.count(".") > 0 and data.count(".") < 1:
                postfix = re_data.split(".")[1]
                if len(postfix) == 2:
                    if postfix == data[len(data) - 2:len(data)]:
                        return
                if len(postfix) == 1:
                    if postfix == data[len(data) - 1:len(data)]:
                        return

    return data

# 匹配用户账户中的余额文本
def match_money(texts):
    regex = '[0-9]([^-]*)(\d+)|[0-9]'
    result = re.search(regex, texts)
    if result != None:
        result = result[0]
    elif result == None:
        result = " "
    return result


def match_sec(texts):
    if texts.count('.') == 1 and len(texts.split('.')[1]) <= 2:
        sec = texts.split('.')[0]
        sec = str(sec)
        if sec.count(',') > 0:
            text = sec.split(',')
            for i in range(1, len(text)):
                if len(text[i]) % 3 != 0:
                    return

    if texts.count('.') >= 1 and len(texts.split('.')[1]) <= 2:
        sec = texts.split('.')
        sec = sec[1:len(sec) - 1]
        if len(sec) % 3 != 0:
            return

    else:
        if texts.count(',') > 0:
            text = texts.split(',')
            for i in range(1, len(text)):
                if len(text[i]) % 3 != 0:
                    return

    return texts


def match_postfix(texts):
    if texts.count('.') > 0:
        sec = texts.split('.')[1]
        if len(sec) == 2 and sec[1] != '5':
            return
    return texts


if __name__ == "__main__":
    room_no = find_room(texts)
    table_no = find_table(texts)
    print(room_no)
    print(table_no)

