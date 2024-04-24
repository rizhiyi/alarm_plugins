# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     DingTalkJobNoticeSoar.py
   Description :     工作通知SOAR
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
# 企业内部应用AgentId
AgentId = ""
# 应用ID (原 AppKey 和 SuiteKey)
ClientID = ""
# 应用秘钥 (原 AppSecret 和 SuiteSecret)
ClientSecret = ""
# 单条最大消息大小
max_message_size = 2048
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
  'http': '',
  'https': '',
}
url_prefix = "https://oapi.dingtalk.com"
################################################################


urllib3.disable_warnings()
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('/data/rizhiyi/logs/soar/DingTalkJobNoticeSoar.log', maxBytes=100 * 1024 * 1024, backupCount=5, encoding='utf-8')
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


def get_access_token():
    """
    获取access_token,每次运行都会获取一个
    @return:
    """
    url = url_prefix + "/gettoken"
    params = {
        "appkey": ClientID,
        "appsecret": ClientSecret
    }

    try:
        response = requests.get(url, params=params, verify=False, timeout=30, proxies=proxies)
        logger.info(response.text)
        text = response.json()
        if text["errcode"] == 0:
            access_token = text["access_token"]
            logger.info("获取access token: %s" % access_token)
            return access_token
        return None
    except Exception as e:
        logger.error("获取access token异常, %s" % e)
        return None


def get_userid_by_mobile(access_token, mobiles: list):
    """
    通过手机号获取钉钉中的userid
    @param access_token:
    @param phone:
    @return:
    """
    userids = []
    url = url_prefix + "/topapi/v2/user/getbymobile?access_token={}".format(access_token)
    header = {
        "Content-Type": "application/json"
    }
    for phone in mobiles:
        data = {
            "mobile": phone
        }
        try:
            response = requests.post(url, json=data, headers=header, verify=False, timeout=30, proxies=proxies)
            logger.info(response.text)
            text = response.json()
            if text["errcode"] == 0:
                userids.append(text["result"]["userid"])
        except Exception as e:
            logger.error("获取userid异常, %s" % e)
        finally:
            return userids


def send_message(access_token, userid_list, message, alertName):
    """
    发送工作消息
    @param access_token:
    @param userid_list:
    @param message:
    @return:
    """
    userid_list = ",".join(userid_list)
    url = url_prefix + "/topapi/message/corpconversation/asyncsend_v2?access_token={}".format(access_token)
    header = {
        "Content-Type": "application/json"
    }
    data = {
        "msg": {
            "msgtype": "text",
            "text": {
                "content": message
            }
        },
        "agent_id": AgentId,
        "userid_list": userid_list
    }
    try:
        response = requests.post(url=url, json=data, headers=header, verify=False, timeout=30, proxies=proxies)
        text = response.json()
        if text["errcode"] == 0:
            logger.info("告警:{}, 推送成功, 推送内容:{}".format(alertName, json.dumps(data, ensure_ascii=False)))
        else:
            logger.warning("告警:{}, 推送失败, 推送内容:{}".format(alertName, json.dumps(data, ensure_ascii=False)))
    except Exception as e:
        logger.error("告警:{}, 推送异常:{}, 推送内容:{}".format(alertName, e, json.dumps(data, ensure_ascii=False)))


def main():
    message = "[SIEM平台]\n告警名称: " + alert_name + "\n告警时间: {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + "\n告警内容: 👇\n" + alert_msg
    logger.info("传入参数...alert_name:{}, alert_msg:{}, mobiles:{}".format(alert_name, message, mobiles))

    msgContexts = split_string_by_bytes(message)
    access_token = get_access_token()
    if access_token:
        userid_list = get_userid_by_mobile(access_token, mobiles.split(","))
        if len(userid_list) > 0:
            if len(msgContexts) > 5:
                for i in range(0, 5):
                    send_message(access_token=access_token, userid_list=userid_list, message=msgContexts[i], alertName=alert_name)
            else:
                for message in msgContexts:
                    send_message(access_token=access_token, userid_list=userid_list, message=message, alertName=alert_name)
            print("True")
        else:
            logger.warning("根据输入手机号:{}, 无法查询相关用户".format(mobiles))
            print("False")
    else:
        logger.error("获取AccessToken异常, 不进行推送")
        print("False")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="/opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/DingTalkJobNoticeSoar.py --alert_name '告警测试' --alert_msg '测试' --mobiles 1111111,222222", add_help=True)
    parser.add_argument("--alert_name", type=str, help="告警名称")
    parser.add_argument("--alert_msg", type=str, help="告警信息, 建议以单引号限定, 否则遇到空格会报错")
    parser.add_argument("--mobiles", type=str, help="可选: 手机号, 多手机以,(逗号)分割")
    options = parser.parse_args()

    if not (options.alert_name or options.alert_msg or options.mobiles):
        logger.warning("alert_name或者alert_msg参数不能为空")
        print("False")
        parser.print_help()
        sys.exit(1)

    if not (AgentId or ClientID or ClientSecret):
        logger.warning("企业内部应用AgentId或者应用ID或者应用密钥不能为空")
        print("False")
        sys.exit(1)

    alert_name = options.alert_name
    alert_msg = options.alert_msg
    mobiles = options.mobiles

    main()