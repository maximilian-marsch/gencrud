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
import os
from gencrud.util.exceptions import (MissingTemplate,
                                     MissingSourceFolder,
                                     KeyNotFoundException,
                                     MissingTemplateFolder,
                                     PathNotFoundException)
from gencrud.util.utils import get_platform
from gencrud.constants import *
from gencrud.config.base import TemplateBase


class TemplateSource( TemplateBase ):
    def __init__( self, tp, **cfg ):
        TemplateBase.__init__( self, None )
        platf = get_platform()
        if platf not in C_PLATFORMS:
            raise Exception( "Unsupported platform: {}".format( platf ) )

        self.__config = cfg
        self.__key = tp
        self.__source = self.__config.get( platf, self.__config ).get( C_SOURCE, {} )
        # if there is no templates directory specified, the gencrud default templates will be used
        self.__template = self.__config.get( platf, self.__config ).get( C_TEMPLATE,
                        os.path.abspath( os.path.join( os.path.dirname( __file__ ), '..', C_TEMPLATES_DIR ) ) )
        return

    @property
    def baseFolder( self ) -> str:
        folder = self.__source.get( C_BASE, os.getcwd() )
        print(os.getcwd())
        print("-----")
        print(folder)
        if not os.path.isdir( folder ):
            raise PathNotFoundException( folder )

        return folder

    @property
    def sourceFolder( self ) -> str:
        folder = self.__source.get( self.__key, None )
        if folder is None:
            raise KeyNotFoundException( "{}.{}".format( C_SOURCE, self.__key ) )

        if not folder.startswith( os.path.pathsep ):
            # not absolute path
            # first test with baseFolder
            if os.path.isdir( os.path.join( self.baseFolder, folder ) ):
                folder = os.path.join( self.baseFolder, folder )

            folder = os.path.abspath( folder )

        if not os.path.isdir( folder ):
            raise MissingSourceFolder( folder )

        return folder

    @property
    def templateFolder( self ) -> str:
        folder = os.path.join( self.__template, self.__key )
        if not os.path.isdir( folder ):
            raise MissingTemplateFolder( folder )

        # Now check if the templates exists
        cnt = 0
        for templ_file in os.listdir( folder ):
            if os.path.splitext( templ_file )[ 1 ] == '.templ':
                cnt += 1

        if cnt == 0:
            raise MissingTemplate( self.__template )

        return folder

    def __repr__( self ):
        return """<TemplateSource {key}
        base = {base} 
        source = {src}
        template = {templ}>""".format( key      = self.__key,
                                       src      = self.sourceFolder,
                                       templ    = self.templateFolder,
                                       base     = self.baseFolder )


class TemplateSourcePython( TemplateSource ):
    def __init__( self, **cfg ):
        TemplateSource.__init__( self, C_PYTHON, **cfg )
        return


class TemplateSourceAngular( TemplateSource ):
    def __init__( self, **cfg ):
        TemplateSource.__init__( self, C_ANGULAR, **cfg )
        return
