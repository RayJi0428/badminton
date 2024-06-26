import datetime
import os
import logger
import utils
from data import ResultData
global target_date

tw_idx = ['一', '二', '三', '四', '五', '六', '日']

initialize = False


# 日期
date_string = '00/00'
# 時間
time_slots = '20:00-22:00'
# 星期
week_day = '-'
# 幾面場
num_court = 3
# 座位數
num_vacancy = 24

# 這一場的資料-----------------------------------------
cur_quarterly_list = []
cur_parttime_list = []
cur_cancel_list = []

# googlesheet資料--------------------------------------------
admin_data_list = None  # 管理員
param_data_list = None  # 參數
court_name = ''  # 羽球場地
num_court = 0  # 羽球場地數
num_seat_per_court = 0  # 一場預設人數
quarterly_list = []  # 季繳名單
tmp_quarterly_list = []  # 啟動時季繳修復資料
tmp_partime_list = []  # 啟動時零打修復資料
cur_blame_user = []  # 懲罰清單
# 指令--------------------------------------------------------
cmd_data_list = None


# 初始化
def init(p_admin_data_list, p_param_data_list, p_cmd_data_list):
    global admin_data_list, param_data_list, cmd_data_list
    global court_name, num_court, num_seat_per_court, quarterly_list, time_slots
    global tmp_quarterly_list, tmp_partime_list

    # 管理員清單
    admin_data_list = p_admin_data_list

    # 參數列表
    param_data_list = p_param_data_list
    court_name = utils.get_param_by_key(param_data_list, '場地')
    num_court = utils.get_param_by_key(param_data_list, '預設場地數')
    num_seat_per_court = utils.get_param_by_key(param_data_list, '一場預設人數')
    time_slots = utils.get_param_by_key(param_data_list, '預設時段')
    quarterly_list = utils.get_param_by_key(param_data_list, '季繳名單').split(',')
    tmp_quarterly_list_str = utils.get_param_by_key(param_data_list, '啟動修復季繳')
    if tmp_quarterly_list_str != None:
        tmp_quarterly_list = tmp_quarterly_list_str.split(',')
    tmp_partime_list_str = utils.get_param_by_key(param_data_list, '啟動修復零打')
    if tmp_partime_list_str != None:
        tmp_partime_list = tmp_partime_list_str.split(',')

    # 指令參數
    cmd_data_list = p_cmd_data_list


# 是否為指令訊息
def find_cmd_in_msg(msg_text):
    for data in cmd_data_list:
        if data['KEY'] in msg_text:
            return data
    return None


# 取得function
def call_cmd_fn(fn_name, event) -> ResultData:
    fn = globals().get(fn_name)
    if callable(fn):
        return fn(event)
    else:
        logger.print(f'找不到對應function:{fn_name}')


# 總結
def get_summary():
    global num_vacancy
    # 總結
    summary_str = ''

    # 標題
    title = f'【{date_string}(週{tw_idx[week_day]}){court_name}】\n{time_slots} {num_court}面場'
    summary_str += title + '\n'

    # 成員
    final_permanent = cur_quarterly_list.copy()
    final_partime = cur_parttime_list.copy()
    mem_str = ''
    for i in range(0, num_vacancy):
        # 季繳
        if len(final_permanent) > 0:
            member = final_permanent.pop(0)
            mem_str += f'{i+1}.{member}\n'
        # 零打
        elif len(final_partime) > 0:
            member = final_partime.pop(0)
            mem_str += f'{i+1}.{member}(零打)\n'
        # 空位
        else:
            mem_str += f'{i+1}.\n'

    summary_str += mem_str

    logger.print(summary_str)
    logger.print('---------------------------------------')

    return summary_str


# 指令處理================================================================
# 指令處理================================================================
# 指令處理================================================================


# 指令說明
def intro(event):
    text = '【指令說明】\n'
    devider = False
    for cmd_data in cmd_data_list:
        if devider == False and cmd_data['管理員限定'] != '':
            text += "-----以下僅管理員使用-----\n"
            devider = True
        key = cmd_data['KEY']
        tip = cmd_data['TIP']
        text += f'{key} ({tip})\n'
    return ResultData(text=text)


# 報名
def apply(event):
    msg_text = event.message.text
    user_id = event.source.user_id
    apply_member = msg_text.split(' ')[1].lower()
    text = '報名失敗...請洽管理員 T____T'
    if initialize == False:
        text = '還沒開喔~~~不要急:)'
    else:
        if apply_member in cur_quarterly_list or apply_member in cur_parttime_list:
            if user_id in cur_blame_user:
                return ResultData(image='https://i.imgur.com/ElfhW41.jpg')
            else:
                cur_blame_user.append(user_id)
                return ResultData(text='已經報了拉!是要報幾次凸')
        else:
            if apply_member not in cur_cancel_list:
                cur_parttime_list.append(apply_member)
                text = get_summary()

    return ResultData(text=text)


# 取消
def cancel(event):
    msg_text = event.message.text
    cancel_member = msg_text.split(' ')[1].lower()

    cancel_result = False
    text = '找不到阿...你確定你有報?凸'
    if initialize == False:
        text = '還沒開取消屁?凸'
    elif cancel_member in cur_quarterly_list:
        cancel_result = True
        cur_quarterly_list.remove(cancel_member)
        text = get_summary()
    elif cancel_member in cur_parttime_list:
        cancel_result = True
        cur_parttime_list.remove(cancel_member)
        text = get_summary()

    if cancel_result == True:
        if cancel_member not in cur_cancel_list:
            cur_cancel_list.append(cancel_member)
        text += "\n失去你我很難過..."
    return ResultData(text=text)


# 查詢活動
def query(event):
    if initialize == False:
        text = '還沒開喔~~~不要急:)'
    else:
        text = get_summary()

    return ResultData(text=text)


# 管理員指令處理================================================================
# 管理員指令處理================================================================
# 管理員指令處理================================================================


# 檢查user是否為管理員
def is_admin(userID):
    result = False
    for admin in admin_data_list:
        if admin['userID'] == userID:
            result = True
    return result


# 建立活動
def initiate(event):
    msg_text = event.message.text
    input_date = msg_text.split(' ')[1]

    global initialize
    global date_string, week_day, time_slots
    global num_court, num_vacancy
    global cur_quarterly_list, cur_parttime_list, cur_cancel_list, cur_blame_user
    global tmp_quarterly_list, tmp_partime_list
    initialize = True

    cur_quarterly_list = quarterly_list.copy()
    cur_parttime_list = []
    cur_cancel_list = []
    cur_blame_user = []
    num_vacancy = num_court * num_seat_per_court
    # 日期
    date_string = input_date
    date_string_list = input_date.split('/')
    y = datetime.datetime.today().year
    m = date_string_list[0]
    d = date_string_list[1]
    full_date_string = f'{y}-{m}-{d}'
    date_obj = datetime.datetime.strptime(full_date_string, '%Y-%m-%d')
    week_day = date_obj.weekday()

    # 修復資料
    if len(tmp_quarterly_list) > 0:
        cur_quarterly_list = tmp_quarterly_list.copy()
        tmp_quarterly_list = []
    if len(tmp_partime_list) > 0:
        cur_parttime_list = tmp_partime_list.copy()
        tmp_partime_list = []

    text = get_summary()
    return ResultData(text=text)


# 修改時間
def edit_time_slots(event):
    if initialize == False:
        return ResultData(text='請先建立活動')
    msg_text = event.message.text
    input_time = msg_text.split(' ')[1]

    global time_slots
    time_slots = input_time
    text = get_summary()
    return ResultData(text=text)


# 活動截止
def events_end(event):

    global initialize

    if initialize == False:
        return ResultData(text='請先建立活動')

    text = ''
    initialize = False
    text = get_summary()
    text += '🈵'
    return ResultData(text=text)


# 設定面數
def edit_court(event):
    global num_vacancy
    if initialize == False:
        return ResultData(text='請先建立活動')
    msg_text = event.message.text
    input_court = int(msg_text.split(' ')[1])

    global num_court
    num_court = input_court
    num_vacancy = num_court * num_seat_per_court
    text = get_summary()
    return ResultData(text=text)


# 設定座位數
def edit_vacancy(event):
    if initialize == False:
        return ResultData(text='請先建立活動')

    msg_text = event.message.text
    input_vacancy = int(msg_text.split(' ')[1])

    global num_vacancy
    num_vacancy = input_vacancy
    text = get_summary()
    return ResultData(text=text)


# 印使用者ID
def get_uid(event):
    text = event.source.user_id
    return ResultData(text=text)


# 印群組ID
def get_gid(event):
    text = '沒有群組ID'
    if hasattr(event.source, 'group_id'):
        text = event.source.group_id
    return ResultData(text=text)


# 設定季繳成員 ex:'@季繳 花生,靖玟'
def add_quaterly_member(event):
    msg_text = event.message.text
    member_list_str = msg_text.split(' ')[1]
    input_member_list = member_list_str.split(',')

    global quarterly_list
    text = '設定失敗'
    for member in input_member_list:
        member = member.lower()
        if member not in quarterly_list:
            quarterly_list.append(member)
            text = '設定成功'
        else:
            text = '本來就在裡面了阿'
    return ResultData(text=text)
