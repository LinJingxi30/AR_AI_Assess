# 使用官方 Node.js 镜像作为基础镜像
FROM python:3.10-slim

# 安装 Python
RUN apt-get update 
RUN apt-get install -y  curl 
# RUN apt-get install -y python3 python3-pip
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 验证安装
RUN node --version && npm --version

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY . .

# 安装 Node.js 依赖
RUN npm install
RUN pip3 install -r requirements.txt

# 暴露应用端口
EXPOSE 8000

# 设置容器启动时的默认命令
CMD ["node", "server.js"]
