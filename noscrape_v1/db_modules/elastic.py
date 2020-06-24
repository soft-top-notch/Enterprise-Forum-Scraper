
from datetime import datetime
from elasticsearch import Elasticsearch

from base_logger import BaseLogger
from elasticsearch.exceptions import RequestError
from urllib3.exceptions import ConnectTimeoutError
import socket
import subprocess as sp

class Elastic:
	def __init__(self, ip=None, port=None, limit=None, exclude_indexes=[]):
		# self.scrape_type = scrape_type
		self.limit = limit or 10000
		# self.keywords = keywords
		self.exclude_indexes = exclude_indexes
		self.logger = BaseLogger(__name__, None)
		self.ip = ip
		self.port = int(port)
		self.db_type = 'es'
		self.timeout = 5

	def connect(self):
		try:
			return Elasticsearch(hosts=[{"host": self.ip, "port": self.port}])
		except Exception as e:
			return False

	def test_connection(self):
		''' Simply tries to connect out to the port on TCP '''
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(self.timeout)
			s.connect((self.ip, self.port))
			s.close()
			return True
		except Exception as e:
			self.logger.error("Error connecting to " + str(self.ip) + ":" + str(self.port) + " - " + str(e))
			return False

	def get_index_count(self, indexes):
		indexes_count = {}
		for index in indexes:
			index_name = index['index']
			index_record_count = index['docs.count']
			indexes_count[index_name] = index_record_count
		return indexes_count

	# get index names
	def get_index_names(self, indexes):
		return [index["index"] for index in indexes]

	def valid_index(self, index):
		for keyword in self.exclude_indexes:
			if keyword.lower() in index.lower():
				self.logger.info("Ignore index %s because contain keyword %s in exclude file." % (index, keyword))
				return False
		return True

	def dump(self):
		dumped = []

		max_elasticdump_limit = 10000
		if self.limit > max_elasticdump_limit:
			self.limit = max_elasticdump_limit

		elastic_db = self.get_db()
		if elastic_db:
			indexes = elastic_db.indices.get("*")
			for index in indexes:
				if self.valid_index(index):
					print("Dumping to file for ip {}:{} and the index {}".format(self.ip, self.port, index))
					records = elastic_db.search(index=index)
					records = records["hits"]["hits"]
					for hit in records:
						dumped.append(hit)


					# elastic_dump_command = "sudo elasticdump --input=http://{}:{}/{} --output={}/{}.txt –ignore-errors --limit={}". \
					# 	format(self.target, self.port, index, self.target, index, self.limit)
					# try:
					# 	sp.check_output(elastic_dump_command, shell=True)
					# except Exception as e:
					# 	print(e)

			return "dump"

	def get_db(self):
		connection_verified = self.test_connection()
		if connection_verified:
			return self.connect()
		return False

	# once known as index headers, get the nodeattrs
	def get_nodeattrs(self, elastic_db):
		try:
			return elastic_db.cat.nodeattrs(format='json')
		except RequestError as re:
			self.logger.error("Request Error fetching nodeattrs {}:{}".format(self.ip, self.port))
			return []

	def fetch_metadata(self):
		try:
			# self.logger.info("----Requesting for cross-section of each index for {}:{}".format(self.ip, self.port))
			elastic_db = self.get_db()
			if elastic_db:
				indexes = elastic_db.cat.indices(v=True, format='json')
				index_names = self.get_index_names(indexes)
				indexes_count = self.get_index_count(indexes)
				nodeattrs = self.get_nodeattrs(elastic_db)
				json_to_store = {
					"index_names": index_names,
					"index_headers": nodeattrs,
					"indexes_count": indexes_count,
					"ip": self.ip,
					"port": self.port,
					"database_type": self.db_type,
					"date": str(datetime.now())
				}
				# self.logger.info("----Results: {}:{}".format(self.ip, self.port))
				elastic_db.close()
				return json_to_store

			return False

		except Exception as e:
			self.logger.error("Unknown Exception: {}".format(str(e)))
			return False