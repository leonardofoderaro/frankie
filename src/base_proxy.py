import re
import sys
import fire
from lxml import etree


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

def _htmlParse(html):
    parser = etree.HTMLParser(encoding='utf-8')
    tree   = etree.parse(StringIO(html), parser)
    return tree

def _fix_absolute_links(base_url, frankie_url, doc):
    doc = re.sub(base_url, '//' + frankie_url, doc)

    return doc

def _XPathRemove(doc, xpath):
    parsedDoc = _htmlParse(doc)
    element = parsedDoc.find(xpath)
    element.clear()
    doc = etree.tostring(parsedDoc, pretty_print=True, method="html")
    return doc.decode("utf-8")

def serve(config = 'frankie.json'):
    import json
    import requests
    from lxml import etree
    from flask import Flask
    from flask import request

    proxy = Flask(__name__)

    try:
        with open(config) as f:
            config_file = json.loads(f.read())
    except FileNotFoundError as e:
        print('Unable to find \'' + config + '\'.')
        print('Please specify config file using --config, or create a \'frankie.json\' file.')
        sys.exit(-1)

    @proxy.route('/', defaults={'path': ''})
    @proxy.route('/<path:path>', methods=['GET', 'POST'])
    def _handle(path):
        params = re.sub('http.?://' + request.host + '/', '', request.url)
        
        url = config_file['target_url'] + params

        if request.method == 'GET':
            doc = requests.get(url).text
        else:
            doc = requests.post(url).text

        #doc = re.sub('\n', '', doc)
  
        doc = _fix_absolute_links(config_file['target_url'], request.host + '/', doc)

        if 'patches' in config_file:
            for patch in config_file['patches']:
                if patch['type'] == 'simple':
                   doc = re.sub(patch['find'], patch['replace'], doc, re.MULTILINE)

                if patch['type'] == 'XPathRemove':
                   doc = _XPathRemove(doc, patch['xpath'])
  


        return doc

    proxy.run() 

def main():
    app = fire.Fire() 

if __name__ == "__main__":
    main()

