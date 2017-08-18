FROM python:3.6
RUN pip install glances docker
COPY glances.ini /app/glances.ini

CMD glances -C /app/glances.ini --export-csv /tmp/glances.csv
