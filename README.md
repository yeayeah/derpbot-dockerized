Acquire rootfs using

	$ wget http://pkg.comploti.st/rootfs-docker-stage1-latest_x86_64.tar.xz -O rootfs.tar.xz

Build image using

	$ docker-compose build . -t sabotage-python [--no-cache]

Launch

	$ docker-compose up [-d]


### swarm

	$ docker service create --name registry --publish "5000:5000" registry:2
	$ docker-compose build . -t sabotage-python [--no-cache]
	$ docker tag sabotage-python:latest localhost:5000/sabotage-python
	$ docker push localhost:5000/sabotage-python
	$ docker stack deploy --compose-file=docker-compose.yaml derpbot
	$ docker service scale derpbot_derpbot=2

#### docker-compose excerpt

	version: "3"
	serices:
	  derpbot:
	    image: localhost:5000/sabotage-python
	
	volumes:
	  derpbot-plugins:
	    driver: nfs
	    driver_opts:
	      path: nfs_server:/home/derpbot/plugins
	  derpbot-data:
	    driver: nfs
	    driver_opts:
	      path: nfs_server:/home/derpbot/data
