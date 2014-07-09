swift-lxc
=========

Swift middleware to deploy lxc containers

THIS IS A TRIPPLE DELUXE WIP.

GOAL
=========

The goal of this is to allow users to upload already created lxc conatiners as tarballs and have swift start them on the object servers. The aim is to upload a container and specify the X-Object-Meta-lxc-deploy
header. The swift_lxc_proxy middleware will look for this header and then look up the first host that the tarball will land on and set the IP of that host in object metadata via X_OBJECT_META_LXC_HOST.
The swift_lxc_manage middleware will check for the lxc-deploy metadata and if found it will look to see if it is the host that should start the container. It will extract the tarball in place on the object server
and create a symlink to /var/lib/lxc/$container. At this point it will start the container.

To upload a container and have it start on an object server run:

    swift upload lxc base.tar --header "X-Object-Meta-lxc-deploy:true"

To get this to work you need to add swift-lxc to your proxy-server.conf on your swift proxies.

    [pipeline:main]
    pipeline = catch_errors proxy-logging healthcheck cache ratelimit authtoken keystoneauth proxy-logging staticweb swift-lxc proxy-server

Add swift_lxc_manage to your object-server.conf on your object servers:

    [pipeline:main]
    pipeline = healthcheck recon swift-lxc-manage object-server

The longterm goal is to get the middleware to detect if the container host has gone down is not reachable and start the container on a replica node.

This is a WIP, and is not high quality at this point.
