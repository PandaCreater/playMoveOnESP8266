import socket
import time
import cv2


def loop_send(client: socket):
    c = 0  # 累计帧数
    timeF = 2  # 隔2帧截一次图，数字越小，播放越细腻(1~99)
    video = cv2.VideoCapture(r"./assets/2.mp4")
    if video.isOpened():  # 判断是否正常打开
        return_value, frame = video.read()  # 返回一个元组，frame是帧对象
    else:
        return_value = False
        exit(1)
    last_time = time.time()
    fps = video.get(cv2.CAP_PROP_FPS)  # 获取帧率
    fpsTime = 1 / fps  # 计算每一帧的所占的时间
    while return_value:  # 循环读取视频帧
        return_value, frame = video.read()
        if return_value is True:
            if c % timeF == 0:  # 每隔timeF帧进行操作
                h, w = frame.shape[:2]
                min_scale = min(h / 64, w / 64)
                resize_h = int(h / min_scale)
                resize_w = int(w / min_scale)  # 计算显示尺寸
                frame = cv2.resize(frame, (resize_w, resize_h))  # 调整尺寸
                # frame = binary_image(frame)  # 调用opencv处理图像（如果是简单的双色图像可以不需要）
                # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)  # 把输入图像灰度化（如果启用了上面的代码的话这句不要）
                cut_w = int((resize_w - 64) / 2)
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
                pix = 0
                messageArray = []
                for row in range(0, 64):
                    for col in range(0, 64):
                        r = cut_frame[row][col][2]
                        g = cut_frame[row][col][1]
                        b = cut_frame[row][col][0]
                        pix = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                        pix1 = pix >> 8
                        pix2 = pix & 0xFF
                        messageArray.append(pix1)
                        messageArray.append(pix2)

                client.sendall(bytes(messageArray))

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
                # 在屏幕上显示当前的图片（有点影响效率）
                cv2.imshow('image', cut_frame)
                cv2.waitKey(1)
            c = c + 1


if __name__ == '__main__':
    # Set the server's IP address and port
    server_ip = '0.0.0.0'  # Listen on all network interfaces
    server_port = 13235  # Port number to listen on

    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the address and port
    server_socket.bind((server_ip, server_port))

    # Listen for incoming connections
    server_socket.listen(2)

    print(f"Server is listening on {server_ip}:{server_port}")

    try:
        while True:
            # Wait for a connection
            print('Waiting for a connection...')
            connection, client_address = server_socket.accept()

            try:
                print(f"Connection from {client_address}")
                loop_send(connection)
            finally:
                # Clean up the connection
                connection.close()
    except KeyboardInterrupt:
        # Gracefully close the server on keyboard interrupt (Ctrl+C)
        print("\nServer shutting down.")
        server_socket.close()
