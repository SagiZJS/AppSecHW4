FROM python:3.7-slim

WORKDIR /app

COPY AppSecHW3/ .

RUN pip3 install flask 

ENV FLASK_APP=app.py

RUN cp /run/secrets/app.py ./app.py

CMD ["flask", "run", "--host=0.0.0.0"]

