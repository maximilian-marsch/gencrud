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
import posixpath
from gencrud.constants import *
from gencrud.config.base import TemplateBase


class TemplateMixinComponent( TemplateBase ):
    def __init__( self, parent, component, mixin ):
        TemplateBase.__init__( self, parent )
        self.__component = component
        self.__config = mixin
        return

    def hasClass( self ):
        return self.__config.get( 'class', None ) is not None

    @property
    def cls( self ):
        return self.__config.get( 'class', None )

    @property
    def filename( self ):
        file = self.__config.get( 'filename', self.__config.get( 'file', None ) )
        file, ext = posixpath.splitext( file )
        if ext == '.py':
            return file.replace( '\\', '.' ).replace( '/', '.' )

        if ext == '.ts':
            if file.startswith( '/' ) or file.startswith( '.' ):
                return file

            return posixpath.join( '.', file )

        return '?'



class TemplateMixinPython( TemplateBase ):
    def __init__( self, parent, mixin ):
        TemplateBase.__init__( self, parent )
        self.__model    = TemplateMixinComponent( self, 'model', mixin.get( 'model',{} ) )
        self.__schema   = TemplateMixinComponent( self, 'schema', mixin.get( 'schema',{} ) )
        self.__view     = TemplateMixinComponent( self, 'view', mixin.get( 'view',{} ) )
        return

    def hasModel( self ):
        return self.__model.hasClass()

    @property
    def Model( self ):
        return self.__model

    def hasSchema( self ):
        return self.__model.hasClass()

    @property
    def Schema( self ):
        return self.__schema

    def hasView( self ):
        return self.__model.hasClass()

    @property
    def View( self ):
        return self.__view


class TemplateMixinAngular( TemplateBase ):
    def __init__( self, parent, mixin ):
        TemplateBase.__init__( self, parent )
        self.__table_component  = TemplateMixinComponent( self, 'table.component', mixin.get( 'table.component',{} ) )
        self.__screen_component = TemplateMixinComponent( self, 'screen.component',mixin.get( 'screen.component',{ } ) )
        self.__delete_dialog    = TemplateMixinComponent( self, 'delete.dialog',mixin.get( 'delete.dialog',{ } ) )
        self.__component_dialog = TemplateMixinComponent( self, 'component.dialog:',mixin.get( 'component.dialog',{ } ) )
        self.__datasource       = TemplateMixinComponent( self, 'datasource',mixin.get( 'datasource',{ } ) )
        self.__service          = TemplateMixinComponent( self, 'service',mixin.get( 'service',{ } ) )
        self.__model            = TemplateMixinComponent( self, 'model',mixin.get( 'model',{ } ) )
        return

    def hasTableComponent( self ):
        return self.__table_component.hasClass()

    @property
    def TableComponent( self ):
        return self.__table_component

    def hasScreenComponent( self ):
        return self.__screen_component.hasClass()

    @property
    def ScreenComponent( self ):
        return self.__screen_component

    def hasDeleteDialog( self ):
        return self.__delete_dialog.hasClass()

    @property
    def DeleteDialog( self ):
        return self.__delete_dialog

    def hasComponentDialog( self ):
        return self.__component_dialog.hasClass()

    @property
    def ComponentDialog( self ):
        return self.__component_dialog

    def hasDataSource( self ):
        return self.__datasource.hasClass()

    @property
    def DataSource( self ):
        return self.__datasource

    def hasService( self ):
        return self.__service.hasClass()

    @property
    def Service( self ):
        return self.__service

    def hasModel( self ):
        return self.__model.hasClass()

    @property
    def Model( self ):
        return self.__model


class TemplateMixin( TemplateBase ):
    def __init__( self, parent, **mixin ):
        TemplateBase.__init__( self, parent )
        self.__python   = TemplateMixinPython( self, mixin.get( 'python', {} ) )
        self.__angular  = TemplateMixinAngular( self, mixin.get( 'angular', {} ) )
        return

    @property
    def Python( self ):
        return self.__python

    @property
    def P( self ):
        return self.__python

    @property
    def Angular( self ):
        return self.__angular

    @property
    def A( self ):
        return self.__angular
