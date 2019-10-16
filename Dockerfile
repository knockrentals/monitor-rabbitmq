FROM python:3.7-slim
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN mkdir /code
WORKDIR /code

COPY requirements.txt /code

RUN pip install -r requirements.txt

COPY . /code

ENTRYPOINT [ "/code/entrypoint.sh" ]

CMD ["python", "app.py"]

