# -*- coding: utf-8 -*-

import argparse
import httplib2
import json
import os
import pprint

DEFAULT_URL = "https://rest.slapos.org/"
ROOT_CONTENT_TYPE = "application/vnd.slapos.org.hal+json; class=slapos.org.master"
LINK_NAME = '_links'
CLASS_NAME = '_class'
PERSON_CLASS = 'slapos.org.person'
PERSON_ID = 'title'
PATH_TO_HOSTING_SUBSCRIPTION_LIST = ['http://slapos.org/reg/me',
                                     'http://slapos.org/reg/hosting_subscription',
                                     'item',
                                     'http://slapos.org/reg/instance']

PATH_TO_HOSTING_SUBSCRIPTION = 'item'
PATH_TO_INSTANCE_LIST = ['http://slapos.org/reg/instance']

# XXX Should be split into a generic class to seek throught rest API
# XXX and a function specific for the work

class InsideRESTSlapOS():

  def __init__(self):
    self.getParameters()
    self.setPathConfig()
    self.setConnection()
    self.pp = pprint.PrettyPrinter(indent=2)

  def setPathConfig(self):
    self.path_to_instance_list = PATH_TO_HOSTING_SUBSCRIPTION_LIST
    self.path_to_instance_list = PATH_TO_INSTANCE_LIST
    self.info = {}

  def getParameters(self):
    parser = argparse.ArgumentParser(
      description='Get Instance list with their request parameters')
    parser.add_argument('--cert', dest='certificate')
    parser.add_argument('--key', dest='key')
    parser.add_argument('--host', dest='host',
                        default=DEFAULT_URL)
    self.config = parser.parse_args()

  def setConnection(self):
    self.h = httplib2.Http(disable_ssl_certificate_validation=True)
    self.h.add_certificate(key=self.config.key,
                      cert=self.config.certificate, domain="")


  def getJSONFromUrl(self, url, content_type):
    headers = {'Accept': content_type}
    self.setConnection()
    response, content = self.h.request(url, headers=headers)
    if response.status != 200:
      print "%s %s %s" % (url, response.status, response.reason)
      return {}
    return json.loads(content)

  def travelPath(self, path, connection_dict, save_info=None):
    url = connection_dict['href']
    content_type = connection_dict['type']
    current_json = self.getJSONFromUrl(url, content_type)
    if save_info:
      if current_json[CLASS_NAME] == save_info['class']:
        self.info[save_info['class']] = current_json
    if not path:
      return current_json
    next_element = path.pop()
    next_element_value = current_json[LINK_NAME][next_element]
    if type(next_element_value) == type(list()):
      result = []
      for item in next_element_value:
        result.append(self.travelPath(list(path), item, save_info))
      return result
    else:
      return self.travelPath(path, next_element_value, save_info)

  def getInstanceList(self):
    path = PATH_TO_HOSTING_SUBSCRIPTION_LIST
    path.reverse()
    connection_dict = {'type': ROOT_CONTENT_TYPE,
                       'href': self.config.host}
    return self.travelPath(path, connection_dict, {'class': PERSON_CLASS})


  def run(self):
    instance_list = self.getInstanceList()
    directory_path = os.path.join(os.getcwd(),
                                  self.info[PERSON_CLASS][PERSON_ID].replace(' ', '_'))
    if not os.path.exists(directory_path):
      os.mkdir(directory_path)
    for instance in instance_list:
      data = self.travelPath([], instance[LINK_NAME]['item'][0])
      file_path = os.path.join(directory_path, data['title'])
      open(file_path, 'w').write(json.dumps(data, indent=2, sort_keys=True))
      self.pp.pprint(self.travelPath([], instance[LINK_NAME]['item'][0]))

if __name__ == "__main__":
  InsideRESTSlapOS().run()
