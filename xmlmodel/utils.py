import re


def convert_dom(dom):
    """
    strip all namespaces from tags.
    Replace None with '' in text.
    """
    root = dom.getroot()
    for e in root.iter():
        e.tag = re.sub('{.*}', '', e.tag)
        if e.tag is None:
            e.tag = ''
