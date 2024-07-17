# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     FeishuApplicationSoar.py
   Description :     飞书-应用机器人告警SOAR
   Author      :     chen.fei
   Email       :     chen.fei@yottabyte.cn
   Date        :     2024/4/23 下午2:42
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
# 应用id
AppId = ""
# 应用秘钥
AppSecret = ""
# 单条最大消息大小
max_message_size = 2048
# 事件数统计、SPL统计以及拓展搜索最大结果行数
max_result_size = 20
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
  'http': '',
  'https': '',
}
url_prefix = "https://open.feishu.cn/open-apis"
################################################################


urllib3.disable_warnings()
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('/data/rizhiyi/logs/soar/FeishuApplicationSoar.log', maxBytes=100 * 1024 * 1024, backupCount=5, encoding='utf-8')
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
    if len(encoded_string) <= 2048:
        return [string]

    parts = []
    current_bytes = 0
    current_part = ""

    for char in string:
        encoded_char = char.encode('utf-8')
        char_bytes = len(encoded_char)

        # 如果当前部分加上当前字符的字节长度不超过指定字节长度，则将当前字符添加到当前部分中
        if current_bytes + char_bytes <= 2048:
            current_part += char
            current_bytes += char_bytes
        else:
            parts.append(current_part)
            current_part = char
            current_bytes = char_bytes

    parts.append(current_part)

    return parts


def get_tenant_access_token():
    """
    获取tenant_access_token
    Returns:

    """
    try:
        url = url_prefix + "/auth/v3/tenant_access_token/internal"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {
            "app_id": AppId,
            "app_secret": AppSecret
        }
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=30, proxies=proxies)
        logger.info(response.text)
        text = response.json()
        if text["code"] == 0:
            return text["tenant_access_token"]
        logger.warning("获取tenant_access_token异常! response: {}".format(response.text))
        return None
    except Exception as ex:
        logger.error("获取tenant_access_token异常! exception: {}".format(ex))
        return None


def get_open_id(tenant_access_token, mobiles: list, emails: list):
    """
    通过手机号或者邮箱查询用户ID
    @param tenant_access_token:
    @param mobiles:
    @return:
    """
    open_ids = []
    try:
        url = url_prefix + "/contact/v3/users/batch_get_id?user_id_type=open_id"
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer {}".format(tenant_access_token)
        }
        payload = {
            "include_resigned": True,
            "mobiles": mobiles,
            "emails": emails
        }
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=30, proxies=proxies)
        logger.info(response.text)
        text = response.json()
        if text["code"] == 0:
            for user_list in text["data"]["user_list"]:
                if user_list.get("user_id"):
                    open_ids.append(user_list.get("user_id"))
    except Exception as ex:
        logger.error("获取tenant_access_token异常! exception: {}".format(ex))
    finally:
        logger.info("mobiles:{}, emails:{}, open_ids:{}".format(mobiles, emails, open_ids))
        return open_ids


def send_message(tenant_access_token, open_ids: list, alertName, message):
    """
    推送消息
    @param tenant_access_token:
    @param open_ids:
    @param alertName:
    @param message:
    @return:
    """
    url = url_prefix + "/im/v1/messages?receive_id_type=open_id"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": "Bearer {}".format(tenant_access_token)
    }
    for receive_id in open_ids:
        payload = {
          "receive_id": receive_id,
          "msg_type": "text",
          "content": json.dumps({"text": message})
        }
        try:

            response = requests.post(url, headers=headers, json=payload, verify=False, timeout=30, proxies=proxies)
            logger.info("告警名称:{}, 告警内容:{}, 推送返回结果:{}".format(alertName, message, response.text))
        except Exception as ex:
            logger.error("告警名称:{}, 发送异常, 详情:{}".format(alertName, ex))


def main():
    message = "[{}]\n告警名称: ".format(sysTitle) + alert_name + "\n告警时间: {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + "\n告警内容: 👇\n" + alert_msg
    logger.info("传入参数...alert_name:{}, alert_msg:{}, mobiles:{}, emails:{}".format(alert_name, message, mobiles, emails))

    msgContexts = split_string_by_bytes(message)
    tenant_access_token = get_tenant_access_token()
    if tenant_access_token:
        open_ids = get_open_id(tenant_access_token, mobiles.split(","), emails.split(","))
        if len(open_ids) > 0:
            if len(msgContexts) > 5:
                for i in range(0, 5):
                    send_message(tenant_access_token=tenant_access_token, open_ids=open_ids, alertName=alert_name, message=msgContexts[i])
            else:
                for message in msgContexts:
                    send_message(tenant_access_token=tenant_access_token, open_ids=open_ids, alertName=alert_name, message=message)
            print("True")
        else:
            logger.warning("根据手机号或者邮箱查询无相关用户open_id, mobiles:{}, emails:{}".format(mobiles, emails))
            print("False")
    else:
        print("False")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="/opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/FeishuApplicationSoar.py --alert_name '告警测试' --alert_msg '测试' --mobiles 1111111,222222 --emails xxx@qq.com", add_help=True)
    parser.add_argument("--alert_name", type=str, help="告警名称")
    parser.add_argument("--alert_msg", type=str, help="告警信息, 建议以单引号限定, 否则遇到空格会报错")
    parser.add_argument("--mobiles", type=str, help="可选: 手机号, 多手机以,(逗号)分割")
    parser.add_argument("--emails", type=str, help="可选: 邮箱, 多邮箱以,(逗号)分割")
    options = parser.parse_args()

    if not (options.alert_name or options.alert_msg):
        logger.warning("alert_name或者alert_msg参数不能为空")
        print("False")
        parser.print_help()
        sys.exit(1)

    if not (options.mobiles and options.emails):
        logger.warning("mobiles,emails参数不能均为空")
        print("False")
        parser.print_help()
        sys.exit(1)

    if AppId == "" or AppSecret == "":
        logger.warning("AppId或者AppSecret参数不能为空")
        print("False")
        sys.exit(1)

    alert_name = options.alert_name
    alert_msg = options.alert_msg
    mobiles = options.mobiles
    emails = options.emails

    main()