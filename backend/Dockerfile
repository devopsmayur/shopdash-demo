FROM python:latest
WORKDIR /app
RUN apt-get update && apt-get install -y curl git
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY . /app
EXPOSE 5000
CMD ["python", "app.py"]
