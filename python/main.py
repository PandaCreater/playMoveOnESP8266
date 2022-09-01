import cv2
import numpy as np
import socket
import time
import random


def binary_image(image):  # 将图像处理为二值化的程序
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)  # 把输入图像灰度化
    h, w = gray.shape[:2]
    m = np.reshape(gray, [1, w * h])
    mean = m.sum() / (w * h)
    ret, binary = cv2.threshold(gray, mean, 255, cv2.THRESH_OTSU)
    return binary


pattern = [
    [0, 32, 8, 40, 2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21]
]
c = 0  # 累计帧数
timeF = 2  # 隔2帧截一次图，数字越小，播放越细腻(1~99)
video = cv2.VideoCapture(r"./assets/BadApple.mp4")

UDP_IP = "192.168.30.104"  # 单片机的ip地址（自行修改单片机有显示地址）
UDP_PORT = 4210  # 单片机的UDP端口

print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

if video.isOpened():  # 判断是否正常打开
    return_value, frame = video.read()  # 返回一个元组，frame是帧对象
else:
    return_value = False
    exit(1)
last_time = time.time()
fps = video.get(cv2.CAP_PROP_FPS)  # 获取帧率
fpsTime = 1 / fps # 计算每一帧的所占的时间
while return_value:  # 循环读取视频帧
    return_value, frame = video.read()
    if return_value is True:
        if c % timeF == 0:  # 每隔timeF帧进行操作
            h, w = frame.shape[:2]
            min_scale = min(h / 64, w / 128)
            resize_h = int(h / min_scale)
            resize_w = int(w / min_scale)  # 计算显示尺寸
            frame = cv2.resize(frame, (resize_w, resize_h))  # 调整尺寸
            # frame = binary_image(frame)  # 调用opencv处理图像（如果是简单的双色图像可以不需要）
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)  # 把输入图像灰度化（如果启用了上面的代码的话这句不要）
            cut_w = int((resize_w - 128) / 2)
            cut_h = int((resize_h - 64) / 2)
            # 截取（128 * 64）的内容，如内容不是128*64自行+-1
            cut_frame = frame[0 + cut_h: resize_h - cut_h, 0 + cut_w: resize_w - cut_w]

            # 先转换成二进制的类型再换算成bytes类型主要目的是节约单次发送的数据长度
            # 8个像素点为一个byte
            # 移位 像素点位置<<位数
            # 0<<7
            # 1<<6
            # 2<<5
            # ....
            # 7<<0
            b = 8
            pix = 0
            messageArray = []
            for row in range(0, 64):
                for col in range(0, 128):
                    b -= 1
                    
                    # 二值化
                    if cut_frame[row][col] > 117:
                        pix += 1 << b

                    # 以下图像处理选择显示最适合的即可（抖动模仿显示不同深度的颜色，具体原理可以参照 https://en.wikipedia.org/wiki/Dither）
                    # # 随机抖动
                    # if random.randint(-50, 50) + cut_frame[row][col] > 117:
                    #     pix += 1 << b

                    # # 有序抖动
                    # if cut_frame[row][col] / 4.0 > pattern[row % 8][col % 8]:
                    #     pix += 1 << b

                    # # 误差扩散 Floyd_Steinberg（非常非常非常非常慢，没有具体验证正确与否）
                    # old_c = cut_frame[row][col]
                    # new_c = old_c > 117 if 225 else 0
                    # cut_frame[row][col] = new_c
                    # error = old_c - new_c
                    # if col != 128 - 1:
                    #     cut_frame[row][col + 1] = int(cut_frame[row][col + 1] + error * 7.0 / 16.0)
                    # if row != 64 - 1 and col != 0:
                    #     cut_frame[row + 1][col - 1] = int(cut_frame[row + 1][col - 1] + error * 3.0 / 16.0)
                    # if row != 64 - 1:
                    #     cut_frame[row + 1][col] = int(cut_frame[row + 1][col] + error * 5.0 / 16.0)
                    # if row != 64 - 1 and col != 128 - 1:
                    #     cut_frame[row + 1][col + 1] = int(cut_frame[row + 1][col + 1] + error * 1.0 / 16.0)
                    #
                    # if cut_frame[row][col] > 117:
                    #     pix += 1 << b

                    if b == 0:
                        b = 8
                        messageArray.append(pix)
                        pix = 0

            # 发送数据
            s.sendto(bytes(messageArray), (UDP_IP, UDP_PORT))
            # 获取当前时间
            currentTime = time.time()
            # 判断是否需要等待播放时间
            time_wait = last_time + fpsTime * timeF - currentTime
            if time_wait > 0:
                time.sleep(time_wait)
            else:
                # 这个log如果有很多说明电脑性能不够，建议把timeF改大点，不然播放会有延迟
                print('please change timeF bigger')

            # 更新最后一帧时间
            last_time = time.time()
            messageArray = []
            # # 在屏幕上显示当前的图片（有点影响效率）
            # cv2.imshow('image', cut_frame)
            # cv2.waitKey(1)
        c = c + 1
