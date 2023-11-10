FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1

RUN mkdir /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && apt-get install -y libpq-dev gcc pkg-config \
    && apt-get install -y default-libmysqlclient-dev \
    && apt-get install -y python3-dev build-essential

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install wheel setuptools pip --upgrade

RUN pip install -r requirements.txt
RUN pip install mysqlclient

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]