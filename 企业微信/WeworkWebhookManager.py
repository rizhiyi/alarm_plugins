# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     WeworkWebhookManager.py
   Description :     企业微信manager告警插件
   Author      :     chen.fei
   Email       :     chen.fei@yottabyte.cn
   Date        :     2024/4/11 10:13
-------------------------------------------------
"""
import logging.config
from datetime import datetime

import requests
from common.plugin_util import convert_config


###########公共参数##############################################
# 日志平台名称
sysTitle = "日志平台"
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
  'http': '',
  'https': '',
}
url_prefix = "https://qyapi.weixin.qq.com/cgi-bin"
################################################################

logger = logging.getLogger(__name__)

META = {
    "name": "WeworkWebhookManager",
    "version": 1,
    "alias": "企业微信-群消息告警",
    "configs": [
        {
          "name": "phones",
          "alias": "(可选项)@指定接收人[手机号, 多个以,号分割]",
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
                "name": "WebhookKey",
                "alias": "群机器人Webhook的key",
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


def send_message(sendKey, title, SmsMsg, phones):
    message = "[{}Manager]\n".format(sysTitle) + "告警名称: " + title + '\n' + SmsMsg

    url = url_prefix + "/webhook/send?key={}".format(sendKey)
    header = {
        "Content-Type": "application/json"
    }
    if len(phones) > 0:
        payload = {
            "msgtype": "text",
            "text": {
                "content": message,
                "mentioned_mobile_list": phones
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
        logger.info("告警名称:{}, 推送消息成功, 内容:{}, 返回结果:{}".format(title, SmsMsg, response.text))
    except Exception as e:
        logger.error("告警名称:{}, 推送消息失败, 内容:{}, 抛出错误:{}".format(title, SmsMsg, e))


def handle(meta, alert):
    param_configs = meta.get("param_configs")
    if param_configs is None:
        logger.error("No param_configs in meta param")
        return False

    param_configs = convert_config(param_configs)
    WebhookKey = param_configs.get("WebhookKey", "")

    configs = meta.get("configs")
    configs = convert_config(configs)
    phones = configs.get("phones", "").replace("，", ",").split(",")

    if WebhookKey == "":
        logger.error("webhook地址不能为空")
        return False

    try:
        title, content = gen_content(alert)
        logger.info("WebhookKey:{}, Title:{}, Content:{}, phones:{}".format(WebhookKey, title, content, phones))
        send_message(WebhookKey, title, content, phones)
    except Exception as e:
        logger.exception(("alert.plugins.guilinBankSMSManager got exception %s") % e)
        raise e