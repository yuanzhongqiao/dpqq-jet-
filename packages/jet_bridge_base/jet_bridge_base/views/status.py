from jet_bridge_base.db import connections
from jet_bridge_base.permissions import AdministratorPermissions
from jet_bridge_base.responses.json import JSONResponse
from jet_bridge_base.utils.classes import issubclass_safe
from jet_bridge_base.utils.graphql import ModelFiltersType, ModelFiltersFieldType, ModelFiltersRelationshipType, \
    ModelLookupsType, ModelLookupsFieldType, ModelLookupsRelationshipType
from jet_bridge_base.views.base.api import BaseAPIView
from sqlalchemy import inspect


class StatusView(BaseAPIView):
    permission_classes = (AdministratorPermissions,)

    def map_connection_graphql_schema(self, schema):
        if not schema:
            return {'status': 'no_schema'}

        instance = schema.get('instance')

        if instance:
            types_count = len(instance._type_map.values())
            filters_count = 0
            filters_fields_count = 0
            filters_relationships_count = 0
            lookups_count = 0
            lookups_fields_count = 0
            lookups_relationships_count = 0
            get_schema_time = schema.get('get_schema_time')

            for item in instance._type_map.values():
                if not hasattr(item, 'graphene_type'):
                    continue

                if issubclass_safe(item.graphene_type, ModelFiltersType):
                    filters_count += 1
                elif issubclass_safe(item.graphene_type, ModelFiltersFieldType):
                    filters_fields_count += 1
                elif issubclass_safe(item.graphene_type, ModelFiltersRelationshipType):
                    filters_relationships_count += 1
                elif issubclass_safe(item.graphene_type, ModelLookupsType):
                    lookups_count += 1
                elif issubclass_safe(item.graphene_type, ModelLookupsFieldType):
                    lookups_fields_count += 1
                elif issubclass_safe(item.graphene_type, ModelLookupsRelationshipType):
                    lookups_relationships_count += 1

            return {
                'status': 'ok',
                'types': types_count,
                'filters': filters_count,
                'filters_fields': filters_fields_count,
                'filters_relationships': filters_relationships_count,
                'lookups': lookups_count,
                'lookups_fields': lookups_fields_count,
                'lookups_relationships': lookups_relationships_count,
                'get_schema_time': get_schema_time
            }
        else:
            return {'status': 'pending'}

    def map_connection(self, connection):
        cache = connection['cache']
        MappedBase = connection['MappedBase']
        column_count = 0
        relationships_count = 0

        for Model in MappedBase.classes:
            mapper = inspect(Model)
            column_count += len(mapper.columns)
            relationships_count += len(mapper.relationships)

        graphql_schema = self.map_connection_graphql_schema(cache.get('graphql_schema'))
        graphql_schema_draft = self.map_connection_graphql_schema(cache.get('graphql_schema_draft'))

        return {
            'name': connection['name'],
            'project': connection.get('project'),
            'token': connection.get('token'),
            'tables': len(MappedBase.classes),
            'columns': column_count,
            'relationships': relationships_count,
            'graphql_schema': graphql_schema,
            'graphql_schema_draft': graphql_schema_draft,
            'connect_time': connection.get('connect_time'),
            'reflect_time': connection.get('reflect_time')
        }

    def get(self, request, *args, **kwargs):
        return JSONResponse({
            'total_connections': len(connections.keys()),
            'connections': map(lambda x: self.map_connection(x), connections.values())
        })