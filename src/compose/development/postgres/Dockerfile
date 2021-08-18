FROM postgres:12.3

COPY ./compose/development/postgres/maintenance /usr/local/bin/maintenance
RUN chmod +x /usr/local/bin/maintenance/*
RUN mv /usr/local/bin/maintenance/* /usr/local/bin \
    && rmdir /usr/local/bin/maintenance

COPY ./collation/latin /usr/share/locale/latin/LC_COLLATION
RUN gunzip -c -k /usr/share/i18n/charmaps/UTF-8.gz > /usr/share/locale/UTF-8
RUN localedef -i /usr/share/locale/latin/LC_COLLATION -f /usr/share/locale/UTF-8 latin
