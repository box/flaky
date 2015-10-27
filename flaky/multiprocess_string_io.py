# coding: utf-8

from __future__ import unicode_literals

import multiprocessing


class MultiprocessingStringIO(object):
    """
    Provide an interface to the multiprocessing ListProxy. The
    multiprocessing ListProxy is a global object that is instantiated before
    this class would be called, so this is an object class.
    """

    _manager = multiprocessing.Manager()
    proxy = _manager.list()  # pylint:disable=no-member

    def __init__(self):
        """
        Interface with the MP_STREAM ListProxy object
        """
        super(MultiprocessingStringIO, self).__init__()

    def getvalue(self):
        """
        Shadow the StringIO method
        """
        return ''.join(i for i in self.proxy)

    def writelines(self, content_list):
        """
        Shadow the StringIO method. Ingests a list and
        translates that to a string
        """
        # every time we see a "\n" we should make a new list item

        for item in content_list:
            self.write(item)

    def write(self, content):
        content.strip('\n')
        self.proxy.append(content)
