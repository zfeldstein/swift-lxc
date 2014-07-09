import os
from swift import gettext_ as _
from swift.common.swob import Request, HTTPServerError, HeaderKeyDict
from swift.proxy.controllers import obj
from swift.common.utils import get_logger, generate_trans_id
from swift.common.wsgi import WSGIContext
from swift.common.ring import Ring
class SwiftLxc(object):
    def __init__(self, app, conf):
        self.app = app
        swift_dir = conf.get('swift_dir', '/etc/swift')
        self.account_ring_path = os.path.join(swift_dir, 'account.ring.gz')
        self.container_ring_path = os.path.join(swift_dir, 'container.ring.gz')
        self.object_ring_path = os.path.join(swift_dir, 'object.ring.gz')
        self.logger = get_logger(conf, log_route='lxc-swift')
    def __call__(self, env, start_response):
        req = Request(env)
        if env.get('REQUEST_METHOD') == "PUT" and env.get("HTTP_X_OBJECT_META_LXC_DEPLOY"):
            ring = Ring(self.object_ring_path)
            raw_path = env.get("RAW_PATH_INFO").split("/")
            node_data = ring.get_nodes(raw_path[2],raw_path[3],raw_path[4])
            deploy_host = node_data[1][0]["ip"]
            req.headers["X-Object-Meta-LXC-HOST"] = deploy_host
            req.headers["REMOTE_USER"] = raw_path[2]
        return self.app(env, start_response)

def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def swiftlxc_filter(app):
        return SwiftLxc(app,conf)
    return swiftlxc_filter