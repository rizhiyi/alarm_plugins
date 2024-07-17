# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     WeworkApplicationManager.py
   Description :     企业微信应用告警推送_Manager版
   Author      :     chen.fei
   Email       :     jcciam@outlook.com
   Date        :     2024/4/11 10:13
-------------------------------------------------
"""
import logging.config
from datetime import datetime
import json
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
    "name": "WeworkApplicationManager",
    "version": 1,
    "alias": "企业微信-应用消息告警",
    "configs": [
        {
          "name": "phones",
          "alias": "(二选一)@指定接收人[手机号, 多个以,号分割]",
          "value_type": "string",
          "default_value": "",
          "style": {
            "rows": 1,
            "columns": 15
          }
        },{
          "name": "user_id",
          "alias": "(二选一)用户ID[多个以,号分割]",
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
            "name": "corpid",
            "alias": "企业id(corpid)",
            "presence": True,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 60
            }
        },{
            "name": "agentid",
            "alias": "应用id(agentid)",
            "presence": True,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 60
            }
        },{
            "name": "secret",
            "alias": "应用秘钥(secret)",
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


def _get_token(corpid, secret):
    """
    获取access token
    Returns:

    """
    try:
        url = url_prefix + "/gettoken?corpid={}&corpsecret={}".format(corpid, secret)
        resp = requests.get(url, verify=False, timeout=30, proxies=proxies)
        if resp.status_code == 200:
            resp_json = resp.json()
            if resp_json["errcode"] == 0:
                access_token = resp_json["access_token"]
                logger.info("获取Token成功, access_token: {}".format(access_token))
                return access_token
            errmsg = resp_json["errmsg"]
            logger.error("获取Token失败! errmsg: {}".format(errmsg))
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


def send_message(agentid, user_id, access_token, title, SmsMsg):
    msg = "[{}Manager]\n".format(sysTitle) + "告警名称:  " + title + '\n' + SmsMsg

    url = url_prefix + "/message/send?access_token={}".format(access_token)
    payload = {
        "touser": user_id,
        "msgtype": "text",
        "agentid": agentid,
        "text": {
            "content": msg
        }
    }
    try:
        logger.info("告警内容:{}".format(msg))
        resp = requests.post(url, data=json.dumps(payload), verify=False, timeout=30, proxies=proxies)
        logger.info("推送返回结果:{}".format(resp.text))
    except Exception as ex:
        logger.error("发送异常, 详情:{}".format(ex))


def handle(meta, alert):
    param_configs = meta.get("param_configs")
    param_configs = convert_config(param_configs)
    corpid = param_configs.get("corpid", "")
    agentid = param_configs.get("agentid", "")
    secret = param_configs.get("secret", "")
    if not corpid or not agentid or not secret:
        logger.error("corpid或agentid或secret不能为空")
        return False

    configs = meta.get("configs")
    configs = convert_config(configs)
    user_id = configs.get("user_id", "").replace("，", "")
    phones = configs.get("phones", "").replace("，", "")

    if len(user_id) == 0 and len(phones) == 0:
        logger.error("user_id和phones不能同时为空")
        return False

    access_token = _get_token(corpid, secret)
    if access_token:
        title, content = gen_content(alert)
        logger.info("user_id:{}, Title:{}, Content:{}, Phones:{}".format(user_id, title, content, phones))
        if len(user_id) > 0:
            if user_id == "all":
                users_str = "@all"
            else:
                users_str = "|".join(user_id.split(","))
        else:
            try:
                users_str = _get_user_id(phones.split(","), access_token)
                if len(users_str) == 0:
                    logger.error("获取用户id失败, 不执行发送")
                    return False
            except Exception as e:
                logger.error("请输入正确手机号, 多个手机号请以逗号分割, 当前配置内容为:{}".format(phones))
                return False
        send_message(agentid, users_str, access_token, title, content)
