# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     FeishuWebhookManager
   Description :     
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2024/4/12
-------------------------------------------------
"""
import base64
import hashlib
import hmac
import logging.config
from datetime import datetime
import time
import requests
from common.plugin_util import convert_config


###########公共参数##############################################
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
  'http': '',
  'https': '',
}
url_prefix = "https://open.feishu.cn/open-apis"
################################################################

logger = logging.getLogger(__name__)

META = {
    "name": "FeishuWebhookManager",
    "version": 1,
    "alias": "飞书-自定义机器人群消息告警",
    "configs": [],
    "param_configs": [
            {
                "name": "WebhookKey",
                "alias": "群机器人Webhook的Token",
                "presence": True,
                "value_type": "string",
                "default_value": "",
                "style": {
                    "rows": 1,
                    "cols": 60
                }
            },{
                "name": "SignSecret",
                "alias": "(可选)签名校验",
                "presence": False,
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
    timestamp = str(int(time.time()))
    # 拼接timestamp和secret
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    # 对结果进行base64处理
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return timestamp, sign


def send_message(webhook_token, secret, title, message):
    """
    推送消息
    @param webhook_token:
    @param secret:
    @param title:
    @param message:
    @return:
    """
    message = "[日志平台Manager]\n" + "告警名称: " + title + '\n' + message

    url = url_prefix + "/bot/v2/hook/{}".format(webhook_token)
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
        logger.info("告警名称:{}, 推送消息成功, 内容:{}, 返回结果:{}".format(title, message, response.text))
    except Exception as e:
        logger.error("告警名称:{}, 推送消息失败, 内容:{}, 抛出错误:{}".format(title, message, e))


def handle(meta, alert):
    param_configs = meta.get("param_configs")
    param_configs = convert_config(param_configs)
    WebhookKey = param_configs.get("WebhookKey", "")
    SignSecret = param_configs.get("SignSecret", "")

    if WebhookKey == "":
        logger.error("webhook地址不能为空")
        return False

    try:
        title, content = gen_content(alert)
        logger.info("WebhookKey:{}, Title:{}, Content:{}".format(WebhookKey, title, content))
        send_message(WebhookKey, SignSecret, title, content)
    except Exception as e:
        logger.exception("插件运行异常, %s" % e)
        raise e