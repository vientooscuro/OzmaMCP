from typing import Optional, Any


def generate_update_data(schema, table_name, obj_id, entity):
    return generate_data(operation_type="update", schema=schema, table_name=table_name, obj_id=obj_id, entity=entity)


def generate_insert_data(schema, table_name, entity):
    return generate_data(operation_type="insert", schema=schema, table_name=table_name, entity=entity)


def generate_delete_data(schema, table_name, obj_id):
    return generate_data(operation_type="delete", schema=schema, table_name=table_name, entity=None, obj_id=obj_id)


def generate_data(operation_type, schema, table_name, entity, obj_id=None):
    data = {
        "type": operation_type,
        "entity": {
            "schema": schema,
            "name": table_name
        }
    }
    if entity is not None:
        data["entries"] = entity

    if obj_id is not None:
        data["id"] = obj_id

    return data


def get_result_and_rows_from_data(data):
    if "result" not in data:
        print("wtf is going on")
        return None, None

    result = data["result"]

    if "rows" not in result:
        print("wtf is going on")
        return None, None
    rows = result["rows"]

    return result, rows


async def post_operations(api, operations) -> Optional[Any]:
    params = {
        "operations": operations
    }
    return await api.insert(params)


async def delete(api, schema, table_name, ids):
    if len(ids) == 0:
        return None
    operations = []
    for obj_id in ids:
        operations.append(generate_delete_data(schema, table_name, obj_id))
    return await post_operations(api, operations)


async def update_params(api, schema, table_name, ids, params):
    if len(ids) == 0:
        return None
    operations = []
    for obj_id in ids:
        operations.append(generate_update_data(schema, table_name, obj_id, params))
    return await post_operations(api, operations)
