FROM python:3

WORKDIR /usr/src/nobarrier

COPY requirement.txt .
COPY entrypoint.sh .

RUN pip install -r requirement.txt

RUN chmod +x entrypoint.sh

COPY . .

ENTRYPOINT ["/usr/src/nobarrier/entrypoint.sh"]
