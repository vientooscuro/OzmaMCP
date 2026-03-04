# FunDB

Source: https://wiki.ozma.io/en/docs/fundb
Exported at (UTC): 2026-03-04 15:18:29

¶ FunDB — ozma.io database

¶ General

FunDB is the database that is the "heart" of our product. It provides query execution, data persistence, permission checking, and much more. An important principle of its work is our approach to customization. All your metadata is also data - all information about schemas, tables, columns, permissions, etc. is the same tables and it is edited on general principles. When you edit them, the database is automatically updated according to your changes.

Each entity has system fields whose values assigned automatically and cannot be set or changed:

- numeric id column. It always exists. It is the master key in SQL terms;

- sub_entity column. It is available for entities that have parent or inherited entities. sub_entity stores the name of an entity subtype for a particular entry as JSON.

Warning: The internal representation of this column is different from JSON and querying its value is a slow operation. Use the OFTYPE and INHERITED FROM statements or virtual fields instead.

¶ System tables structure

System tables is stored in the public schema. They describe the current database settings.

Some tables also have the allow_broken column - when it is set, errors in setting up this entity are not a critical error and only lead to the inoperability of this entity.

Some tables also have an allow_broken column.

Setting the value to true means that errors in setting this entity are not critical and they only lead to the inoperability of this entity.

¶ schemas

Contains generated schemas.

Column
Type
Description

name
string
Schema name. Cannot be empty, contain spaces, strings / and __.

¶ entities

Contains created entities.

Column
Type
Description

schema_id
reference (public.schemas)
The schema (its identifier) containing the entity.

name
string
Entity name. Cannot be empty, contain spaces, strings / and __.

main_field
string
Each entity has a "master column" defined, which is used to briefly describe the entry, e.g. it is using when select entries from lists or for display in tables. If main_field is empty, id is used.

is_frozen
bool
All changes to this entity are prohibited.

is_abstract
bool
An entity is abstract, i.e. you cannot create new records for this entity. Used in conjunction with inheritance.

parent_id
reference (public.entities)
An entity inherits from another entity. When querying for parent entities, child records will also be in the result. Child entities have all the fields of the parent entities, as well as their own fields.

save_restore_key
string
Alternate key (from those given in unique_constraints) that is used to save and restore data from the table. The first key column must be a reference to either public.schemas or another entity with the given save_restore_key. Recursion is not supported.

¶ column_fields

Contains columns for tables.

Column
Description

entity_id
The entity (its identifier) containing the field.

name
Column name. It cannot be empty, contain spaces, strings / and __, be called id or sub_entity.

type
Data type. See datatypes.

default
Default value. It is set in the FunQL language. May be null.

is_nullable
Whether the value in the column can be null.

is_immutable
Whether the data in the column can change after creation.

¶ computed_fields

Contains calculated columns, i.e. columns that are automatically calculated from the values of other columns.

Column
Description

entity_id
The entity (its identifier) containing the field.

name
Column name. It cannot be empty, contain spaces, the strings / and __, be named id or sub_entity.

expression
Expression for the calculated column. Specified as a FunQL language expression (eg "name" || "surname").

is_virtual
Whether it is allowed to override the field expression in child entities. Used to return results based on the subtype of the entry.

is_materialized
Cache the value of a calculated field in the database. Similar to AS MATERIALIZED STORED functionality in PostgreSQL.

¶ unique_constraints

Contains unique constraints, i.e. sets of columns whose values must be unique throughout the table.

Column
Description

entity_id
The entity (its identifier) containing the constraint.

name
The name of the constraint. Cannot be empty, contain spaces, strings / and __.

columns
An array of expressions whose tuples must be unique.

is_alternate_key
Marks the constraint as an alternate key. In some queries to the database, records can be referred not only through id, but also through alternative keys. Alternate keys are also used to save and restore arbitrary entities. Columns included in an alternate key cannot be NULL.

¶ check_constraints

Contains data restrictions, i.e. checks that each row in the table must pass.

Column
Description

entity_id
The entity (its identifier) containing the constraint.

name
The name of the constraint. Cannot be empty, contain spaces, strings / and __.

expression
An expression whose result must be true or null. Specified as a FunQL language expression. Can use the => operator.

¶ indexes

Contains indexes for tables. Used to speed up heavy queries. At the moment, the indexes are fully consistent with the created indexes in PostgreSQL. It is recommended to study Postgres documentation.

Currently, only the trgm indexing operator is supported, which supports strings and gin and gist index types. It creates a trigram index using pg_trgm.

Column
Description

entity_id
The entity (its identifier) containing the index.

name
Index name. Cannot be empty, contain spaces, strings / and __.

expressions
The index is built on an array of these expressions. Collation options can be specified after the expression (as in ORDER BY and index operator class. The currently supported operator class is trgm, which allows you to create GIN indexes for full-text search.

included_expressions
An array of expressions stored within the index. Corresponds to INCLUDE in CREATE INDEX.

is_unique
Whether the index must be unique. This allows for more flexible uniqueness constraints than unique_constraints, but it is not recommended to use an index for this unless uniqueness needs to be checked against expressions.

predicate
Boolean expression for the columns on which the index is built. Corresponds to WHERE in CREATE INDEX.

type
Index type. btree, gist and gin are supported.

¶ user_views

Contains named queries that can be called.

Column
Description

schema_id
The schema (its identifier) containing the user view.

name
Query name. Cannot be empty, contain spaces, strings / and __.

query
Query in FunQL.

¶ user_view_generators

Contains named query generators. You can automatically fill the schema with named queries, for example, by creating on demand for each entity in the table. For schemas with query generators, it is not possible to create additional named queries. A generator is an ECMAScript module that exports a function by default. The signature of generators can be examined in the form of TypeScript signatures here. Requests to the database from the generator are not allowed. The generator takes data about the structure of the database as input.

Column
Description

schema_id
The schema (its identifier) containing the generator.

script
Generator code in JavaScript.

¶ fields_attributes

Contains default attributes for entity fields.

These attributes are automatically added to queries that use the specified fields. This allows users to specify, for example, a single caption for an entity column. Default attributes are set separately for the entities they are bound to. Attributes for the same entity are grouped according to priority.

Column
Description

schema_id
The schema (its identifier) containing the attributes.

field_entity_id
Attributes are set for this entity.

field_name
Attributes are set for this field in field_entity_id.

priority
The default attribute priority by which they are merged in case of conflicts. The lower number corresponds to higher priority.

attributes
Attributes list in the format @{ name1 = value1, name2 = value2 }.

¶ actions

Contains the code of actions -- server-side functions that work within a single transaction. Actions have access to the FunDB API, and they are limited to the role of the user who invoked the action.

An action is an ECMAScript module that exports a handler function by default. The signature of the action functions and the API available internally can be examined in the form of TypeScript signatures here.

The action can take arguments that are passed during the call to FunDB and can return data that will be passed back to the client.

Column
Description

schema_id
The schema (its identifier) containing the action.

function
Action code in JavaScript.

You can check out more information about actions in a separate article.

¶ triggers

Contains a list of triggers that are executed on specified operations.

A trigger is an ECMAScript module that exports a handler function by default. The signatures of the trigger functions and the API available internally can be examined as TypeScript signatures here.

Triggers that execute before an operation (before triggers) can modify the operation's arguments by returning a new args value. If no modifications are needed, return true.

If you return false,  the operation will be considered as cancelled; no further triggers will be fired, but the transaction will be executed to the end.

Column
Description

schema_id
The schema (its identifier) containing the trigger.

trigger_entity_id
The entity whose events the trigger responds to.

name
The name of the trigger. Cannot be empty, contain spaces, strings / and __.

time
Trigger execution time (BEFORE or AFTER the operation).

priority
Trigger execution priority when there are multiple triggers for the same operation.

on_insert
The trigger reacts to the insertion of new records.

on_update_fields
The trigger reacts to change of records. An array that can list field names or *. to respond to changes to any field.

on_delete
The trigger responds to the deletion of records.

procedure
Trigger code in JavaScript.

¶ roles

Contains a list of roles that restrict access to the database. Each role describes the entities and fields to which access is allowed according to the given restrictions. Roles can be inherited from other roles -- inherited permissions are cumulative.

Column
Description

schema_id
The schema (its identifier) containing the role.

name
Role name.

¶ role_parents

Contains relationships between parent roles and child roles. Roles can have multiple parents.

Column
Description

role_id
The role for which the parent (parent_role_id) is defined.

parent_role_id
Parent role.

¶ role_entities

Contains the restrictions set for the given role and entity.

- If restrictions are not defined, access to the entire entity is denied.

- If a restriction on a particular action is not set, the entire action is considered forbidden.

- For full resolution, set the limit to true.

For entities in the same inheritance hierarchy (for example, organizations and people within contacts), accesses are added as "AND" from the root of the hierarchy.

For example, if contacts are constrained to c, organizations to o, and people to p, then the general constraint

c AND (
        sub_entity OF TYPE "people" AND p
    OR sub_entity OF TYPE "organizations" AND o
)

When sampling people, the constraint will simply be

c AND p

Column
Description

role_id
The role containing the restriction.

entity_id
The entity for which the restriction is defined.

insert
Permission to insert records. Requires change permission on at least all required entity fields.

select
SELECT constraint as an expression in FunQL.

update
UPDATE constraint as an expression in FunQL. Additionally, restrictions are imposed from select for the entity and affected fields.

delete
DELETE constraint as an expression in FunQL. Additionally, restrictions are imposed from select for the entity and all its fields. Requires change permission on all entity fields.

check
Check for the admissibility of user changes. Conducted after INSERT and UPDATE queries. Required for INSERT and UPDATE.

¶ role_column_fields

Contains the restrictions that are set for the given role and entity field.

- If restrictions are not defined, access to the entire field is denied.

- If a restriction on a particular action is not set, the entire action is considered forbidden.

- For full resolution, set the limit to true.

The field restrictions are added to the entity restrictions if the field is used in the query.

Column
Description

role_entity_id
The entity constraint containing the field with column_name constraint.

column_name
The field for which the constraint is being defined.

select
SELECT constraint as an expression in FunQL.

insert
Permission to fill in this column in new records.

update
UPDATE constraint as an expression in FunQL.

check
Check for the admissibility of user changes.

¶ users

Contains a list of users who are allowed to access the database.

Column
Description

name
User ID (the email the account was created).

is_enabled
Whether the user is activated.

is_root
Whether the user is a database administrator (full access, including service operations).

role_id
The role that the user belongs to. May be absent (perhaps when the user is an administrator).

¶ events

Contains the event log in the database.

Column
Description

transaction_time
Transaction time.

transaction_id
Unique transaction identifier within the database. Together with "transaction_time" uniquely identifies a transaction in the database.

timestamp
Operation time. Unique within a single transaction.

source
Event source. JSON, where the "source" field is set to "api" (for operations performed by the user) or "trigger" (for operations performed by triggers).

user_name
The user who started the transaction.

type
Event type.

error
The type of error that occurred if the operation failed.

schema_name
The name of the schema for which the event occurred.

entity_name
The name of the entity for which the event occurred.

entity_id
The ID of the record for which the event occurred.

details
Event details in any format.

¶ API

Your database has a public API through which you can interact directly with your data. The base can be used for your own solutions: it does not contain a binding to FunApp (our constructor product), on the contrary - FunApp is built on top of the base, and we use the same public calls.

The API is currently not in a stable version.

Details: FunDB API
