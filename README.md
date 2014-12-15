
Docker registry jss storage(HTTP://JAE.JD.COM) driver
This is a docker-registry backend driver for JSS Cloud Storage.

Usage (recommendation)

docker-registry 安装

1:基础环境准备
 1.1 安装基础
    sudo apt-get install build-essential python-dev libevent-dev python-pip libssl-dev
    sudo pip install liblzma-dev
    sudo pip install libevent1-dev

 1.2 创建目录
    mkdir -p /export/service
    mkdir -p /export/home/jae
    mkdir -p /tmp
 1.3 mount 磁盘到 /tmp 用于存储临时文件

2:源代码下载 并且安装
  2.1 源代码下载
        cd /export/service/ && git clone https://github.com/docker/docker-registry.git
  2.2 安装docker-registry
      cd /export/service/docker-registry/  && sudo python setup.pu install
  2.3 安装jss python sdk
     sudo pip install jss_python
  2.4 安装 docker-registry-driver-jss 驱动
     sudo  pip install docker-registry-driver-jss 

3:修改配置
  cd /usr/local/lib/python2.7/dist-packages/docker_registry-0.9.0-py2.7.egg
  修改 config/config.yml  如果config/下无 config.yml 就cp config_sample.yml config.yml

  修改后的config.yml------->加粗字体表示启用 jssstorage 驱动
# All other flavors inherit the `common' config snippet
common: &common
    issue: '"docker-registry server"'
    # Default log level is info
    loglevel: debug
    # Enable debugging (additional informations in the output of the _ping endpoint)
    debug: true
    # By default, the registry acts standalone (eg: doesn't query the index)
    standalone: _env:STANDALONE:true
    # The default endpoint to use (if NOT standalone) is index.docker.io
    index_endpoint: _env:INDEX_ENDPOINT:https://index.docker.io
    # Storage redirect is disabled
    storage_redirect: _env:STORAGE_REDIRECT
    # Token auth is enabled (if NOT standalone)
    disable_token_auth: _env:DISABLE_TOKEN_AUTH
    # No priv key
    privileged_key: _env:PRIVILEGED_KEY
    # No search backend
    search_backend: _env:SEARCH_BACKEND
    # SQLite search backend
    sqlalchemy_index_database: _env:SQLALCHEMY_INDEX_DATABASE:sqlite:////tmp/docker-registry.db
    # Mirroring is not enabled
    mirroring:
        source: _env:MIRROR_SOURCE # https://registry-1.docker.io
        source_index: _env:MIRROR_SOURCE_INDEX # https://index.docker.io
        tags_cache_ttl: _env:MIRROR_TAGS_CACHE_TTL:172800 # seconds
    cache:
        host: _env:CACHE_REDIS_HOST
        port: _env:CACHE_REDIS_PORT
        db: _env:CACHE_REDIS_DB:0
        password: _env:CACHE_REDIS_PASSWORD
    # Enabling LRU cache for small files
    # This speeds up read/write on small files
    # when using a remote storage backend (like S3).
    cache_lru:
        host: _env:CACHE_LRU_REDIS_HOST
        port: _env:CACHE_LRU_REDIS_PORT
        db: _env:CACHE_LRU_REDIS_DB:0
        password: _env:CACHE_LRU_REDIS_PASSWORD
    # Enabling these options makes the Registry send an email on each code Exception
    email_exceptions:
        smtp_host: _env:SMTP_HOST
        smtp_port: _env:SMTP_PORT:25
        smtp_login: _env:SMTP_LOGIN
        smtp_password: _env:SMTP_PASSWORD
        smtp_secure: _env:SMTP_SECURE:false
        from_addr: _env:SMTP_FROM_ADDR:docker-registry@localdomain.local
        to_addr: _env:SMTP_TO_ADDR:noise+dockerregistry@localdomain.local
    # Enable bugsnag (set the API key)
    bugsnag: _env:BUGSNAG
    # CORS support is not enabled by default
    cors:
        origins: _env:CORS_ORIGINS
        methods: _env:CORS_METHODS
        headers: _env:CORS_HEADERS:[Content-Type]
        expose_headers: _env:CORS_EXPOSE_HEADERS
        supports_credentials: _env:CORS_SUPPORTS_CREDENTIALS
        max_age: _env:CORS_MAX_AGE
        send_wildcard: _env:CORS_SEND_WILDCARD
        always_send: _env:CORS_ALWAYS_SEND
        automatic_options: _env:CORS_AUTOMATIC_OPTIONS
        vary_header: _env:CORS_VARY_HEADER
        resources: _env:CORS_RESOURCES
local: &local
    <<: *common
    storage: local
    storage_path: _env:STORAGE_PATH:/tmp/registry
jssstorage: &jssstorage
    <<: *common
    storage: jssstorage
    jss_bucket: your jss bucket
    jss_accesskey: your jss_accesskey
    jss_secretkey: your jss_secretkey
    jss_domain: storage.jcloud.com
# This is the default configuration when no flavor is specified
dev: &dev
    <<: *jssstorage
    loglevel: _env:LOGLEVEL:debug
    debug: _env:DEBUG:true
    search_backend: _env:SEARCH_BACKEND:sqlalchemy
# This flavor is used by unit tests
test:
    <<: *dev
    index_endpoint: https://registry-stage.hub.docker.com
    standalone: true
    storage_path: _env:STORAGE_PATH:./tmp/test
# To specify another flavor, set the environment variable SETTINGS_FLAVOR
# $ export SETTINGS_FLAVOR=prod
prod:
    <<: *jssstorage
    storage_path: _env:STORAGE_PATH:/prod


starting command:
--daemon running
gunicorn  --access-logfile /export/home/jae/registry_access.log --error-logfile /export/home/jae/registry_error.log --daemon --debug -k gevent -b 0.0.0.0:5000 -w 8 docker_registry.wsgi:application

-- no daemon running
gunicorn --access-logfile /export/home/jae/registry_access.log --error-logfile /export/home/jae/registry_error.log --debug -k gevent -b 0.0.0.0:5000 -w 1 docker_registry.wsgi:application

Go to JSS Cloud Storage to get your access_key first.

Run docker-registry service by docker container


In order to verify what you did is ok, just run pip install tox; tox. This will run the tests provided by docker-registry-core.

For more information, plz check docker-registry-readme
