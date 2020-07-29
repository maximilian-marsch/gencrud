#
#   Python backend and Angular frontend code generation by gencrud
#   Copyright (C) 2018-2020 Marc Bertens-Nguyen m.bertens@pe2mbs.nl
#
#   This library is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Library General Public License GPL-2.0-only
#   as published by the Free Software Foundation.
#
#   This library is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#   Library General Public License for more details.
#
#   You should have received a copy of the GNU Library General Public
#   License GPL-2.0-only along with this library; if not, write to the
#   Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
#   Boston, MA 02110-1301 USA
#
import json
import os
import sys
import yaml
import logging
import shutil
import datetime
import hashlib
import gencrud.version
from mako.template import Template
from gencrud.configuraton import TemplateConfiguration
import gencrud.util.utils
import gencrud.util.exceptions
from gencrud.util.positon import PositionInterface
import gencrud.util.utils as API

logger = logging.getLogger()

MENU_CHILDEREN_LABEL    = 'childeren'
MENU_DISPLAY_NAME       = 'displayName'
MENU_ICON_NAME          = 'iconName'

MENU_DISPLAY_NAME_V2    = 'caption'
MENU_ICON_NAME_V2       = 'icon'

MENU_INDEX              = 'index'
MENU_ID                 = 'id'
MENU_ROUTE              = 'route'
LABEL_LIST_MODULES      = 'listModules = ['
LABEL_MENU_ITEMS        = 'menuItems = ['
LABEL_END_LIST          = ']'


def makePythonModules( root_path, *args ):
    def write__init__py():
        with open( os.path.join( root_path, '__init__.py' ), 'w+' ) as stream:
            # Write one newline to the file
            print( '', file = stream )

        return

    if len( args ) > 0:
        root_path = os.path.join( root_path, args[ 0 ] )
        if not os.path.isdir( root_path ):
            os.mkdir( root_path )

        makePythonModules( root_path, *args[ 1: ] )

    if len( args ) > 0:
        if not os.path.isfile( os.path.join( root_path, '__init__.py' ) ):
            write__init__py()

    return


def updatePythonProject( config: TemplateConfiguration, app_module ):
    del app_module  # unused
    logger.debug( config.python.sourceFolder )
    lines = []
    filename = os.path.join( config.python.sourceFolder, config.application, 'main.py' )
    if os.path.isfile( filename ):
        if config.options.backupFiles:
            gencrud.util.utils.backupFile( filename )

        lines = open( filename, 'r' ).readlines()

    if len( lines ) <= 2:
        lines = open( os.path.join( os.path.dirname( __file__ ),
                                    '..',
                                    'common-py',
                                    'main.py' ), 'r' ).readlines()

    rangePos            = gencrud.util.utils.findImportSection( lines )
    # Copy the following files from the common-py folder to the source folder of the project
    for src_filename in ( 'common.py', ):
        fns = os.path.abspath( os.path.join( os.path.dirname( __file__ ), '..', 'common-py', src_filename ) )
        fnd = os.path.abspath( os.path.join( config.python.sourceFolder, config.application, src_filename ) )
        logger.debug( "Source: {}\nTarget: {}".format( fns, fnd ) )
        shutil.copy( fns, fnd )

    # update import section
    modules = []
    for table in config:
        line = 'import {0}.{1}   # import maintained by gencrud.py'.format( config.application,
                                                                            table.name )
        gencrud.util.utils.insertLinesUnique( lines, rangePos, line )
        modules.append( '{0}.{1}'.format( config.application, table.name ) )

    sectionLines = gencrud.util.utils.searchSection( lines,
                                                     rangePos,
                                                     LABEL_LIST_MODULES,
                                                     LABEL_END_LIST )
    del sectionLines[ 0 ]
    del sectionLines[ -1 ]
    for line in sectionLines:
        line = line.strip( ' ,\n' )
        if line not in modules:
            modules.append( line )

    sectionLines = [ LABEL_LIST_MODULES + '\n' ]
    for idx, mod in enumerate( modules ):
        sectionLines.append( '    {0}{1}\n'.format( mod,
                                                    '' if len( modules ) - 1 == idx else ',' ) )

    sectionLines.append( LABEL_END_LIST + '\n' )
    gencrud.util.utils.replaceInList( lines, rangePos, sectionLines )

    def makeMenuId( menu,prefix ):
        return hashlib.md5( (prefix + menu.caption).encode('ascii') ).hexdigest().upper()

    if API.config.version == 1:
        sectionLines = gencrud.util.utils.searchSection( lines,
                                                         rangePos,
                                                         LABEL_MENU_ITEMS,
                                                         LABEL_END_LIST )
        pos = sectionLines[ 0 ].find( '[' )
        sectionLines[ 0 ] = sectionLines[ 0 ][ pos: ]
        try:
            menuItems = json.loads( ''.join( sectionLines ) )

        except Exception:
            for line_no, line in enumerate( sectionLines ):
                logger.error( '{:04} : {}'.format( line_no, line.replace( '\n', '' ).replace( '\r', '' ) ) )

            raise

        def processMenuStructure_V1( menu_items, menu, id_prefix = "" ):
            """This is needed for reverse calling

            :param menu_items:
            :param menu:
            :return:
            """
            foundMenu = False
            for newMenuItem in menu_items:
                if newMenuItem[ MENU_DISPLAY_NAME ] == menu.caption:
                    foundMenu = True
                    if menu.menu is not None:
                        # sub menu
                        if MENU_CHILDEREN_LABEL not in newMenuItem:
                            newMenuItem[ MENU_CHILDEREN_LABEL ] = []

                        processMenuStructure_V1( newMenuItem[ MENU_CHILDEREN_LABEL ],
                                                 menu.menu,
                                                 newMenuItem[ MENU_ID ] + '_' )

                    else:
                        newMenuItem[ MENU_DISPLAY_NAME ]   = menu.caption
                        newMenuItem[ MENU_ICON_NAME ]      = menu.icon
                        newMenuItem[ MENU_INDEX ]          = menu.index
                        newMenuItem[ MENU_ID ]             = makeMenuId( menu, id_prefix )
                        if menu.route is not None:
                            newMenuItem[ MENU_ROUTE ]      = menu.route

                        elif menu.menu is not None:
                            if MENU_CHILDEREN_LABEL not in newMenuItem:
                                newMenuItem[ MENU_CHILDEREN_LABEL ] = []

                            processMenuStructure_V1( newMenuItem[ MENU_CHILDEREN_LABEL ],
                                                     menu.menu,
                                                     newMenuItem[ MENU_ID ] + '_' )

            if not foundMenu:
                newMenuItem = { MENU_DISPLAY_NAME:   menu.caption,
                                MENU_ICON_NAME:      menu.icon,
                                MENU_ID:             makeMenuId( menu, id_prefix ),
                                MENU_INDEX:          menu.index }
                if menu.route is not None:
                    newMenuItem[ MENU_ROUTE ] = menu.route

                elif menu.menu is not None:
                    newMenuItem[ MENU_CHILDEREN_LABEL ] = []
                    processMenuStructure_V1( newMenuItem[ MENU_CHILDEREN_LABEL ],
                                             menu.menu,
                                             newMenuItem[ MENU_ID ] + '_' )

                menu_items.insert( menu.index if menu.index >= 0 else ( len( menu_items ) + menu.index + 1 ),
                                   newMenuItem )

            return

        for cfg in config:
            if cfg.menu is None:
                continue

            processMenuStructure_V1( menuItems, cfg.menu )

        for idx, menuItem in enumerate( menuItems ):
            menuItem[ MENU_INDEX ] = idx
            if MENU_CHILDEREN_LABEL in menuItem:
                # Re-number the submenu
                for subIdx, subMenuItem in enumerate( menuItem[ MENU_CHILDEREN_LABEL ] ):
                    subMenuItem[ MENU_INDEX ] = subIdx

        menuItemsBlock = ( "menuItems = " + json.dumps( menuItems, indent = 4 )).split( '\n' )
        gencrud.util.utils.replaceInList( lines, rangePos, menuItemsBlock )

    else:
        menuFilename = os.path.join( config.python.sourceFolder, config.application, 'menu.yaml' )
        if os.path.isfile( menuFilename ):
            with open( menuFilename, 'r' )  as stream:
                menuItems = yaml.load( stream, Loader = yaml.Loader )
                if menuItems is None:
                    menuItems = []

        else:
            menuItems = []

        def processMenuStructure_V2( items, menu, id_prefix = '' ):
            foundMenu = False
            for menuItem in items:
                if menuItem[ MENU_DISPLAY_NAME_V2 ] == menu.caption:
                    foundMenu = True
                    if menu.menu is not None:
                        # sub menu
                        if MENU_CHILDEREN_LABEL not in menuItem:
                            menuItem[ MENU_CHILDEREN_LABEL ] = [ ]

                        processMenuStructure_V2( menuItem[ MENU_CHILDEREN_LABEL ],
                                                 menu.menu,
                                                 menuItem[ MENU_ID ] + '_' )

                    else:
                        menuItem[ MENU_DISPLAY_NAME_V2 ] = menu.caption
                        menuItem[ MENU_ICON_NAME_V2 ] = menu.icon
                        menuItem[ MENU_ID ] = makeMenuId( menu, id_prefix )
                        if menu.route is not None:
                            menuItem[ MENU_ROUTE ] = menu.route

                        # elif menu.menu is not None:
                        #     if MENU_CHILDEREN_LABEL not in menuItem:
                        #         menuItem[ MENU_CHILDEREN_LABEL ] = [ ]
                        #
                        #     processMenuStructure_V2( menuItem[ MENU_CHILDEREN_LABEL ],
                        #                              menu.menu,
                        #                              menuItem[ MENU_ID ] + '_' )

            if not foundMenu:
                newMenuItem = { MENU_DISPLAY_NAME_V2: menu.caption,
                                MENU_ID: makeMenuId( menu, id_prefix ),
                                MENU_ICON_NAME_V2: menu.icon }
                if menu.route is not None:
                    newMenuItem[ MENU_ROUTE ] = menu.route

                elif menu.menu is not None:
                    newMenuItem[ MENU_CHILDEREN_LABEL ] = [ ]
                    processMenuStructure_V2( newMenuItem[ MENU_CHILDEREN_LABEL ],
                                             menu.menu,
                                             newMenuItem[ MENU_ID ] + '_' )

                if menu.hasBeforeAfter():
                    index = -1
                    if menu.after is not None:
                        for idx, menuItem in enumerate( items ):
                            if menuItem[ MENU_DISPLAY_NAME_V2 ] == menu.after:
                                index = idx + 1

                    else: # before
                        for idx, menuItem in enumerate( items ):
                            if menuItem[ MENU_DISPLAY_NAME_V2 ] == menu.before:
                                index = idx

                    items.insert( index, newMenuItem )

                else:
                    items.insert( menu.index if menu.index >= 0 else (len( items ) + menu.index + 1), newMenuItem )

            return


        for cfg in config:
            if cfg.menu is None:
                continue

            processMenuStructure_V2( menuItems, cfg.menu )

        with open( menuFilename, 'w' )  as stream:
            yaml.dump( menuItems, stream, default_style=False, default_flow_style=False )

    open( filename, 'w' ).writelines( lines )
    return


def generatePython( config: TemplateConfiguration, templates: list ):
    modules = []
    constants = []
    logger.info( 'application : {0}'.format( config.application ) )
    dt = datetime.datetime.now()
    generationDateTime = dt.strftime( "%Y-%m-%d %H:%M:%S" )
    userName = os.path.split( os.path.expanduser( "~" ) )[ 1 ]
    for cfg in config:
        modulePath = os.path.join( config.python.sourceFolder,
                                   config.application,
                                   cfg.name )
        logger.info( 'name        : {0}'.format( cfg.name ) )
        logger.info( 'class       : {0}'.format( cfg.cls ) )
        logger.info( 'table       : {0}'.format( cfg.table.tableName ) )
        logger.info( 'primary key : {0}'.format( cfg.table.primaryKey ) )
        logger.info( 'uri         : {0}'.format( cfg.uri ) )
        for col in cfg.table.columns:
            logger.info( '- {0:<20}  {1}'.format( col.name, col.sqlAlchemyDef() ) )

        for templ in templates:
            logger.info( 'template    : {0}'.format( templ ) )

            if not os.path.isdir( config.python.sourceFolder ):
                os.makedirs( config.python.sourceFolder )

            if os.path.isdir( modulePath ) and not config.options.overWriteFiles:
                raise gencrud.util.exceptions.ModuleExistsAlready( cfg, modulePath )

            outputSourceFile = os.path.join( modulePath, gencrud.util.utils.sourceName( templ ) )
            if config.options.backupFiles:
                gencrud.util.utils.backupFile( outputSourceFile )

            if os.path.isfile( outputSourceFile ):
                # remove the file first
                os.remove( outputSourceFile )

            makePythonModules( config.python.sourceFolder, config.application, cfg.name )
            with open( outputSourceFile,
                       gencrud.util.utils.C_FILEMODE_WRITE ) as stream:
                for line in Template( filename = os.path.abspath( templ ) ).render( obj = cfg,
                                                                                    root = config,
                                                                                    date = generationDateTime,
                                                                                    version = gencrud.version.__version__,
                                                                                    username = userName ).split( '\n' ):
                    stream.write( line )
                    if sys.platform.startswith( 'linux' ):
                        stream.write( '\n' )

        for column in cfg.table.columns:
            if column.ui is not None:
                if column.ui.hasResolveList():
                    constants.append( '# field {}.{} constants\n'.format( cfg.table.name, column.name ) )
                    for line in column.ui.createResolveConstants():
                        if line not in constants:
                            constants.append( line + '\n' )

                    constants.append( '\n' )

        if len( constants ) > 0:
            constants.insert( 0, '# Generated by gencrud\n' )
            filename = os.path.join( modulePath, 'constant.py' )
            if config.options.backupFiles:
                gencrud.util.utils.backupFile( filename )

            with open( filename, 'w' ) as stream:
                stream.writelines( constants )

        entryPointsFile = os.path.join( modulePath, 'entry_points.py' )
        if len( cfg.actions.getCustomButtons() ) > 0 and not os.path.isfile( entryPointsFile ):
            # use the template from 'common-py'
            templateFolder  = os.path.abspath( os.path.join( os.path.dirname( __file__ ), '..', 'common-py' ) )
            templateFile    = os.path.join( templateFolder, 'entry-points.py.templ' )

            with open( entryPointsFile, gencrud.util.utils.C_FILEMODE_WRITE ) as stream:
                for line in Template( filename = templateFile ).render( obj = cfg, root = config ).split( '\n' ):
                    stream.write( line + '\n' )

    updatePythonProject( config, '' )
    return
