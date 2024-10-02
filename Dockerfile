FROM python:3.12.5

WORKDIR /star-chatbot-admin

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt


COPY . .

CMD [ "python3", "main.py" ]