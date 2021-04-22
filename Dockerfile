FROM ubuntu:18.04

EXPOSE 80

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get -y install apache2
RUN apt-get -y install python3
RUN apt-get -y install python3-pil python3-matplotlib python3-scipy python3-sklearn python3-pip

#enable cgi in the website root
#second block to allow .htaccess
RUN echo "                                    \n \
TimeOut 1200                                  \n \
<Directory '/var/www/html'>                   \n \
   DirectoryIndex index.html                  \n \
</Directory>" >> /etc/apache2/apache2.conf

RUN mkdir /var/www/cgi-bin
COPY var/www/html /var/www/html
COPY var/www/cgi-bin /usr/lib/cgi-bin
RUN chown -R www-data:www-data /var/www /usr/lib/cgi-bin
RUN chmod -R u+rwx,g+x,o+x /var/www/cgi-bin /usr/lib/cgi-bin

#load apache cgi module
RUN a2enmod cgi
RUN service apache2 restart
RUN ln -sf /usr/bin/python /usr/local/bin/python
RUN pip3 install requests

CMD /usr/sbin/apache2ctl -D FOREGROUND