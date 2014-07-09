import os
import tarfile
from subprocess import check_output
from swift import gettext_ as _
from swift.common.utils import whataremyips
from swift.common.swob import Request, HTTPServerError, HeaderKeyDict
from swift.proxy.controllers import obj
from swift.common.utils import get_logger, generate_trans_id, storage_directory, hash_path
from swift.common.wsgi import WSGIContext
from swift.common.ring import Ring
class SwiftLxcManage(object):
    def __init__(self, app, conf):
        self.app = app
        swift_dir = conf.get('swift_dir', '/etc/swift')
        self.account_ring_path = os.path.join(swift_dir, 'account.ring.gz')
        self.container_ring_path = os.path.join(swift_dir, 'container.ring.gz')
        self.object_ring_path = os.path.join(swift_dir, 'object.ring.gz')
        self.logger = get_logger(conf, log_route='lxc-swift')
        self.root = conf.get("devices", "/srv/node")
        self.lxc_root = "/var/lib/lxc"

    def start_container(self, cont):
        cmd = "sudo lxc-start -n %s -d" % (cont)
        cmd = check_output(cmd, shell=True)

    def check_cont_status(self, cont):
        cmd = "sudo lxc-info -n %s -s" % (cont)
        cmd = check_output(cmd, shell=True)
        cmd = cmd.split(":")
        state = cmd[1].lstrip()
        if state != "RUNNING":
            self.start_container(cont)

    def check_container(self, path, cont):
        #Get rid of .tar ext
        cont_name = os.path.splitext(cont)
        #/var/lib/lxc/$cont
        lxc_cont_path = "%s/%s" % (self.lxc_root, cont_name[0])
        #/srv/node/diskN/objects/.....
        swift_cont_path = "%s/%s" % (path, cont_name[0])
        if os.path.islink(lxc_cont_path):
            self.check_cont_status(cont_name[0])
        else:
            # Full path to actual tarball in swift
            for file_ in os.listdir(path):
                if file_.endswith(".data"):
                    c_data_path = "%s/%s" % (path, file_ )
                    cmd = "sudo tar -xvf %s -C %s" % (c_data_path, path)
                    cmd = check_output(cmd, shell=True)
                    #cont_data = tarfile.open(c_data_path)
                    #cont_data.extractall()
            os.symlink(swift_cont_path, lxc_cont_path)
            self.check_cont_status(cont_name[0])


    def __call__(self, env, start_response):
        req = Request(env)
        lxc_host = env.get("HTTP_X_OBJECT_META_LXC_HOST")
        addresses = whataremyips()
        if lxc_host in addresses:
            #path_hash = hash_path(account, container, obj)
            ring = Ring(self.object_ring_path)
            raw_path = env.get("RAW_PATH_INFO").split("/")
            path_hash = hash_path(raw_path[3],raw_path[4],raw_path[5])
            f_location = storage_directory("objects", raw_path[2], path_hash)
            path = "%s/%s/%s" % (self.root, raw_path[1], f_location)
            #Check if container exists and is running
            self.check_container(path, raw_path[5])

        return self.app(env, start_response)

def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def swift_lxc_manager_filter(app):
        return SwiftLxcManage(app,conf)
    return swift_lxc_manager_filter
