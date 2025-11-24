# Copyright (C) 2008-2021 Red Hat, Inc.  All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program; if
# not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA.  Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Red Hat Author: Miloslav Trmac <mitr@redhat.com>

import logging
import sys
import traceback

import server_common
import utils


class AddAdminConfiguration(server_common.ServerBaseConfiguration):

    def _read_configuration(self, parser):
        super(AddAdminConfiguration, self)._read_configuration(parser)
        self.batch_mode = False


def main():
    parser = utils.create_basic_parser('Add an administrator to the signing '
                                       'server', '~/.sigul/server.conf')
    utils.optparse_add_batch_option(parser)
    parser.add_option('-n', '--name', metavar='USER',
                      help='Administrator user name')
    options = utils.optparse_parse_options_only(parser)

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=logging.DEBUG)  # Force DEBUG level for troubleshooting
    logging.info('🔧 [ADD_ADMIN] Starting server_add_admin')
    logging.info('🔧 [ADD_ADMIN] Batch mode: %s', options.batch)
    try:
        logging.info('🔧 [ADD_ADMIN] Loading configuration from: %s', options.config_file)
        config = AddAdminConfiguration(options.config_file)
        logging.info('✅ [ADD_ADMIN] Configuration loaded successfully')
    except utils.ConfigurationError as e:
        logging.error('🔴 [ADD_ADMIN] Configuration error: %s', e)
        traceback.print_exc()
        sys.exit(str(e))
    config.batch_mode = options.batch
    try:
        logging.info('🔧 [ADD_ADMIN] Setting user/group IDs')
        utils.set_regid(config)
        utils.set_reuid(config)
        utils.update_HOME_for_uid(config)
        logging.info('✅ [ADD_ADMIN] User/group IDs set successfully')
    except Exception as e:
        logging.error('🔴 [ADD_ADMIN] Failed to set user/group IDs: %s', e)
        traceback.print_exc()
        sys.exit(1)

    try:
        logging.info('🔧 [ADD_ADMIN] Initializing NSS')
        utils.nss_init(config)
        logging.info('✅ [ADD_ADMIN] NSS initialized successfully')
    except utils.NSSInitError as e:
        logging.error('🔴 [ADD_ADMIN] NSS initialization failed: %s', e)
        traceback.print_exc()
        sys.exit(str(e))

    if options.name is not None:
        name = options.name
        logging.info('🔧 [ADD_ADMIN] Using admin name from command line: %r', name)
    else:
        # readline import makes raw_input more usable.  Import only here to
        # avoid sending escape sequences to stdout when not interactive.
        import readline
        name = utils.input('Administrator user name: ')
        logging.info('🔧 [ADD_ADMIN] Admin name from prompt: %r', name)

    logging.info('🔧 [ADD_ADMIN] Reading password (batch_mode=%s)', config.batch_mode)
    password = utils.read_password(config, 'Administrator password: ')
    logging.info('🔧 [ADD_ADMIN] Password received, length: %d', len(password))
    logging.info('🔧 [ADD_ADMIN] Password repr: %r', password)
    logging.info('🔧 [ADD_ADMIN] Password type: %s', type(password))
    logging.info('🔧 [ADD_ADMIN] Password hex: %s', password.encode('utf-8').hex() if isinstance(password, str) else password.hex())
    
    if not config.batch_mode:
        logging.info('🔧 [ADD_ADMIN] Reading password confirmation (interactive mode)')
        p2 = utils.read_password(config, 'Administrator password (again): ')
        if password != p2:
            logging.error('🔴 [ADD_ADMIN] Passwords do not match')
            sys.exit('Passwords don\'t match.')
        logging.info('✅ [ADD_ADMIN] Password confirmation matched')

    try:
        logging.info('🔧 [ADD_ADMIN] Opening database')
        db = server_common.db_open(config)
        logging.info('✅ [ADD_ADMIN] Database opened successfully')
        
        logging.info('🔧 [ADD_ADMIN] Creating User object for: %r', name)
        user = server_common.User(name, clear_password=password, admin=True)
        logging.info('✅ [ADD_ADMIN] User object created')
        
        logging.info('🔧 [ADD_ADMIN] Adding user to database')
        db.add(user)
        logging.info('✅ [ADD_ADMIN] User added to database session')
        
        logging.info('🔧 [ADD_ADMIN] Committing database transaction')
        db.commit()
        logging.info('✅ [ADD_ADMIN] Database transaction committed successfully')
        
        logging.info('🎉 [ADD_ADMIN] Admin user "%s" created successfully', name)
    except Exception as e:
        logging.error('🔴 [ADD_ADMIN] Failed to create admin user: %s', e)
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
