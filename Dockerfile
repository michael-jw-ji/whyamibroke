FROM python:3.13-slim
ENV WORKDIR=/user/src/app
WORKDIR /user/src/app
RUN mkdir -p $WORKDIR
COPY "requirements.txt" .
RUN apt-get update 
RUN pip install -r requirements.txt
COPY "app.py" $WORKDIR
ENTRYPOINT ["python", "app.py"]

EXPOSE 80
