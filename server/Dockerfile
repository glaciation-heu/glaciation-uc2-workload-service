FROM python:3.9-alpine3.19
WORKDIR /app
COPY ./workload /app
RUN mkdir -p /home/ubuntu/UC/data
RUN apk update
RUN apk add linux-headers make automake gcc g++ subversion python3-dev
RUN pip install -r requirements.txt
CMD ["python", "./workload.py", "-t", "-r", "1000000"]
