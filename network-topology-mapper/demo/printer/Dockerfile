FROM alpine:3.19

RUN apk add --no-cache socat

EXPOSE 631 9100

CMD sh -c "socat TCP-LISTEN:631,fork,reuseaddr PIPE & \
           socat TCP-LISTEN:9100,fork,reuseaddr PIPE & \
           wait"
