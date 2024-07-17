# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     WeworkWebhookSoar.py
   Description :     企业微信群聊机器人告警推送SOAR
   Author      :     chen.fei
   Email       :     chen.fei@yottabyte.cn
   Date        :     2024/4/23 下午2:41
-------------------------------------------------
"""
import argparse
import logging
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
import urllib3

###########公共参数##############################################
# SIEM平台名称
sysTitle = "SIEM平台"
# 兜底机器人key, 监控项未配置则使用该配置项
webhook_key = ""
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
handler = RotatingFileHandler('/data/rizhiyi/logs/soar/WeworkWebhookSoar.log', maxBytes=100 * 1024 * 1024, backupCount=5, encoding='utf-8')
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


def send_message(alert_name, message, sendKey, mobiles):
    """
    推送消息
    Args:
        alertName: 告警名称
        message: 推送消息
        sendKey: 机器人key
        phones: 群艾特成员
    Returns:

    """
    url = url_prefix + "/webhook/send?key={}".format(sendKey)
    header = {
        "Content-Type": "application/json"
    }
    if len(mobiles) > 0:
        payload = {
            "msgtype": "text",
            "text": {
                "content": message,
                "mentioned_mobile_list": mobiles
            }
        }
    else:
        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
    try:
        response = requests.request("POST", url=url, headers=header, json=payload, timeout=30, proxies=proxies)
        logger.info("告警名称:{}, 推送消息成功, 内容:{}, 返回结果:{}".format(alert_name, message, response.text))
    except Exception as e:
        logger.exception("告警名称:{}, 推送消息失败, 内容:{}, 抛出错误:{}".format(alert_name, message, e))


def main():
    message = "[{}]\n告警名称: ".format(sysTitle) + alert_name + "\n告警时间: {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + "\n告警内容: 👇\n" + alert_msg
    logger.info("传入参数...alert_name:{}, alert_msg:{}, mobiles:{}".format(alert_name, message, mobiles))
    send_message(alert_name=alert_name, message=message, sendKey=webhook_key, mobiles=mobiles.split(","))
    print("True")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="/opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/WeworkWebhookSoar.py --alert_name '告警测试' --alert_msg '测试' --mobiles 1111111,222222 --key xxxxxxxxxxxxxx", add_help=True)
    parser.add_argument("--alert_name", type=str, help="告警名称")
    parser.add_argument("--alert_msg", type=str, help="告警信息, 建议以单引号限定, 否则遇到空格会报错")
    parser.add_argument("--mobiles", type=str, help="可选: 手机号, 多手机以,(逗号)分割")
    parser.add_argument("--key", type=str, help="可选: 群机器人Webhook Key")
    options = parser.parse_args()

    if not (options.alert_name or options.alert_msg):
        logger.warning("alert_name或者alert_msg参数不能为空")
        print("False")
        parser.print_help()
        sys.exit(1)

    alert_name = options.alert_name
    alert_msg = options.alert_msg
    mobiles = options.mobiles
    webhook_key = options.key if options.key else webhook_key

    main()