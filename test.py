from bs4 import BeautifulSoup

raw = open('raw.txt', 'r').read()
raw = BeautifulSoup(raw, 'html.parser')
body = raw.find('sec-header')
print(body)


# <SEQUENCE>1
# <html>
# <head>
# <title>test.py</title>
# </head>
# <body>
# ...
# </body>
# </html>
