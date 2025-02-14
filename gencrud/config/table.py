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
#
import logging
from gencrud.config.base import TemplateBase
from gencrud.config._inports import SourceImport
from gencrud.config.column import TemplateColumn
from gencrud.config.tab import TemplateTabs
from gencrud.config.sort import SortInfo
from gencrud.config.mixin import TemplateMixin
import gencrud.util.utils as root
from gencrud.util.exceptions import *
from gencrud.constants import *
from gencrud.util.exceptions import InvalidViewSize

logger = logging.getLogger()


class RelationShip( TemplateBase ):
    def __init__( self, parent, relation ):
        TemplateBase.__init__( self, parent )
        self.__relation = relation
        return

    @property
    def cls( self ):
        return self.__relation.get( C_CLASS )

    @property
    def table( self ):
        return self.__relation.get( C_TABLE )

    @property
    def cascade( self ):
        return self.__relation.get( C_CASCADE )


class TemplateTable( TemplateBase ):
    def __init__( self, parent, **table ):
        TemplateBase.__init__( self, parent )
        self.__table            = table
        self.__columns          = []
        self.__primaryKey       = ''
        self.__viewSort         = None
        self.__viewSize         = None
        self.__defaultViewSize  = 10
        self.__inports          = SourceImport()
        if C_NAME not in self.__table:
            raise MissingAttribute( C_TABLE, C_NAME )

        if C_COLUMNS not in self.__table:
            raise MissingAttribute( C_TABLE, C_COLUMNS )

        for col in self.__table[ C_COLUMNS ]:
            column = TemplateColumn( self, self.name, **col )
            self.__columns.append( column )
            if column.isPrimaryKey():
                self.__primaryKey = column.name

        if C_VIEW_SORT in table:
            self.__viewSort = SortInfo( table[ C_VIEW_SORT ] )

        if C_VIEW_SIZE in table:
            if type( table[ C_VIEW_SIZE ] ) in ( int, str ):
                self.__viewSize = table[ C_VIEW_SIZE ]

            else:
                raise InvalidViewSize()

        return

    @property
    def object( self ):
        return self.parent

    def __iter__(self):
        return iter( self.__columns )

    @property
    def config( self ):
        return self.object.config

    def hasTabs( self, tp = C_DIALOG ) -> bool:
        if C_TABS in self.__table:
            return len( self.__table.get( C_TABS,[ ] ) ) > 0

        return len( self.__table.get( tp + C_TABS, [] ) ) > 0

    def tabs( self, tp = C_DIALOG ) -> TemplateTabs:
        if C_TABS in self.__table:
            return TemplateTabs( self,**self.__table.get( C_TABS,{ } ) )

        return TemplateTabs( self, **self.__table.get( tp + C_TABS, {} ) )

    def sortedInfo( self ) -> str:
        if self.__viewSort is not None:
            return self.__viewSort.htmlMaterialSorting()

        return ''

    @property
    def leadIn( self ) -> str:
        result = []
        for column in self.__columns:
            for leadin in column.leadIn:
                if leadin not in result:
                    result.append( leadin )

        logger.info( "LeadIn = {}".format( result ) )
        return '\n'.join( result )

    @property
    def tableName( self ) -> str:
        if root.config.options.ignoreCaseDbIds:
            return self.__table.get( C_NAME, '' ).lower()

        return self.__table.get( C_NAME, '' )

    @property
    def name( self ) -> str:
        if root.config.options.ignoreCaseDbIds:
            return self.__table.get( C_NAME, '' ).lower()

        return self.__table.get( C_NAME, '' )

    @property
    def sortField( self ) -> str:
        if C_VIEW_SORT in self.__table:
            return self.__viewSort.field
        return self.__primaryKey

    @property
    def sortDirection( self ) -> str:
        if C_VIEW_SORT in self.__table:
            return self.__viewSort.direction
        return C_DESENDING

    @property
    def uniqueKey( self ) -> dict:
        values  = {}
        for key, value in self.__table.get( C_UNIQUE_KEY, {} ).items():
            if isinstance( value, str ):
                values[ key ] = ', '.join( [ "'{0}'".format( item.strip() ) for item in value.split( ',' ) ] )

            elif isinstance( value, ( list, tuple ) ):
                values[ key ] = ', '.join( [ "'{0}'".format( item.strip() ) for item in value ] )

        return values

    def hasUniqueKey( self ) -> bool:
        if C_UNIQUE_KEY in self.__table:
            if type( self.__table.get( C_UNIQUE_KEY, None ) ) in ( dict, tuple, list ):
                return True

        return False

    @property
    def hasAutoUpdate( self ) -> bool:
        for field in self.__columns:
            if field.hasAutoUpdate:
                return True

        return False

    @property
    def relationShips( self ):
        return [ RelationShip( self, rs ) for rs in self.__table.get( C_RELATION_SHIP, [] ) ]

    @property
    def relationShipList( self ):
        return self.__table.get( C_RELATION_SHIP, [] )

    @property
    def columns( self ):
        return self.__columns

    @property
    def primaryKey( self ) -> str:
        return self.__primaryKey

    @property
    def firstTextField( self ):
        for col in self.__columns:
            if col.isString():
                return col.name

        return self.__columns[ 1 ].name

    @property
    def listViewColumns( self ) -> list:
        return sorted( [ col for col in self.__columns if col.listview.index is not None ],
                       key = lambda col: col.listview.index )

    def buildFilter( self ) -> str:
        result = [ ]
        for item in self.listViewColumns:
            if item.ui.isUiType(C_CHOICE, C_CHOICE_AUTO) or item.ui.isUiType(C_COMBOBOX, C_COMBO):
                result.append( "( this.{0}_Label( record.{0} ) )".format( item.name ) )

            elif item.ui.isCheckbox() or item.ui.isSliderToggle():
                result.append( "( this.{0}_Label( record.{0} ) )".format( item.name ) )

            elif item.tsType == 'string':
                result.append( "( record.{0} || '' )".format( item.name ) )

        if len( result ) == 0:
            return "''"

        return ' + \r\n                   '.join( result )

    @property
    def viewSort( self ) -> SortInfo:
        return self.__viewSort

    @property
    def hasViewSizeService( self ) -> bool:
        if self.__viewSize is not None:
            return type( self.__viewSize ) is str

        return False

    @property
    def hasViewSizeValue( self ) -> bool:
        if self.__viewSize is not None:
            return type( self.__viewSize ) is int

        return False

    @property
    def viewSize( self ):
        return self.__viewSize

    def __repr__(self):
        return "<TemplateTable name={}, table={}>".format( self.name, self.tableName )
