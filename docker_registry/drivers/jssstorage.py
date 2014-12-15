
import docker_registry.core.boto as  coreboto
from docker_registry.core import compat
from docker_registry.core import driver
from docker_registry.core import exceptions
from docker_registry.core import lru
import StringIO
import tempfile
import os
import urllib
import logging

from jss.connection import JssClient

logger = logging.getLogger(__name__)
json = compat.json

class Storage(driver.Base):

    def __init__(self, path=None, config=None):
        self._access_key = config.jss_accesskey
        self._secret_key = config.jss_secretkey
        self._bucket = config.jss_bucket
        self._domain = config.jss_domain
        logger.info("==========================>access_key:%s" % config.jss_accesskey)
        logger.info("==========================>jss_secretkey:%s" % config.jss_secretkey)
        logger.info("==========================>jss_bucket:%s" % config.jss_bucket)
        logger.info("==========================>jss_domain:%s" % config.jss_domain)
        
        self._jss = JssClient(self._access_key, self._secret_key, self._domain, None)
        
    def _init_path(self, path=None):
        if path:
            return path.replace("/", ".")
        return path

    def content_redirect_url(self, path):
        logger.info("content_redirect_url path:%s" % path)
        path1 = self._init_path(path)
        object_instance = self._jss.bucket(self._bucket).object(path1)
        
        return object_instance.generate_url("GET")
#    
#    def get_json(self, path):
#        logger.info("get_json path:%s" % path)
#        try:
#            result = json.loads(self.get_unicode(path))
#            logger.info("get_json result:%s" % result)
#            return result
#        except Exception as e:
#            logger.error("get_json error:%s" % e)
#            return []
#        
    @lru.get
    def get_content(self, path):
        logger.info("get_content path:%s" % path)
        path1 = self._init_path(path)
        output = StringIO.StringIO()
        try:
            object_instance = self._jss.bucket(self._bucket).object(path1)
            res = object_instance.download_flow()
            logger.info("get_content res:%s" % res)
            while True:
                data = res.read(1024)
                if len(data) != 0:
                    output.write(data)
                else:
                    break
                    
            return output.getvalue()
        except Exception as e:
            logger.error("get_content error:%s" % e)
            raise exceptions.FileNotFoundError("File not found %s" % path)
        finally:
            output.close()

    def stream_read(self, path, bytes_range=None):
        logger.info("stream_read path:%s" % path)
        path1 = self._init_path(path)
        
        try:
            object_instance = self._jss.bucket(self._bucket).object(path1)
            res = object_instance.download_flow()
            while True:
                data = res.read(1024)
                if len(data) != 0:
                    yield data
                else:
                    break
        except Exception as e:
            logger.error("stream_read error:%s" % e)
            raise exceptions.FileNotFoundError("File not found %s" % path)
        
    @lru.set
    def put_content(self, path, content):
        logger.info("put_content path:%s" % path)
        logger.info("-------------------------------------->%s" % content)
        path1 = self._init_path(path)
        try:
            object_instance = self._jss.bucket(self._bucket).object(path1)
            object_instance.upload_flow(headers=None, data=content)
        except Exception as e:
            logger.error("put_content error:%s" % e)
            raise e
        return path


#    def stream_write(self, path, fp):
#        logger.info("stream_write path:%s" % path)
#        path1 = self._init_path(path)
#        part_size = 5 * 1024 * 1024
#        if self.buffer_size < part_size:
#            part_size = self.buffer_size
#        try:
#             object_instance = self._jss.bucket(self._bucket).object(path1)
#             object_instance.multi_upload_fp(None, fp, part_size)
#        except Exception as e :
#            logger.error("stream_write error:%s" % e)
#            raise e

    def list_directory(self, path=None):
        logger.info("list_directory path:%s" % path)
        path1 = self._init_path(path)
        
        try:
            response = self._jss.bucket(self._bucket).get_all_keys(headers=None, prefix=path1)
            logger.info("list_directory response:%s" % response)
            files = response["Contents"] 
            
            logger.info("list_directory files:%s" % files)
            logger.info("list_directory len(files):%s" % len(files))
            
            if len(files) == 0 :
                raise Exception('empty')
            
            for file in files:
                logger.info("list_directory key:%s" % file["Key"])
                yield file["Key"].replace(".", "/")
        except Exception as e:
            logger.error("list_directory error:%s" % e)
            raise exceptions.FileNotFoundError("File not found %s" % path)
        
    def stream_write(self, path, fp):
        logger.info("stream_write path:%s" % path)
        path1 = self._init_path(path)
        part_size = 5 * 1024 * 1024
        if self.buffer_size < part_size:
            part_size = self.buffer_size
        
        try:
            tmp_file = tempfile.mktemp(suffix=path1, prefix='docker_registry_image', dir="/tmp")
            with open(tmp_file, 'w') as f:
                while True:
                    buf = fp.read(part_size)
                    if not buf: break
                    f.write(buf)
                
            with open(tmp_file, 'r') as fp:
                object_instance = self._jss.bucket(self._bucket).object(path1)
                object_instance.multi_upload_fp(None, fp, part_size)
                
        except Exception as e :
             logger.error("stream_write error:%s" % e)
             raise e
        finally:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
        

    @lru.remove
    def remove(self, path):
        logger.info("remove path:%s" % path)
        path1 = self._init_path(path)

        try:
           self._jss.bucket(self._bucket).delete_key(path1)
        except Exception as e:
            logger.error("remove error:%s" % e)
            raise e
        
    def get_size(self, path):
        logger.info("get_size path:%s" % path)
        try:
            path1 = self._init_path(path)
            keyInfo = self._jss.bucket(self._bucket).get_key(path1)
            
            return keyInfo.content_length
        except Exception as e:
            logger.error("get_size error:%s" % e)
            raise exceptions.FileNotFoundError("File not found %s" % path)
        
    def exists(self, path):
        logger.info("exists path:%s" % path)
        path1 = self._init_path(path)
        
        try:
            res = self._jss.bucket(self._bucket).get_key(path1)
            if res is None :
                return False
            return True
        except Exception as e:
            
            return False
