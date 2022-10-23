# From指定基础镜像(Base Image)
FROM python:3.7-slim

# 创建镜像里面的根目录
WORKDIR /app

# 当前目录所有文件拷贝到路径中: . 到 .
COPY . .


# 时区设置，统一使用，不用改
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# RUN指定创建镜像时安装依赖路径（清华源）
# RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
# RUN pip install --trusted-host https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# CMD指定运行容器时运行Py文件
CMD ["python","main.py"]