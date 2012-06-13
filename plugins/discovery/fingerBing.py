'''
fingerBing.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException, w3afMustStopOnUrlError
from core.controllers.w3afException import w3afRunOnce

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.data.searchEngines.bing import bing as bing
import core.data.parsers.dpCache as dpCache


class fingerBing(baseDiscoveryPlugin):
    '''
    Search Bing to get a list of users for a domain.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        # Internal variables
        self._run = True
        self._accounts = []
        # User configured 
        self._resultLimit = 300

    def discover(self, fuzzableRequest):
        '''
        @parameter fuzzableRequest: A fuzzableRequest instance that contains 
        (among other things) the URL to test.
        '''
        result = []
        # This will remove the plugin from the discovery plugins to be run.
        if not self._run:
            raise w3afRunOnce()

        # This plugin will only run one time. 
        self._run = False
        bingSE = bing(self._uri_opener)
        self._domain = fuzzableRequest.getURL().getDomain()
        self._domain_root = fuzzableRequest.getURL().getRootDomain()

        results = bingSE.getNResults('@'+self._domain_root, self._resultLimit)

        for result in results:
            self._run_async(meth=self._findAccounts, args=(result,))
        
        self._join()
        self.printUniq(kb.kb.getData('fingerBing', 'mails'), None)
        
        return result

    def _findAccounts(self, page):
        '''
        Finds mails in bing result.

        @return: A list of valid accounts
        '''
        try:
            url = page.URL
            om.out.debug('Searching for mails in: %s' % url)
            
            grep = True if self._domain == url.getDomain() else False
            response = self._uri_opener.GET(page.URL, cache=True,
                                           grep=grep)
        except KeyboardInterrupt, e:
            raise e
        except w3afMustStopOnUrlError:
            # Just ignore it
            pass
        except w3afException, w3:
            msg = 'xUrllib exception raised while fetching page in fingerBing,'
            msg += ' error description: ' + str(w3)
            om.out.debug(msg)
        else:
            
            # I have the response object!
            try:
                document_parser = dpCache.dpc.getDocumentParserFor(response)
            except w3afException:
                # Failed to find a suitable parser for the document
                pass
            else:
                # Search for email addresses
                for mail in document_parser.getEmails(self._domain_root):
                    if mail not in self._accounts:
                        self._accounts.append( mail )

                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setURL(page.URL)
                        i.setName(mail)
                        msg = 'The mail account: "'+ mail + '" was found in: "' + page.URL + '"'
                        i.setDesc( msg )
                        i['mail'] = mail
                        i['user'] = mail.split('@')[0]
                        i['url_list'] = [page.URL, ]
                        kb.kb.append( 'mails', 'mails', i )
                        kb.kb.append( 'fingerBing', 'mails', i )

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Fetch the first "resultLimit" results from the Bing search'
        o1 = option('resultLimit', self._resultLimit, d1, 'integer')
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of getOptions().

        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        self._resultLimit = optionsMap['resultLimit'].getValue()

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds mail addresses in Bing search engine.

        One configurable parameter exist:
            - resultLimit

        This plugin searches Bing for : "@domain.com", requests all search results and 
        parses them in order to find new mail addresses.
        '''
