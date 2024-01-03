from email.header import decode_header, make_header
from urllib.parse import unquote
from re import match as regex
from base64 import b64decode
import sys
import os

# Add the Splunk internal library
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from splunklib.searchcommands import dispatch, StreamingCommand, Configuration, Option, validators

# List of possible returned errors.
ERR_COMMAND_USAGE = 10
ERR_UNKNOWN_EXCEPTION = 11

# Decode the input.
def decode(string, type = None):
    decoded = str(string).strip().strip("'")

    # Passing the string through the email cleaner only if
    # it seems to be an email subject.
    email_matches = regex("(=\?[^ \r\n]+\?)", decoded)
    if type == 'email' or (type is None and email_matches):
        decoded = str(make_header(decode_header(decoded)))

        if type == 'email':
            return decoded
    
    # If the input is an URL.
    if type == 'url' or type is None:
        decoded = str(unquote(decoded))

        # Sometimes, the result of unquote is still encoded.
        # So, we do another unquote action.
        if "%" in decoded:
            decoded = unquote(decoded)

        if type == 'url':
            return decoded

    # If the input is a base64-encoded text.
    if type == 'base64' or type is None:
        try:
            decoded = b64decode(decoded).decode('utf-8')
        except: pass

        if type == 'base64':
            return decoded
        
    # If this is an hexadecimal value, such as
    # the Linux PROCTITLE logs.
    if type == 'hex' or type is None:
        try:
            decoded = bytearray.fromhex(decoded).decode()
        except: pass

        if type == 'hex':
            return decoded
        
    return decoded

@Configuration()
class DecodeCommand(StreamingCommand):

    type = Option(
        doc='''
            **Syntax:** **type=***<"email"|"url"|"base64">*
            **Description:** Encoding algorithm''',
        require=False, validate=validators.Set("email", "url", "base64"))
        
    # This is the method treating all the events.
    def stream(self, events):
        for event in events:
            for key in self.fieldnames:
                value = event[key] if key in event else None

                if value is None:
                    continue

                if isinstance(value, list):
                    decoded = []

                    for data in value:
                        decoded.append(decode(data, self.type))

                    event[key + "_decoded"] = decoded
                else:
                    event[key + "_decoded"] = decode(value, self.type)

            yield event

# Finally, say to Splunk that this command exists.
dispatch(DecodeCommand, sys.argv, sys.stdin, sys.stdout, __name__)