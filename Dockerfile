FROM python:3.10
ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src
RUN pip install -r requirements.txt
