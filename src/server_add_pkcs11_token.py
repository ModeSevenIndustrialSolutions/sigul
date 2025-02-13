#!/usr/bin/env python3

# Copyright (c) 2025 Microsoft Corporation.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from server import ServerConfiguration
import server_common
import utils


def main():
    """
    Register a PKCS#11 token to use when signing PE applications.

    Adds a new private key to the Sigul database using the PKCS11 key type.
    The key added is a reference to the key that resides in the token.
    """
    cli_parser = utils.create_basic_parser(
        "Register a PKCS#11 token to use when signing PE applications.",
        "~/.sigul/server.conf",
    )
    cli_parser.add_option("-a", "--initial-key-admin", help="The key admin's username")
    cli_parser.add_option("-k", "--key-uri", help="The key's PKCS#11 URI")
    cli_parser.add_option("-n", "--key-name", help="The key name; used by the sigul client")
    cli_parser.add_option(
        "-t",
        "--token-pin-file",
        help="File containing PIN required to log into the PKCS#11 token",
    )
    cli_parser.add_option(
        "-p",
        "--passphrase-file",
        help="File containing the user passphrase to access the key",
    )

    options = utils.optparse_parse_options_only(cli_parser)
    config = ServerConfiguration(options.config_file)
    db = server_common.db_open(config)

    token_pin = open(options.token_pin_file, "rt").readline().strip()
    user_passphrase = open(options.passphrase_file, "rt").readline().strip()

    # The fingerprint is used to ensure the file is unique, but since the keys are stored in hardware, we use
    # this field to store the key URI.
    admin = (
        db.query(server_common.User).filter_by(name=options.initial_key_admin).first()
    )
    key = server_common.Key(options.key_name, "PKCS11", options.key_uri)
    db.add(key)
    access = server_common.KeyAccess(key, admin, key_admin=True)
    access.set_passphrase(
        config,
        key_passphrase=token_pin,
        user_passphrase=user_passphrase,
        bind_params=None,
    )
    db.add(access)
    db.commit()


if __name__ == "__main__":
    main()
