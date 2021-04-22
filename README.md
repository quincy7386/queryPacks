This build process will enable you to demo the Live Query API's capabilities as see in this [video](https://onevmw.sharepoint.com/teams/SBUTechnicalSolutionOrganization/SitePages/Selling-Beyond-Security.aspx). 

Make sure you have installed the Docker Desktop from [here](https://www.docker.com/products/docker-desktop).

After you pull down this repo, you need to edit the `var/www/cgi-bin/credentials.psc` file and add your credentials, and ORG key. 

Next you will build the image for the container, and you will only need to do this once, which will take
a few minutes to complete. You might see some errors, but they can be ignored for the most part. Here is the build command:

    docker build . -t ubuntu-18.04

In the last two rows of messages you will find the image ID:

```
Removing intermediate container be9fd0ae4dc0
 ---> dd8a05f1e433
Step 18/18 : CMD /usr/sbin/apache2ctl -D FOREGROUND
 ---> Running in e17a5a699f0c
Removing intermediate container e17a5a699f0c
 ---> adea87282549
Successfully built adea87282549
Successfully tagged ubuntu-18.04:latest
```
Here it is `adea87282549`. Copy this is it will be used to start the container. After this point, any time you want to run this demo all you will have to do is run the following command:

    docker run -d -p 8080:80 <IMAGE_ID>

or in this case:

    docker run -d -p 8080:80 adea87282549

To ensure that the container is running:

    docker container ls

and you should see something like:

```
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS           PORTS                  NAMES
a641cc3a84e9        adea87282549        "/bin/sh -c '/usr/sb…"   13 hours ago        Up 13 hours         0.0.0.0:8080->80/tcp   elastic_vaughan
```

Now you can navigate to http://localhost:8080 and find the demo UI.
