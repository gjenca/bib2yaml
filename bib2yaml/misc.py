# -*- coding: utf-8 -*-

import unicodedata

def strip_accents(s):

    return unicodedata.normalize('NFKD',s).encode("ascii","ignore").decode("ascii")
