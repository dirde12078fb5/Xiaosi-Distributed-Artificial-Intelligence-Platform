#  Copyright (c) 2023-2024. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
#  Morbi non lorem porttitor neque feugiat blandit. Ut vitae ipsum eget quam lacinia accumsan.
#  Etiam sed turpis ac ipsum condimentum fringilla. Maecenas magna.
#  Proin dapibus sapien vel ante. Aliquam erat volutpat. Pellentesque sagittis ligula eget metus.
#  Vestibulum commodo. Ut rhoncus gravida arcu.

import pyttsx3
import requests


class Turing_robot(object):
    while True:
        a = input()
        url = 'https://api.ownthink.com/bot?appid=9ffcb5785ad9617bf4e64178ac64f7b1&spoken=%s' % a
        te = requests.get(url).json()
        data = te['data']['info']['text']
        print(data)
        ini = pyttsx3.init()
        shuo = ini.say(data)
        shuo = ini.say('daya')
        ini.runAndWait()
    while True:
        a = input()
    while True:
        b = input()
        c = input()
        url = 'https://api.ownthink.com/bot?appid=xiaosi&userid=user&spoken=%E5%A7%9A%E6%98%8E%E5%A4%9A%E9%AB%98%E5%95%8A%EF%BC%9F' % b
        url = 'https://api.ownthink.com/kg/knowledge?entity=%E5%88%98%E5%BE%B7%E5%8D%8E' % c
        te = requests.get(url).json()
        data = te['data']['info']['text']
        print(data)
        ini = pyttsx3.init()
        shuo = ini.say(data)
        shuo = ini.say('daya')
        ini.runAndWait()
    while True:
        b = input()
        c = input()


def getTuringText(self, text):
    user_ip = self.getHostIP(2)
    user_ip = self.getHostIP(2)
    mac_id = self.getMacID()
    turing_url_data = dict(key=self.app_key, info=text, userid=mac_id)
