FROM python:3.6
RUN pip install git+https://github.com/tarekziade/glances.git#egg=glances
RUN pip install docker
COPY glances.ini /app/glances.ini

CMD glances -C /app/glances.ini --export-csv /app/data/glances.csv
