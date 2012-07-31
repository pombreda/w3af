'''
test_html_file.py

Copyright 2012 Andres Riancho

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

import os
import re

import core.data.kb.vuln as vuln

from core.data.parsers.urlParser import url_object
from ..helper import PluginTest, PluginConfig


class TestHTMLOutput(PluginTest):
    
    xss_url = 'http://moth/w3af/audit/xss/'
    OUTPUT_FILE = 'output-unittest.html'
    
    _run_configs = {
        'cfg': {
            'target': xss_url,
            'plugins': {
                'audit': (
                    PluginConfig(
                         'xss',
                         ('checkStored', True, PluginConfig.BOOL),
                         ('numberOfChecks', 3, PluginConfig.INT)),
                    ),
                'discovery': (
                    PluginConfig(
                        'web_spider',
                        ('onlyForward', True, PluginConfig.BOOL)),
                ),
                'output': (
                    PluginConfig(
                        'html_file',
                        ('fileName', OUTPUT_FILE, PluginConfig.STR)),
                )         
            },
        }
    }
    
    def test_found_xss(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        
        xss_vulns = self.kb.getData('xss', 'xss')
        file_vulns = self._from_html_get_vulns()
        
        self.assertGreaterEqual(len(xss_vulns), 3)
        
        self.assertEquals(
            set(sorted([v.getURL() for v in xss_vulns])),
            set(sorted([v.getURL() for v in file_vulns]))
        )
        
    def _from_html_get_vulns(self):
        vuln_url_re = re.compile('<b>URL:</b> (.*?)<br />')
        vulns = []
        
        for line in file(self.OUTPUT_FILE):
            
            mo = vuln_url_re.search( line )
            if mo:
                url = url_object( mo.group(1) )
                v = vuln.vuln()
                v.setURL( url )
                vulns.append(v)
                
        return vulns
        
    def tearDown(self):
        super(TestHTMLOutput, self).tearDown()
        try:
            os.remove(self.OUTPUT_FILE)
        except:
            pass
