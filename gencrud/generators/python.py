#
#   Python backend and Angular frontend code generation by gencrud
#   Copyright (C) 2018-2019 Marc Bertens-Nguyen m.bertens@pe2mbs.nl
#
#   This library is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Library General Public License GPL-2.0-only
#   as published by the Free Software Foundation; either version 2 of the
#   License, or (at your option) any later version.
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
import logging
import shutil
from mako.template import Template

import gencrud.util.utils
import gencrud.util.exceptions
from gencrud.util.positon import PositionInterface

logger = logging.getLogger()

MENU_CHILDEREN_LABEL    = 'childeren'
MENU_DISPLAY_NAME       = 'displayName'
MENU_ICON_NAME          = 'iconName'
MENU_INDEX              = 'index'
MENU_ROUTE              = 'route'
LABEL_LIST_MODULES      = 'listModules = ['
LABEL_MENU_ITEMS        = 'menuItems = ['
LABEL_END_LIST          = ']'


def makePythonModules( root_path, *args ):
    def write__init__py():
        with open( os.path.join( root_path, '__init__.py' ), 'w+' ) as stream:
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


def updatePythonProject( config, app_module ):
    logger.debug( config.python.sourceFolder )

    lines = []
    filename = os.path.join( config.python.sourceFolder, config.application, 'main.py' )
    if os.path.isfile( filename ):
        lines = open( filename, 'r' ).readlines()
        gencrud.util.utils.backupFile( filename )

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
        line = 'import {0}.{1}   # import maintained by generator.py'.format( config.application,
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
                                                    '' if len( modules )-1 == idx else ',' ) )

    sectionLines.append( LABEL_END_LIST + '\n' )
    gencrud.util.utils.replaceInList( lines, rangePos, sectionLines )

    sectionLines = gencrud.util.utils.searchSection( lines,
                                                     rangePos,
                                                     LABEL_MENU_ITEMS,
                                                     LABEL_END_LIST )
    pos = sectionLines[ 0 ].find( '[' )
    sectionLines[ 0 ] = sectionLines[ 0 ][ pos: ]
    try:
        menuItems = json.loads( ''.join( sectionLines ) )

    except:
        for line_no, line in enumerate( sectionLines ):
            print( '{:04} : {}'.format( line_no, line.replace( '\n', '' ).replace( '\r', '' ) ) )

        raise

    def processNewMenuStructure( menu_items, menu ):
        """This is needed for reverse calling

        :param menu_items:
        :param menu:
        :return:
        """
        foundMenu = False
        for menuItem in menu_items:
            if menuItem[ MENU_DISPLAY_NAME ] == menu.displayName:
                foundMenu = True
                if menu.menu is not None:
                    # sub menu
                    if MENU_CHILDEREN_LABEL not in menuItem:
                        menuItem[ MENU_CHILDEREN_LABEL ] = []

                    processNewMenuStructure( menuItem[ MENU_CHILDEREN_LABEL ], menu.menu )
                else:
                    menuItem[ MENU_DISPLAY_NAME ]   = menu.displayName
                    menuItem[ MENU_ICON_NAME ]      = menu.iconName
                    menuItem[ MENU_INDEX ]          = menu.index
                    if menu.route is not None:
                        menuItem[ MENU_ROUTE ]          = menu.route

                    elif menu.menu is not None:
                        if MENU_CHILDEREN_LABEL not in menuItem:
                            menuItem[ MENU_CHILDEREN_LABEL ] = []

                        processNewMenuStructure( menuItem[ MENU_CHILDEREN_LABEL ], menu.menu )

        if not foundMenu:
            menuItem = {   MENU_DISPLAY_NAME:   menu.displayName,
                           MENU_ICON_NAME:      menu.iconName,
                           MENU_INDEX:          menu.index }
            if menu.route is not None:
                menuItem[ MENU_ROUTE ] = menu.route

            elif menu.menu is not None:
                menuItem[ MENU_CHILDEREN_LABEL ] = []
                processNewMenuStructure( menuItem[ MENU_CHILDEREN_LABEL ],menu.menu )

            menu_items.insert( menu.index if menu.index >= 0 else ( len( menu_items ) + menu.index + 1 ),
                               menuItem )

        return

    for cfg in config:
        if cfg.menu is None:
            continue

        processNewMenuStructure( menuItems, cfg.menu )

    for idx, menuItem in enumerate( menuItems ):
        menuItem[ MENU_INDEX ] = idx
        if MENU_CHILDEREN_LABEL in menuItem:
            # Re-number the submenu
            for idx, subMenuItem in enumerate( menuItem[ MENU_CHILDEREN_LABEL ] ):
                subMenuItem[ MENU_INDEX ] = idx

    menuItemsBlock = ( "menuItems = " + json.dumps( menuItems, indent = 4 )).split( '\n' )
    gencrud.util.utils.replaceInList( lines, rangePos, menuItemsBlock )

    open( filename, 'w' ).writelines( lines )
    return


def generatePython( templates, config ):
    modules = []
    for cfg in config:
        backupDone = False
        modulePath = os.path.join( config.python.sourceFolder,
                                   config.application,
                                   cfg.name )
        for templ in templates:
            logger.info( 'template    : {0}'.format( templ ) )
            logger.info( 'application : {0}'.format( config.application ) )
            logger.info( 'name        : {0}'.format( cfg.name ) )
            logger.info( 'class       : {0}'.format( cfg.cls ) )
            logger.info( 'table       : {0}'.format( cfg.table.tableName ) )
            for col in cfg.table.columns:
                logger.info( '- {0:<20}  {1}'.format( col.name, col.sqlAlchemyDef() ) )

            for imp in cfg.table.tsInports:
                logger.info( '  {0}  {1}'.format( imp.module, imp.name ) )

            for imp in cfg.table.pyInports:
                logger.info( '  {0}  {1}'.format( imp.module, imp.name ) )

            logger.info( 'primary key : {0}'.format( cfg.table.primaryKey ) )
            logger.info( 'uri         : {0}'.format( cfg.uri ) )

            if not os.path.isdir( config.python.sourceFolder ):
                os.makedirs( config.python.sourceFolder )

            if os.path.isdir( modulePath ) and not gencrud.util.utils.overWriteFiles:
                raise gencrud.util.exceptions.ModuleExistsAlready( cfg, modulePath )

            makePythonModules( config.python.sourceFolder, config.application, cfg.name )

            with open( os.path.join( modulePath,
                                     gencrud.util.utils.sourceName( templ ) ),
                       gencrud.util.utils.C_FILEMODE_WRITE ) as stream:
                # stream.write( Template( filename = os.path.abspath( templ ) ).render( obj = cfg ) )
                for line in Template( filename = os.path.abspath( templ ) ).render( obj = cfg ).split( '\n' ):
                    stream.write( line )
                    if sys.platform.startswith( 'linux' ):
                        stream.write( '\n' )


            # Open the __init__.py
            filename = os.path.join( modulePath, '__init__.py' )
            moduleName, _ = os.path.splitext( gencrud.util.utils.sourceName( templ ) )
            importStr = 'from {0}.{1}.{2} import *'.format( config.application,
                                                            cfg.name,
                                                            moduleName )
            lines = []
            try:
                lines = open( filename, gencrud.util.utils.C_FILEMODE_READ ).readlines()

            except:
                logger.error( 'Error reading the file {0}'.format( filename ), file = sys.stdout )

            logger.info( lines )
            gencrud.util.utils.insertLinesUnique( lines,
                                                  PositionInterface( end = len( lines ) ),
                                                  importStr )
            if not backupDone:
                gencrud.util.utils.backupFile( filename )
                modules.append( ( config.application, cfg.name ) )
                backupDone = True

            open( filename, gencrud.util.utils.C_FILEMODE_WRITE ).writelines( lines )

        # entryPointsFile = os.path.join( modulePath, 'entry_points.py' )
        # if len( cfg.actions.getCustomButtons() ) > 0 and not os.path.isfile( entryPointsFile ):
        #     # use the template from 'common-py'
        #     templateFolder  = os.path.abspath( os.path.join( os.path.dirname( __file__ ), '..', 'common-py' ) )
        #     templateFile    = os.path.join( templateFolder, 'entry-points.py.templ' )
        #
        #     with open( entryPointsFile, gencrud.util.utils.C_FILEMODE_WRITE ) as stream:
        #         for line in Template( filename = templateFile ).render( obj = cfg ).split( '\n' ):
        #             stream.write( line + '\n' )

    updatePythonProject( config, '' )
    return
