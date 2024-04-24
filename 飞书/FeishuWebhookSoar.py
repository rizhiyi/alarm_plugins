# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     FeishuWebhookSoar.py
   Description :     飞书-自定义机器人群消息告警SOAR
   Author      :     chen.fei
   Email       :     chen.fei@yottabyte.cn
   Date        :     2024/4/23 下午2:42
-------------------------------------------------
"""
import argparse
import base64
import hashlib
import hmac
import logging
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
import urllib3

###########公共参数##############################################
# 兜底机器人token，监控项未配置则使用该配置项
webhook_token = ""
# (可选)兜底机器人签名校验，监控项未配置则使用该配置项
webhook_secret = ""
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
handler = RotatingFileHandler('/data/rizhiyi/logs/soar/FeishuWebhookSoar.log', maxBytes=100 * 1024 * 1024, backupCount=5, encoding='utf-8')
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


def gen_timestamp_sign(secret):
    """
    生成签名
    @param secret:
    @return:
    """
    timestamp = str(int(time.time()))
    # 拼接timestamp和secret
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    # 对结果进行base64处理
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return timestamp, sign


def send_message(alert_name, message, token, secret):
    """
    推送消息
    Args:
        alert_name: 告警名称
        message: 推送消息
        token: 机器人key
        secret: 加签密钥
    Returns:

    """
    url = url_prefix + "/bot/v2/hook/{}".format(token)
    header = {
        "Content-Type": "application/json"
    }
    if secret:
        timestamp, sign = gen_timestamp_sign(secret)
        payload = {
            "timestamp": str(timestamp),
            "sign": sign,
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
    else:
        payload = {
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
    try:
        response = requests.request("POST", url=url, headers=header, json=payload, timeout=30, proxies=proxies)
        logger.info("告警名称:{}, 推送消息成功, 内容:{}, 返回结果:{}".format(alert_name, message, response.text))
    except Exception as e:
        logger.error("告警名称:{}, 推送消息失败, 内容:{}, 抛出错误:{}".format(alert_name, message, e))


def main():
    message = "[SIEM平台]\n告警名称: " + alert_name + "\n告警时间: {}".format(
        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + "\n告警内容: 👇\n" + alert_msg
    logger.info("传入参数...alert_name:{}, alert_msg:{}, mobiles:{}".format(alert_name, message, mobiles))

    msgContexts = split_string_by_bytes(message)
    if len(msgContexts) > 5:
        for i in range(0, 5):
            send_message(alert_name=alert_name, message=msgContexts[i], token=access_token, secret=secret)
    else:
        for message in msgContexts:
            send_message(alert_name=alert_name, message=message, token=access_token, secret=secret)
    print("True")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="/opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/FeishuWebhookSoar.py --alert_name '告警测试' --alert_msg '测试' --webhoook_token xxxx --sign_secret xxxx", add_help=True)
    parser.add_argument("--alert_name", type=str, help="告警名称")
    parser.add_argument("--alert_msg", type=str, help="告警信息, 建议以单引号限定, 否则遇到空格会报错")
    parser.add_argument("--webhoook_token", type=str, help="可选: 自定义机器人AccessToken")
    parser.add_argument("--sign_secret", type=str, help="可选: 签名校验")
    options = parser.parse_args()

    if not (options.alert_name or options.alert_msg):
        logger.warning("alert_name或者alert_msg参数不能为空")
        print("False")
        parser.print_help()
        sys.exit(1)

    if webhook_token == "" and options.webhoook_token is not None:
        logger.warning("webhook_token参数不能为空")
        print("False")
        parser.print_help()
        sys.exit(1)

    alert_name = options.alert_name
    alert_msg = options.alert_msg
    mobiles = options.mobiles
    access_token = options.webhoook_token if options.webhoook_token else webhook_token
    secret = options.sign_secret if options.sign_secret else webhook_secret

    main()
