# -*- coding: utf-8 -*-
import random
import mimetypes
import string


def encode_parameters(parameters):
    boundary = ''.join (random.choice (string.letters) for ii in range (30 + 1))

    def get_content_type(filename):
        return mimetypes.guess_type (filename)[0] or 'application/octet-stream'

    def encode_field(field_name):
        return ('--' + boundary,
                'Content-Disposition: form-data; name="%s"' % field_name,
                '', str (parameters [field_name]))

    def encode_file(field_name):
        f = parameters [field_name]
        filename = f.name
        result = ('--' + boundary,
                'Content-Disposition: form-data; name="%s"; filename="%s"' % (field_name, filename),
                'Content-Type: %s' % get_content_type(filename),
                '', f.read() )
        f.close()

        return result

    lines = []
    for parametr_name in parameters:
        if isinstance(parameters[parametr_name], file):
            lines.extend(encode_file(parametr_name))
        else:
            lines.extend(encode_field(parametr_name))

    lines.extend(('--%s--' % boundary, ''))

    body = '\r\n'.join(lines)

    headers = {'content-type': 'multipart/form-data; boundary=' + boundary,
               'content-length': str(len(body))}

    return body, headers
