build:
 echo Building
 docker build -t shopdash .

run:
 docker run -p 5000:5000 shopdash

deploy:
 bash scripts/deploy.sh
