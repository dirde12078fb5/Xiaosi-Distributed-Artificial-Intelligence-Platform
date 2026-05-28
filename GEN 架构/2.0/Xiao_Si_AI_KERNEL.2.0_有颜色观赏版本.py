#  Copyright (c) 2024. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
#  Morbi non lorem porttitor neque feugiat blandit. Ut vitae ipsum eget quam lacinia accumsan.
#  Etiam sed turpis ac ipsum condimentum fringilla. Maecenas magna.
#  Proin dapibus sapien vel ante. Aliquam erat volutpat. Pellentesque sagittis ligula eget metus.
#  Vestibulum commodo. Ut rhoncus gravida arcu.
import json
import pyttsx3
import requests
xiao_si = pyttsx3.init()
print('\033[1;36mXiaosi Artificial Intelligence Program\033[0m')
print('\033[1;31m版本所有权 -- 更新查看网址 --\033[0m')
print('\033[1;31mhttps://gitee.com/dirde12078904/xiao-si/releases\033[0m')
print('--- Hello Tis is Xiao_Si_Kernel_2.0 --- ')
API_KEY = "2iU0QJiVJBQqCKOLW5Jf8aS9"
SECRET_KEY = "Aqg401HImuqRaprlpctYDLO1TnkClH6c"


def main():
    print('\033[1;36m作为你的智能伙伴，我既能写文案、想点子，又能陪你聊天、答疑解惑\033[0m')
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=" + get_access_token()
    while (1):
        s = input()
        # 注意message必须是奇数条
        payload = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": s
                }
            ]
        })
        headers = {
            'Content-Type': 'application/json'
        }

        res = requests.request("POST", url, headers=headers, data=payload).json()
        print(res['result'])
        xiao_si.say(res['result'])
        xiao_si.runAndWait()
        print('\033[1;37m内容由AI生成，无法确保真实准确，仅供参考\033[0m')


def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))


if __name__ == '__main__':
    main()
