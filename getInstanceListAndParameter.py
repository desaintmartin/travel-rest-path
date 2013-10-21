# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os

from hateoasbrowser import SlaposHateoasBrowser

def getParameters():
  parser = argparse.ArgumentParser(
    description='Get Instance list with their request parameters')
  parser.add_argument('--cert', dest='certificate', required=True)
  parser.add_argument('--key', dest='key', required=True)
  parser.add_argument('--host', dest='host', default=None)
  config = parser.parse_args()
  return config.host, config.certificate, config.key

def getInstanceList(browser):
  """
  Return the list of all instances of all hosting subscription:
  {
    'hosting1': {
      'instance1': {
        'info1': 'value1',
        'info2': 'value2',
       },
       'instance2': { ... },
    },
    'hosting2': { ... },
  }
  """
  # Go to hosting subscription list
  browser.goToRootObject()
  browser.goToObject('http://slapos.org/reg/me')
  browser.goToObject('http://slapos.org/reg/hosting_subscription')
  
  # Get all hosting subscriptions
  for item in browser.getCurrentLinks()['item']:
    # XXX hardcoded
    if item['href'] not in [
        'https://resilientmaster:10007/hosting_subscription_module/20131011-91069/HostingSubscription_getHateoas',
        #'https://resilientmaster:10007/hosting_subscription_module/20131011-AA8D5/HostingSubscription_getHateoas',
        ]:
      continue
    
    # XXX: implement this in browser itself, don't use private method
    browser._fetchObject(item['href'], item['type'])['_links']
    hosting_subscription_title = browser.getCurrentObject()['title']
    # Get all instances of current hosting subscription
    browser.goToObject('http://slapos.org/reg/instance')
    instance_uri_list = browser.getCurrentLinks()['item']
    instance_dict = {}
    hosting_subscription_dict = {}
    for instance_uri in instance_uri_list:
      browser._fetchObject(instance_uri['href'], instance_uri['type'])
      current_instance_informations = browser.getCurrentObject()
      instance_title = current_instance_informations.pop('title')
      instance_dict[instance_title] = current_instance_informations
    hosting_subscription_dict[hosting_subscription_title] = instance_dict

  return hosting_subscription_dict

def getPersonName(browser):
  """
  Return the current person name
  """
  browser.goToRootObject()
  return browser.goToObject('http://slapos.org/reg/me')['title']

def save_informations(person_name, hosting_subscription_dict):
  """
  Write all informations to filesystem.
  """
  person_directory_path = os.path.join(os.getcwd(), person_name)
  if not os.path.exists(person_directory_path):
    os.mkdir(person_directory_path)

  for hosting_subscription_title, instance_dict in hosting_subscription_dict.iteritems():
    hosting_subscription_directory_path = os.path.join(
        person_directory_path,
        hosting_subscription_title
    )
    if not os.path.exists(hosting_subscription_directory_path):
      os.mkdir(hosting_subscription_directory_path)

    for instance_title, instance_informations in instance_dict.iteritems():
      file_path = os.path.join(
          hosting_subscription_directory_path,
          instance_title.replace('/', '-')
      )
      open(file_path, 'w').write(
          json.dumps(instance_informations, indent=2, sort_keys=True)
      )


def run():
 logging.basicConfig()

 host, certificate, key = getParameters()
 browser = SlaposHateoasBrowser(
     root_uri=host,
     ssl_certificate=certificate,
     ssl_key=key,
     ssl_verify=False,
     log_level=logging.DEBUG
 )

 person_name = getPersonName(browser)
 hosting_subscription_dict = getInstanceList(browser)
 
 save_informations(person_name, hosting_subscription_dict)

if __name__ == "__main__":
  run()
