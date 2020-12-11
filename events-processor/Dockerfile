FROM  python:3 

WORKDIR /usr/src/app

RUN sed -i -e 's/v3\.4/edge/g' /etc/apk/repositories \
    && apk upgrade --update-cache --available \
    && apk --no-cache add librdkafka

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python3", "./app.py" ]
