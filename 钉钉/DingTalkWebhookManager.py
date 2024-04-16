# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     DingTalkWebhookManager
   Description :     自定义机器人推送消息到群聊_Manager版
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2024/4/12
-------------------------------------------------
"""
import logging.config
from datetime import datetime
import json
import time
import requests
import hmac
import hashlib
import base64
import urllib.parse
from common.plugin_util import convert_config

###########公共参数##############################################
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
  'http': '',
  'https': '',
}
url_prefix = "https://oapi.dingtalk.com"
################################################################

logger = logging.getLogger(__name__)


META = {
    "name": "DingTalkWebhookManager",
    "version": 1,
    "alias": "钉钉-自定义机器人群消息告警",
    "configs": [
        {
          "name": "phones",
          "alias": "(可选)@指定接收人[手机号, 多个以,号分割]",
          "value_type": "string",
          "default_value": "",
          "style": {
            "rows": 1,
            "columns": 15
          }
        }
    ],
    "param_configs": [
        {
            "name": "access_token",
            "alias": "Access_token",
            "presence": True,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 60
            }
        },{
            "name": "secret",
            "alias": "加签密钥(Secret), 可选",
            "presence": True,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 60
            }
        }
    ]
}


def gen_content(alert):
    final_alert = {}
    module = alert.get("Module", "")
    type = alert.get("Type", "")
    ip = alert.get("Ip", "")
    alarm_time = alert.get("Time", "")
    if alarm_time == "":
        alarm_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    detail = alert.get("Detail", "")
    recovery = alert.get("Recover", "")
    if recovery == "True" or recovery == True:
        recovery = u"恢复"
        recoveryString = u"告警已恢复: "
    else:
        recovery = u""
        recoveryString = u""

    if module != "" and ip != "":
        title = u"%s %s %s%s通知" % (ip, module, type, recovery)
        content = u"%s告警类型: %s\n告警模块: %s\n告警IP: %s\n告警时间: %s\n告警详情: %s" % (recoveryString, type, module, ip, alarm_time, detail)
    elif ip != "":
        title = u"%s %s%s通知" % (ip, type, recovery)
        content = u"%s告警类型: %s\n告警IP: %s\n告警时间: %s\n告警详情: %s" % (recoveryString, type, ip, alarm_time, detail)
    else:
        title = u"%s%s通知" % (type, recovery)
        content = u"%s告警类型: %s\n告警时间: %s\n告警详情: %s" % (recoveryString, type, alarm_time, detail)

    return title, content


def gen_timestamp_sign(secret):
    """
    生成签名
    @param secret:
    @return:
    """
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode("utf-8")
    string_to_sign = "{}\n{}".format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode("utf-8")
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def send_message(secret, access_token, title, message, phones):
    message = "[日志平台Manager]\n" + "告警名称:  " + title + '\n' + message

    if secret:
        timestamp, sign = gen_timestamp_sign(secret)
        url = url_prefix + "/robot/send?access_token={}&timestamp={}&sign={}".format(access_token, timestamp, sign)
    else:
        url = url_prefix + "/robot/send?access_token={}".format(access_token)
    header = {
        "Content-Type": "application/json"
    }
    if len(phones) > 0:
        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            },
            "at": {
                "atMobiles": phones
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
        logger.info("告警内容:{}".format(message))
        resp = requests.post(url, data=json.dumps(payload), headers=header, verify=False, timeout=30, proxies=proxies)
        logger.info("推送返回结果:{}".format(resp.text))
    except Exception as ex:
        logger.error("发送异常, 详情:{}".format(ex))


def handle(meta, alert):
    param_configs = meta.get("param_configs")
    param_configs = convert_config(param_configs)
    access_token = param_configs.get("access_token", "")
    secret = param_configs.get("secret", "")
    if not access_token:
        logger.error("access_token不能为空")
        return False

    configs = meta.get("configs")
    configs = convert_config(configs)
    phones = configs.get("phones", "").replace("，", "").split(",")

    title, content = gen_content(alert)
    send_message(secret, access_token, title, content, phones)
