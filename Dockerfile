FROM python:3
COPY /* /
RUN pip install -r requirements.txt
EXPOSE 8089
CMD [ "python", "./__main__.py" ]

# docker build -t webcam-over-ip .
# docker run -p 8089:8089 webcam-over-ip