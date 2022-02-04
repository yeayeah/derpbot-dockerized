FROM scratch
ADD rootfs.tar.xz /
RUN wget http://pkg.comploti.st/pack/netbsd-curses_x86_64_8.tar.xz
RUN butch unpack netbsd-curses_x86_64_8.tar.xz && rm netbsd-curses_x86_64_8.tar.xz
RUN butch install termcap
RUN wget http://pkg.comploti.st/pack/python_x86_64_12.tar.xz
RUN butch unpack python_x86_64_12.tar.xz && rm python_x86_64_12.tar.xz
RUN wget http://pkg.comploti.st/pack/python-beautifulsoup4_x86_64_1.tar.xz
RUN butch unpack python-beautifulsoup4_x86_64_1.tar.xz && rm python-beautifulsoup4_x86_64_1.tar.xz
RUN busybox addgroup -S derpbot && busybox adduser -h /home/derpbot -S -G derpbot derpbot
COPY derpbot/ /home/derpbot
#RUN mkdir /home/derpbot/data /home/derpbot/plugins && chown derpbot:derpbot /home/derpbot/data /home/derpbot/plugins
USER derpbot
#COPY derpbot/plugins-default/ /home/derpbot/plugins/
WORKDIR /home/derpbot
CMD ["/opt/python/bin/python", "/home/derpbot/derpbot.py", "--dockerized", "1"]
