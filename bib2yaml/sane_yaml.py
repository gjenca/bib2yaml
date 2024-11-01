import yaml
import functools
import yadata.record

def construct_yaml_str(self, node):
    return self.construct_scalar(node)

# Override the default string handling function
# to always return unicode objects
yaml.Loader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)
yaml.SafeLoader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)

def unicode_representer(dumper, uni):
    node = yaml.ScalarNode(tag='tag:yaml.org,2002:str', value=uni)
    return node

# This is necessary to dump ASCII string normally
yaml.add_representer(str, unicode_representer)

def load_all(f,**kwargs):
    for d in yaml.load_all(f,Loader=yaml.Loader,**kwargs):
        yield d

yaml_load=yaml.load

def dump(rec):

    d_help={}
    flow_style=None
    if issubclass(type(rec),dict):
        if issubclass(type(rec),yadata.record.Record):
                top_fields=['_key']+rec.top_fields
        else:
            top_fields=['_key']
        for fieldname in top_fields:
            if fieldname in rec:
                d_help[fieldname]=rec[fieldname]
        for fieldname in rec:
            if fieldname not in d_help:
                d_help[fieldname]=rec[fieldname]
        for fieldname in d_help:
            if issubclass(type(rec),yadata.record.Record) and \
                fieldname in type(rec)._inverse:
                    continue
            if type(d_help[fieldname]) is list:
                has_list=True
                break
        else:
            has_list=False
        rec_help=(type(rec))(d_help)
        if has_list:
            flow_style=None
        else:
            flow_style=False
    else:
        rec_help=rec
    return yaml.dump(rec_help,allow_unicode=True,default_flow_style=flow_style,sort_keys=False)

load=yaml.safe_load

