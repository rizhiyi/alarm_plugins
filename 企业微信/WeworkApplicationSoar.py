# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     WeworkApplicationSoar.py
   Description :     企业微信应用告警推送SOAR
   Author      :     chen.fei
   Email       :     chen.fei@yottabyte.cn
   Date        :     2024/4/23 下午2:41
-------------------------------------------------
"""
import argparse
import json
import logging
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
import urllib3

###########公共参数##############################################
# SIEM平台名称
sysTitle = "SIEM平台"
# 企业id
corpid = ""
# 应用秘钥
secret = ""
# 应用id
agentid = ""
# 单条最大消息大小
max_message_size = 2048
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
  'http': '',
  'https': '',
}
url_prefix = "https://qyapi.weixin.qq.com/cgi-bin"
################################################################


urllib3.disable_warnings()
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('/data/rizhiyi/logs/soar/WeworkApplicationSoar.log', maxBytes=100 * 1024 * 1024, backupCount=5, encoding='utf-8')
formatter = logging.Formatter(fmt="[%(asctime)s] [%(levelname)s] [%(filename)s.%(funcName)s.%(lineno)d] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


def split_string_by_bytes(string):
    """
    根据指定字节长度分割字符串
    Args:
        string: 字符
    Returns:

    """
    encoded_string = string.encode('utf-8')  # 将字符串编码为 UTF-8 字节序列

    # 如果字符串本身的字节长度小于等于指定字节长度，则无需分割，直接返回原字符串
    if len(encoded_string) <= max_message_size:
        return [string]

    parts = []
    current_bytes = 0
    current_part = ""

    for char in string:
        encoded_char = char.encode('utf-8')
        char_bytes = len(encoded_char)

        # 如果当前部分加上当前字符的字节长度不超过指定字节长度，则将当前字符添加到当前部分中
        if current_bytes + char_bytes <= max_message_size:
            current_part += char
            current_bytes += char_bytes
        else:
            parts.append(current_part)
            current_part = char
            current_bytes = char_bytes

    parts.append(current_part)

    return parts


def _get_token():
    """
    获取access token
    Returns:

    """
    try:
        url = url_prefix + "/gettoken?corpid={}&corpsecret={}".format(corpid, secret)
        resp = requests.get(url, verify=False, timeout=30, proxies=proxies)
        logger.debug(resp.text)
        if resp.status_code == 200:
            resp_json = resp.json()
            if resp_json["errcode"] == 0:
                access_token = resp_json["access_token"]
                logger.info("获取Token成功, access_token: {}".format(access_token))
                return access_token
            else:
                logger.error("获取Token失败! response: {}".format(resp.text))
            return None
        logger.error("获取Token失败! response: {}".format(resp.text))
    except Exception as ex:
        logger.error("获取Token异常! exception: {}".format(ex))
    return None


def _get_user_id(phones, access_token):
    """
    根据手机号获取用户ID
    Returns:

    """
    user_ids = []
    try:
        url = url_prefix + "/user/getuserid?access_token={}".format(access_token)
        for phone in phones:
            body = {
                "mobile": phone
            }
            resp = requests.post(url, json=body, verify=False, timeout=30, proxies=proxies)
            logger.debug(resp.text)
            if resp.status_code == 200:
                resp_json = resp.json()
                if resp_json["errcode"] == 0:
                    user_ids.append(resp_json["userid"])
                else:
                    logger.error("获取{}用户ID失败, 详情:{}".format(phone, resp_json["errmsg"]))
    except Exception as e:
        logger.error("获取UserID异常! exception: {}".format(e))
    finally:
        return "|".join(user_ids)


def send_message(alert_name, users, message, access_token):
    """
    @param users: 接收消息的成员
    @param message: 消息内容
    @param access_token: access_token
    @return:
    """
    url = url_prefix + "/message/send?access_token={}".format(access_token)
    payload = {
        "touser": users,
        "msgtype": "text",
        "agentid": agentid,
        "text": {
            "content": message
        }
    }
    try:
        response = requests.post(url, data=json.dumps(payload), verify=False, timeout=30, proxies=proxies)
        logger.debug(response.text)
        logger.info("告警名称:{}, 推送消息成功, 内容:{}, 返回结果:{}".format(alert_name, message, response.text))
    except Exception as e:
        logger.error("告警名称:{}, 推送消息失败, 内容:{}, 抛出错误:{}".format(alert_name, message, e))


def main():
    try:
        message = "[{}]\n告警名称: ".format(sysTitle) + alert_name + "\n告警时间: {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + "\n告警内容: 👇\n" + alert_msg
        logger.info("传入参数...alert_name:{}, alert_msg:{}, users_ids:{}, mobiles:{}".format(alert_name, message, users_ids, mobiles))

        msgContexts = split_string_by_bytes(message)
        access_token = _get_token()
        if access_token:
            users_str = ""
            if len(users_ids) > 0:
                if users_ids == "all":
                    users_str = "@all"
                else:
                    users_str = "|".join(users_ids.split(","))
            elif len(mobiles) > 0:
                try:
                    users_str = _get_user_id(mobiles.split(','), access_token)
                    if len(users_str) == 0:
                        logger.error("获取用户id失败, 不执行发送")
                except Exception as e:
                    logger.exception("请输入正确手机号, 多个手机号请以逗号分割")

            if len(msgContexts) > 5:
                for i in range(0, 5):
                    send_message(alert_name=alert_name, users=users_str, message=msgContexts[i], access_token=access_token)
            else:
                for message in msgContexts:
                    send_message(alert_name=alert_name, users=users_str, message=message, access_token=access_token)
            print("True")
    except Exception as e:
        logger.exception(e)
        print("False")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="/opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/WeworkApplicationSoar.py --alert_name '告警测试' --alert_msg '测试' --users_ids 1111111,222222 --mobiles 1111111,222222", add_help=True)
    parser.add_argument("--alert_name", type=str, help="告警名称")
    parser.add_argument("--alert_msg", type=str, help="告警信息, 建议以单引号限定, 否则遇到空格会报错")
    parser.add_argument("--users_ids", type=str, help="可选: 用户ID, 多用户ID以,(逗号)分割")
    parser.add_argument("--mobiles", type=str, help="可选: 手机号, 多手机以,(逗号)分割")
    options = parser.parse_args()

    if not (options.alert_name or options.alert_msg):
        logger.warning("alert_name或者alert_msg参数不能为空")
        print("False")
        parser.print_help()
        sys.exit(1)
    if not (options.users_ids and options.mobiles):
        logger.warning("users_id或者mobiles参数只能一个为空")
        print("False")
        parser.print_help()
        sys.exit(1)

    if not (corpid or agentid or secret):
        logger.warning("企业id或者应用秘钥或应用ID不能为空")
        print("False")
        sys.exit(1)

    alert_name = options.alert_name
    alert_msg = options.alert_msg
    users_ids = options.users_ids
    mobiles = options.mobiles

    main()
