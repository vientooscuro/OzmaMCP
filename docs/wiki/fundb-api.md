# FunDB API

Source: https://wiki.ozma.io/en/docs/fundb-api
Exported at (UTC): 2026-03-04 15:18:29

¶ FunDB API

The database has a REST API to perform arbitrary operations. All basic actions with the database are performed through this interface, including operations that are performed from the web interface.

Requests are made to the URL corresponding to your instance address, following the pattern: https://YOUR_INSTANCE_NAME.api.ozma.org.

If applicable, the request body must be in JSON format. You need to add the Content-type: application/json header in this case.

Data is returned in JSON format, including errors. For error results, the returned object always contains fields:

- "type": error type (currently only "generic");

- "message": error message.

¶ Authorization

The authorization mechanism and bot accounts will be redesigned in the future.

Authorization in the system is performed according to the OIDC standard. To get your client id and secret, write an email to [email protected].

After receiving the client id and client secret, you can request an authorization token using the username and password of the desired user (grant_type=password). For example, for Python there is a suitable library requests-authlib.

- OIDC automatic configuration URL: https://account.ozma.io/auth/realms/default/.well-known/openid-configuration

- URL to get the token: https://account.ozma.io/auth/realms/default/protocol/openid-connect/token

The token (access token in OIDC) should be sent in HTTP request headers to the API using Authorization: Bearer YOUR_TOKEN.

Example request via curl:

curl \
  -d "client_id=client" \
  -d "client_secret=secret" \
  -d "grant_type=password" \
  -d "username=user" \
  -d "password=password" \
  "https://account.ozma.io/auth/realms/default/protocol/openid-connect/token"

Same request with Python:

import requests

url = "https://account.ozma.io/auth/realms/default/protocol/openid-connect/token"
payload = {
    "client_id": "client",
    "client_secret": "secret",
    "grant_type": "password",
    "username": "user",
    "password": "password"
}

# Make the POST request
response = requests.post(url, data=payload)
response.raise_for_status()
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

To check access rights to the database by token, you can use the GET /check_access request. If the token is valid and it allows access to this database, a 200 OK response will be returned.

The token must be refreshed regularly according to the OAuth standard using refresh_token. It is better to entrust work with a token to a ready-made library for your programming language. An example of an update request via curl:

curl \
  -d "client_id=client" \
  -d "client_secret=secret" \
  -d "grant_type=refresh_token" \
  -d "refresh_token=REFRESH_TOKEN" \
  "https://account.ozma.io/auth/realms/default/protocol/openid-connect/token"

The response comes with a new access_token, and with a new refresh_token.

¶ Receiving data

It is possible to both make queries on existing (named) mappings, and make arbitrary (anonimous) queries. For all user view types, several calls are provided to retrieve data and metadata.

¶ Named user view

Path to user view: /views/by_name/USER_VIEW_SCHEMA/USER_VIEW_NAME.

¶ Anonimous user view

Path to user view: /views/anonymous.

Among the GET parameters, there must be a __query parameter containing the query string.

If you plan to use the query frequently, you will achieve better performance by creating a named query. It is also recommended to use arguments in the query instead of pasting the values directly into the query body. This way the request will be cached and you can avoid code injection attacks.

¶ Receiving data from the database

Query: PATH_TO_THE_USER_VIEW/entries.

Returns: IViewExprResult (see further)

You can pass display arguments to GET request parameters, for example ?id=42. Arguments are encoded as JSON, for example, a string parameter is passed like this: foo="value".

¶ Receiving metadata

Query: PATH_TO_THE_USER_VIEW/info.

Returns: IViewInfoResult (see further)

¶ Returned values

The following TypeScript types describe the format of the returned data:

// Auxiliary types.ber;

export type DomainId = nu
export type RowId = number;
export type FieldName = string;
export type EntityName = string;
export type SchemaName = string;
export type ColumnName = string;
export type AttributeName = string;
export type UserViewName = string;

// Metadata. They are not needed if you only plan to work with previously known queries without changing the data.

export interface IEntityRef {
  schema: SchemaName;
  name: EntityName;
}

export interface IFieldRef {
  entity: IEntityRef;
  name: FieldName;
}

export interface IUserViewRef {
  schema: SchemaName;
  name: UserViewName;
}

export type SimpleType = "int" | "decimal" | "string" | "bool" | "datetime" | "date" | "interval" | "regclass" | "json";

export interface IScalarSimpleType {
  type: SimpleType;
}

export interface IArraySimpleType {
  type: "array";
  subtype: SimpleType;
}

export type ValueType = IScalarSimpleType | IArraySimpleType;

export type FieldValueType = "int" | "decimal" | "string" | "bool" | "datetime" | "date" | "interval" | "json";

export type AttributeTypesMap = Record<AttributeName, ValueType>;

export interface IScalarFieldType {
  type: FieldValueType;
}

export interface IArrayFieldType {
  type: "array";
  subtype: FieldValueType;
}

export interface IReferenceFieldType {
  type: "reference";
  entity: IEntityRef;
  where?: string;
}

export interface IEnumFieldType {
  type: "enum";
  values: string[];
}

export type FieldType = IScalarFieldType | IArrayFieldType | IReferenceFieldType | IEnumFieldType;

export interface IColumnField {
  fieldType: FieldType;
  valueType: ValueType;
  defaultValue: any;
  isNullable: boolean;
  isImmutable: boolean;
  inheritedFrom?: IEntityRef;
}

export interface IMainFieldInfo {
  name: FieldName;
  field: IColumnField;
}

export interface IResultColumnInfo {
  name: string;
  attributeTypes: AttributeTypesMap;
  cellAttributeTypes: AttributeTypesMap;
  valueType: ValueType;
  punType?: ValueType;
  mainField?: IMainFieldInfo;
}

export interface IDomainField {
  ref: IFieldRef;
  field?: IColumnField;
  idColumn: ColumnName;
}

export interface IResultViewInfo {
  attributeTypes: AttributeTypesMap;
  rowAttributeTypes: AttributeTypesMap;
  domains: Record<DomainId, Record<ColumnName, IDomainField>>;
  mainEntity?: IEntityRef;
  columns: IResultColumnInfo[];
}

// Data.

export type AttributesMap = Record<AttributeName, any>;

export interface IExecutedValue {
  value: any; // Value in the cell
  attributes?: AttributesMap;
  pun?: any;
}

export interface IEntityId {
  id: RowId;
  subEntity?: IEntityRef;
}

export interface IExecutedRow {
  values: IExecutedValue[]; // Value in the row
  domainId: DomainId;
  attributes?: AttributesMap;
  entityIds?: Record<ColumnName, IEntityId>;
  mainId?: RowId;
  mainSubEntity?: IEntityRef;
}

export interface IExecutedViewExpr {
  attributes: AttributesMap;
  columnAttributes: AttributesMap[];
  rows: IExecutedRow[];
}

export interface IViewExprResult {
  info: IResultViewInfo;
  result: IExecutedViewExpr;
}

export interface IViewInfoResult {
  info: IResultViewInfo;
  pureAttributes: Record<AttributeName, any>;
  pureColumnAttributes: Record<AttributeName, any>[];
}

For example, the following query returns the result of displaying funapp.settings:

GET /views/by_name/funapp/settings/entries
Authorization: Bearer REPLACE_WITH_YOUR_OIDC_TOKEN

Result:

{
  "info":{
    "attributeTypes":{},
    "rowAttributeTypes":{},
    "domains":{
      "0":{
        "name":{
          "ref":{
            "entity":{
              "schema":"funapp",
              "name":"settings"
            },
            "name":"name"
          },
          "field":{
            "fieldType":{
              "type":"string"
            },
            "valueType":{
              "type":"string"
            },
            "isNullable":false,
            "isImmutable":false
          },
          "idColumn":"name"
        },
        "value":{
          "ref":{
            "entity":{
              "schema":"funapp",
              "name":"settings"
            },
            "name":"value"
          },
          "field":{
            "fieldType":{
              "type":"string"
            },
            "valueType":{
              "type":"string"
            },
            "isNullable":false,
            "isImmutable":false
          },
          "idColumn":"name"
        }
      }
    },
    "columns":[
      {
        "name":"name",
        "attributeTypes":{},
        "cellAttributeTypes":{},
        "valueType":{
          "type":"string"
        }
      },
      {
        "name":"value",
        "attributeTypes":{},
        "cellAttributeTypes":{},
        "valueType":{
          "type":"string"
        }
      }
    ]
  },
  "result":{
    "attributes":{},
    "columnAttributes":[
      {},
      {}
    ],
    "rows":[
      {
        "values":[
          {
            "value":"save_back_color"
          },
          {
            "value":"black"
          }
        ],
        "domainId":0,
        "entityIds":{
          "name":{
            "id":3
          }
        }
      },
      {
        "values":[
          {
            "value":"required_back_color"
          },
          {
            "value":"#F0E5FF"
          }
        ],
        "domainId":0,
        "entityIds":{
          "name":{
            "id":5
          }
        }
      },
      ...
    ]
  }
}

¶ Changing data

All operations with the database are carried out through transactions, which are executed completely and atomically.

Query: POST /transaction

The ITransaction object is passed as the body of the request. If the transaction is successful, an object of type ITransactionResult is returned.

The following TypeScript types describe the format of data sent and returned:

export interface IInsertEntityOp {
  type: "insert";
  entity: IEntityRef;
  entries: Record<FieldName, any>;
}

export interface IUpdateEntityOp {
  type: "update";
  entity: IEntityRef;
  id: number;
  entries: Record<FieldName, any>;
}

export interface IDeleteEntityOp {
  type: "delete";
  entity: IEntityRef;
  id: number;
}

export type TransactionOp = IInsertEntityOp | IUpdateEntityOp | IDeleteEntityOp;

export interface ITransaction {
  operations: TransactionOp[];
}

export interface IInsertEntityResult {
  type: "insert";
  id: number;
}

export interface IUpdateEntityResult {
  type: "update";
}

export interface IDeleteEntityResult {
  type: "delete";
}

export type TransactionOpResult = IInsertEntityResult | IUpdateEntityResult | IDeleteEntityResult;

export interface ITransactionResult {
  results: TransactionOpResult[];
}

For example, an operation to add a new record to the user.test table with the foo field set to 123:

POST /transaction
Authorization: Bearer REPLACE_WITH_YOUR_OIDC_TOKEN
Content-type: application/json

{
  "operations":[
    {
      "type":"insert",
      "entity":{
        "schema":"user",
        "name":"test"
      },
      "entries":{
        "foo":123
      }
    }
  ]
}

Query result:

{
  "results":[
    {
      "type":"insert",
      "id":120
    }
  ]
}

¶ Run action (procedure)

Request: POST /actions/ACTION_SCHEMA/ACTION_NAME/run

POST /actions/marketing/create_list_from_selected_elements/run
Authorization: Bearer YOUR_OIDC_TOKEN
Content-type: application/json
{
    "ids":[26,54,34],
  "list_name":"Clients list"
}

Response:

result contains all the data that was returned by the procedure:

{
    "result": {
        "ok": true
    }
}

or

{
    "result": {
        "ref": {
            "schema": "marketing",
            "name": "list_form"
        },
        "args": {
            "id": 7
        },
        "target": "modal"
    }
}

¶ Check if the instance exists

Request: GET /check_access

GET /check_access
Authorization: Bearer YOUR_OIDC_TOKEN
Content-type: application/json

Python example draft:

response = requests.request(
    "GET",
    "https://" + instance_name + ".api.ozma.org/check_access"
    headers={"Authorization": "Bearer REPLACE_WITH_YOUR_OIDC_TOKEN"},
    json={},
)

If the response is 404, then no such instance exists.

¶ Copy instance schemas

Request: GET /layouts

GET /layouts
Authorization: Bearer YOUR_OIDC_TOKEN
Content-type: application/zip

PUT /layouts
Authorization: Bearer YOUR_OIDC_TOKEN
Content-type: application/zip

Python example draft:

# Download scheme
response = requests.request(
    "GET",
    "https://" + instance_name + ".api.ozma.org/layouts"
    headers={
        "Authorization": "Bearer REPLACE_WITH_YOUR_OIDC_TOKEN",
        "Accept": "application/zip"
    },
    params = {"skip_preloaded":"1"},
)

# Upload cheme to new instance
response_allschemas = requests.request(
    "PUT",
    "https://" + instance_name + ".api.ozma.org/layouts"
    headers={
        "Authorization": "Bearer REPLACE_WITH_YOUR_OIDC_TOKEN",
        "Accept": "application/zip"
    },
    data=response_allschemas.content,
)
