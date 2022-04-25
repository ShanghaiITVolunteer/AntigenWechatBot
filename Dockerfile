FROM python:3.9

WORKDIR /antigenbot

# cache the building stage of docker
COPY requirements.txt requirements.txt
COPY Makefile Makefile
RUN make install

ENV IN_DOCKER=true

COPY . .

CMD [ "make", "run"]