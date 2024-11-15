#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml
import sys
from pybtex.database.input import bibtex
import re
import tempfile
import unicodedata
import argparse
from io import StringIO
from bib2yaml.misc import strip_accents
import logging
from bib2yaml.titlecase import titlecase

def readpubs(f,ns):

    parser = bibtex.Parser(encoding='utf-8')
    uni=f.read()
    bib_data = parser.parse_stream(StringIO(uni))
    ret=[]
    for entry in bib_data.entries.values():
        try:
            pub={}
            pub["type"]=entry.type.lower()
            if entry.persons:
                pub["authors"]=list(map(str,entry.persons['author']))
            else:
                pub["authors"]=["NOBODY, X."]
            for fname,value in entry.fields.items():
                # TODO: sanitize fname properly
                fname=fname.replace("-","_") # - is forbidden in yaml map keys
                fname=fname.lower()
                pub[fname]=value.strip('{}')
                if not ns.no_titlecase and \
                        fname in ("journal","title","series","booktitle") and \
                        pub[fname].isupper():
                    pub[fname]=titlecase(pub[fname].lower())
            if "year" not in pub:
                pub["year"]="NOYEAR"
            if "title" not in pub:
                pub["title"]="NOTITLE"
            if "pages" in pub:
                if "-" in pub["pages"] or "–" in pub["pages"]:
                    pub["startpage"],pub["endpage"]=[x for x in re.split('[-–]+',pub["pages"],maxsplit=1)]
                else:
                    pub["startpage"]=pub["pages"]
                    pub["endpage"]=pub["pages"]
                del pub["pages"]
            for fname in pub:
                try:
                    if type(pub[fname]) in (str,str):
                        pub[fname]=int(pub[fname])
                except ValueError:
                    pass
            if "abstract" in pub and not ns.keep_abstract:
                del pub["abstract"]
            if "art_number" in pub:
                pub["article_number"]=pub["art_number"]
                del pub["art_number"]
            ret.append(pub)
        except:
            print("error in",entry)
            raise
    return ret

def patch_and_convert(fin,ns):

    keys_d={}
    start_suffix=ord('a')
    if ns.scopus:
        f=tempfile.TemporaryFile(mode='r+')
        for line in fin:
            # Scopus generates invalid key for auhors
            # with multiword surnames
            # As of 2017, Scopus generates keys with accents (WRONG)
            m=re.match(r"^( *@.*{ *)([^ ,]*)(.*)$",line)
            if m:
                line="".join(line.split())
                line=strip_accents(line)
                key=m.group(2)
                keys_d[key]=keys_d.get(key,0)+1
                if keys_d[key]==1:
                    key_suffix=''
                else:
                    key_suffix=chr(start_suffix-1+keys_d[key])
                line=m.group(1)+m.group(2)+key_suffix+m.group(3)
            # For years, Scopus produces an invalid list of authors
            if re.match(r"^ *author *=.*$",line):
                key,val=line.split("=",1)
                val=re.sub(r", *(\w\w)",r" and \1",val)
                f.write("%s=%s" % (key,val))
            else:
                f.write(line)
        f.seek(0)
    elif ns.wos:
        f=tempfile.TemporaryFile(mode='r+')
        for line in fin:
            m=re.match('^ *([^=]*)=(.*)$',line)
            if m:
                key=m.group(1).rstrip().replace(' ','_')
                val=m.group(2)
                f.write("%s=%s" % (key,val))
            else:
                f.write(line)
        f.seek(0)
    else:
        f=fin
    pubs=readpubs(f,ns)
    for pub in pubs:
        print("---")
        sys.stdout.write(yaml.dump(pub,allow_unicode=True,default_flow_style=None,sort_keys=False))
    if f is not fin:
        fin.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("bibfile",nargs="*",help="BibTeX file to read; reads standard input if omitted")
    parser.add_argument("-s","--scopus",action="store_true",help="correct broken BibTeX produced by SCOPUS")
    parser.add_argument("-w","--wos",action="store_true",help="correct broken BibTeX produced by WOS")
    parser.add_argument("-a","--keep-abstract",action="store_true",help="keep abstract")
    parser.add_argument("-n","--no-titlecase",action="store_true",help="do not titlecase ALL CAPS strings")
    ns=parser.parse_args()

    if not ns.bibfile:
        patch_and_convert(sys.stdin,ns)
    else:
        for fnm in ns.bibfile:
            with open(fnm) as fin:
                patch_and_convert(fin,ns)

