FROM alpine:3.19

RUN apk add --no-cache openssh-server socat \
    && ssh-keygen -A \
    && echo "PermitRootLogin yes" >> /etc/ssh/sshd_config \
    && echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config \
    && echo "root:demo" | chpasswd

EXPOSE 22 139 445

CMD sh -c "socat TCP-LISTEN:139,fork,reuseaddr PIPE & \
           socat TCP-LISTEN:445,fork,reuseaddr PIPE & \
           /usr/sbin/sshd -D"
