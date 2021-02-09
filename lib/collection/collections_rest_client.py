from membase.api.rest_client import RestConnection

import logger
import threading


class CollectionsRest(object):
    def __init__(self, node):
        self.node = node
        self.log = logger.Logger.get_logger()
        self.rest = RestConnection(self.node)

    def create_collection(self, bucket="default", scope="scope0", collection="mycollection0", params=None):
        return self.rest.create_collection(bucket, scope, collection, params)

    def create_scope(self, bucket="default", scope="scope0", params=None):
        return self.rest.create_scope(bucket, scope, params)

    def delete_collection(self, bucket="default", scope='_default', collection='_default'):
        return self.rest.delete_collection(bucket, scope, collection)

    def delete_scope(self, bucket="default", scope='_default'):
        return self.rest.delete_scope(bucket, scope)

    # Create collection in scope
    # scope: scope name
    # collection: collection name
    # bucket: bucket name
    # params: collection parameters (eg: expiry)
    def create_scope_collection(self, bucket, scope, collection, params=None):
        if self.create_scope(bucket, scope):
            if self.create_collection(bucket, scope, collection, params):
                return True
        return False

    # Create n scopes and collections
    # scope_num: Number of scopes
    # collection_num: Number of collections per scope
    # scope_prefix: Scope name, will be appended with "_count"
    # collection_prefix: Collection name, will be appended with "_count"
    # bucket: bucket name
    # params: collection parameters (eg: expiry)
    def create_scope_collection_count(self, scope_num, collection_num,
                                      scope_prefix="scope", collection_prefix="collection",
                                      bucket="default", params=None):
        try:
            for s in range(1, scope_num + 1):
                scope = scope_prefix + '_' + str(s)
                self.create_scope(bucket, scope)
                for c in range(1, collection_num + 1):
                    self.create_collection(bucket, scope, collection_prefix + '_' + str(c), params)
        except Exception as e:
            self.log.error(str(e))
            return False
        return True

    def delete_scope_collection(self, bucket, scope, collection):
        if self.rest.delete_collection(bucket, scope, collection):
            if self.delete_scope(bucket, scope):
                return True
        return False

    class CollectionFactory(threading.Thread):
        def __init__(self, bucket, scope, collections, rest):
            threading.Thread.__init__(self)
            self.bucket_name = bucket
            self.scope_name = scope
            self.collections = collections
            self.rest_handle = rest

        def run(self):
            self.rest_handle.create_collection(self.bucket_name, self.scope_name, self.collections)

    # Multithreaded for bulk creation
    def async_create_scope_collection(self, scope_num, collection_num, bucket="default"):
        tasks = []
        collections = []
        for c in range(1, collection_num + 1):
            collections.append("collection_" + str(c))
        for s in range(1, scope_num + 1):
            scope = "scope_" + str(s)
            self.create_scope(bucket, scope)
            task = self.CollectionFactory(bucket, scope, collections, self.rest)
            task.start()
            tasks.append(task)

        for task in tasks:
            task.join()

    def get_bucket_scopes(self, bucket):
        return self.rest.get_bucket_scopes(bucket)

    def get_bucket_collections(self, bucket):
        return self.rest.get_bucket_collections(bucket)

    def get_scope_collections(self, bucket, scope):
        return self.rest.get_scope_collections(bucket, scope)

    def create_buckets_scopes_collections(self, num_buckets, num_scopes,
                                          num_collections, bucket_size,
                                          bucket_prefix="test_bucket",
                                          scope_prefix="test_scope",
                                          collection_prefix="test_collection"):
        for bucket_id in range(1, num_buckets + 1):
            bucket_name = f"{bucket_prefix}_{bucket_id}"
            self.rest.create_bucket(bucket_name, ramQuotaMB=bucket_size)
            self.create_scope_collection_count(num_scopes, num_collections,
                                               scope_prefix, collection_prefix,
                                               bucket_name)
