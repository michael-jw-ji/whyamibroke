#FROM python:3.13-slim
#ENV WORKDIR=/user/src/app
#WORKDIR /user/src/app
#RUN mkdir -p $WORKDIR
#COPY "requirements.txt" .
#RUN apt-get update 
#RUN pip install -r requirements.txt
#COPY "app.py" $WORKDIR
#ENTRYPOINT ["python", "app.py"]

#EXPOSE 80

FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    pip install -r requirements.txt && \
    apt-get purge -y build-essential -y && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY . /app

EXPOSE 7000

ENTRYPOINT ["python", "app.py"]
