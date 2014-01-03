# -*- coding: utf-8 -*-

import logging
import requests

#browser = HateoasBrowser(root_url, root_content_type, certificate, key)
#
#browser.goToRootObject() -> sets self.class, self.links, returns everything else if any (like "news" for Instance)
#browser.getCurrentClass() -> returns the current class
#browser.getCurrentUri() -> returns the current uri (url? uri?)
#browser.getCurrentLinks() -> returns (content_type / href) key/value store
#
#browser.goToLinkedObject(thecontenttype) -> sets self.class, self.links, returns everything else if any (like "news" for Instance)
#browser.getCurrentClass() -> etc, etc.

class HateoasBrowser(object):
  """
  A small library allowing to browse a HATEOAS-based API using JSON.
  """
  DEFAULT_LINK_NAME = '_links'
  DEFAULT_CLASS_NAME = '_class'
  DEFAULT_HREF_NAME = 'href'
  DEFAULT_CONTENT_TYPE_NAME = 'type'

  def __init__(self, root_uri,  root_content_type,
               ssl_certificate=None, ssl_key=None, ssl_verify=True,
               links_name=None, class_name=None, href_name=None, content_type_name=None,
               log_level=logging.INFO):
    self.root_uri = root_uri
    self.root_content_type = root_content_type
    self.ssl_certificate = ssl_certificate
    self.ssl_key = ssl_key
    self.ssl_verify = ssl_verify

    if not links_name:
      links_name = self.DEFAULT_LINK_NAME
    self.links_name = links_name
    if not class_name:
      class_name = self.DEFAULT_CLASS_NAME
    self.class_name = class_name
    if not href_name:
      href_name = self.DEFAULT_HREF_NAME
    self.href_name = href_name
    if not content_type_name:
      content_type_name = self.DEFAULT_CONTENT_TYPE_NAME
    self.content_type_name = content_type_name

    self.me = None
    self.current_class = None
    self.current_content = {}
    self.current_links = {}
    self.current_uri = None

    self._current_content_type = None
    self._history = []

    self.logger = logging.getLogger('Browser')
    self.logger.setLevel(log_level)

    # List of classes that are a collection
    self.valid_collection_class_list = []

    # XXX: check ssl validity

  def _get(self, url, headers=None):
    """
    Low level network plumbering method.
    """
    parameter_dict = {
        'url': url,
        'verify': self.ssl_verify,
    }
    if self.ssl_certificate and self.ssl_key:
      parameter_dict['cert'] = (self.ssl_certificate, self.ssl_key)
    if headers:
      parameter_dict['headers'] = headers
    return requests.get(**parameter_dict)

  def _fetchObject(self, uri, content_type):
    """
    Fetch the object specified by its uri and content_type, and set:
     * current class
     * current available links
     * current custom informations available trought the current object
     * URI of the current object (i.e used to fetch the current object)
    """
    # XXX set self.
    self.logger.debug('Fetching %s...' % uri)
    headers = {'Accept': content_type}
    response = self._get(uri, headers=headers)
    if response.status_code != 200:
      self.logger.error('Bad response: %s %s') % (
          uri, response.status_code, response.text
      )
      return {}
    try:
      current_content = response.json()
    except ValueError:
      raise ValueError('No JSON object could be decoded from %s.\n'
           'Received data is:\n%s' % (uri, response.text))

    # This allows basic history to go to the previous object.
    self._history.append((self.current_uri, self._current_content_type))
    self._current_content_type = content_type

    # Set all informations about new (current) object
    self.current_class = current_content.pop(self.class_name)
    self.current_links = current_content.pop(self.links_name)
    self.current_content = current_content
    # XXX: Is it an URI or an URL?
    self.current_uri = uri

  def _isACollection(self):
    """
    Define if current object is a collection.
    """
    if self.getCurrentClass() in self.valid_collection_class_list:
      return True
    return False

  def goToLinkedObject(self, link_relation, index=None):
    """
    Go to the object specified by its link_relation (definition index) and
    set informations about fetched object.
    If URI is not available from the links of the current object, raise.

    Current object is either an element, or a collection of elements.
    """
    # XXX: setup discovery through definition of API -> ease navigation
    current_links = self.getCurrentLinks()
    if index:
      if not self.isACollection():
        raise AttributeError('Current links do not contain a collection.')
      target = current_links[link_relation[index]]
    else:
      target = current_links.get(link_relation, None)
      if target is None:
        raise AttributeError('Current object does not define such relation.')

    uri = target[self.href_name]
    content_type = target[self.content_type_name]
    return self._fetchObject(uri, content_type)

  def goToRootObject(self):
    """
    Go to the root object. Mandatory to initialize the browser instance.
    """
    return self._fetchObject(
        uri=self.root_uri,
        content_type=self.root_content_type,
    )

  def goToPreviousObject(self):
    """
    Go to the previous object.
    """
    # XXX: implement real history, not only one object.
    # XXX: implement cache
    if not self.history:
      raise AttributeError('No history available.')
    uri, content_type = self._history.pop()
    return self._fetchObject(uri=uri, content_type=content_type)

  def getCurrentContent(self):
    """
    Return current arbitrary informations of the current object set by goToLinkedObject().
    If no object is defined yet, raise.
    """
    if self.current_content is None:
      raise AttributeError('No object is set yet. Call goToRootObject() before.')
    return self.current_content

  def getCurrentLinks(self):
    """
    Return current links available for navigation set by goToLinkedObject(), using a
    (content_type / href) key/value data store (dict).
    If no links are defined yet, raise.
    """
    if self.current_links is None:
      raise AttributeError('No links are set yet. Call goToRootObject() before.')
    return self.current_links

  def getCurrentClass(self):
    """
    Return current class set by goToLinkedObject().
    If no class is defined yet, raise.
    """
    if self.current_class is None:
      raise AttributeError('No class is set yet. Call goToRootObject() before.')
    return self.current_class

  def getCurrentUri(self):
    """
    Return current URI set by goToLinkedObject().
    If no URI is defined yet, raise.
    """
    if self.current_uri is None:
      raise AttributeError('No URI is set yet. Call goToRootObject() before.')
    return self.current_uri


class SlaposHateoasBrowser(HateoasBrowser):
  DEFAULT_ROOT_URI = "https://rest.slapos.org/Base_getHateoasMaster"
  DEFAULT_ROOT_CONTENT_TYPE = "application/vnd.slapos.org.hal+json; class=slapos.org.master"

  def __init__(
      self,
      root_uri=None, root_content_type=None,
      ssl_certificate=None, ssl_key=None, ssl_verify=True,
      log_level=logging.INFO
  ):
    if root_uri == None:
      root_uri = self.DEFAULT_ROOT_URI
    if root_content_type == None:
      root_content_type=self.DEFAULT_ROOT_CONTENT_TYPE
    HateoasBrowser.__init__(self, root_uri, root_content_type,
                            ssl_certificate, ssl_key, ssl_verify,
                            log_level=log_level)
    self.valid_collection_class_list = ['slapos.org.collection']

  def goToLinkedObject(self, link_relation=None, index=None):
    if not link_relation:
      link_relation = 'item'
