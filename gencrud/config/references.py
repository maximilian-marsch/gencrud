from gencrud.constants import *
from gencrud.config.angularmod import TemplateAngularModule


class TemplateReferences( object ):
    def __init__( self, **cfg ):
        self.__config = cfg
        tmp             = self.__config[ C_APP_MODULE ] if C_APP_MODULE in self.__config else { }
        self.__main     = TemplateAngularModule( 'app.module.ts',
                                             'AppModule',
                                             **tmp )
        tmp             = self.__config[ C_APP_ROUTING ] if C_APP_ROUTING in self.__config else { }
        self.__rout     = TemplateAngularModule( 'app.routing.module.ts',
                                                'AppRoutingModule',
                                                **tmp )
        return

    @property
    def app_module( self ) -> TemplateAngularModule:
        return self.__main

    @property
    def app_routing( self ) -> TemplateAngularModule:
        return self.__rout
