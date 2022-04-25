run:
	make install
	python run.py

install:
	pip install -r requirements.txt

build:
	docker build -t antigen-bot:0.1 .
	docker build -t antigen-bot:latest . 
