FROM pandoc/latex

RUN apk add --update make python3
RUN tlmgr update --self && \
	tlmgr install adjustbox collectbox upquote microtype parskip xurl bookmark \
	footnotehyper pagecolor mdframed zref needspace titling todonotes chngcntr \
	enumitem changepage soul sourcesanspro sourcecodepro ly1 standalone

RUN adduser --no-create-home --disabled-password --gecos '' user
USER user

ENTRYPOINT ["sh", "-c"]
