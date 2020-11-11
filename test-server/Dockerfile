FROM python:3.7-alpine
COPY . /app
WORKDIR /app
ENV FLASK_APP=test-server.py
ENV FLASK_RUN_HOST=0.0.0.0
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["flask", "run"]