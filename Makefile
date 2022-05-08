run:
	make install
	python3 run.py

install:
	pip3 install -r requirements.txt

build:
	docker build -t antigen-bot:latest . 
	