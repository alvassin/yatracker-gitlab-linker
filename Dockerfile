########################################################################
FROM snakepacker/python:all as builder

RUN python3.11 -m venv /usr/share/python3/app
RUN /usr/share/python3/app/bin/pip install -U pip setuptools wheel

ADD dist/ /mnt/dist/
RUN /usr/share/python3/app/bin/pip install --no-cache-dir /mnt/dist/*.whl
RUN /usr/share/python3/app/bin/pip check

RUN find-libdeps /usr/share/python3/app > /usr/share/python3/app/pkgdeps.txt

########################################################################
FROM snakepacker/python:3.11 as app

COPY --from=builder /usr/share/python3/app /usr/share/python3/app
RUN ln -snf /usr/share/python3/app/bin/yatracker-linker /usr/bin/

CMD ["yatracker-linker"]
